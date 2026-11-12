"""
Cafe24 백오피스 일일 자동화 메인 실행 파일

실행 방법:
    python main.py
"""
import os
import sys
import socket
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import config
from utils.logger import logger
from utils.email_notifier import email_notifier
from steps import step1_shop_logs, step2_log_stats, step3_dashboard, step4_daily_check, step5_checklist


# 해지 감지 프로브(cafe24_backoffice/tools/cancel_probe)가 남긴 요약 파일.
# run_daily.sh 가 main.py 보다 먼저 프로브를 돌려 이 파일을 만든다.
CANCEL_PROBE_SUMMARY_FILE = os.path.join(config.OUTPUT_DIR, "cancel_probe_summary.txt")


def read_cancel_probe_summary():
    """성공 알림 메일에 덧붙일 해지 감지 요약.

    오늘 결과가 아니면(프로브 실패·미실행) 그 사실을 적는다 —
    조용히 빠지면 프로브가 멈춘 것을 알아챌 수 없기 때문이다.
    """
    import datetime

    header = "[도메인 해지 감지]"
    today = datetime.date.today().isoformat()
    try:
        with open(CANCEL_PROBE_SUMMARY_FILE, encoding="utf-8") as fp:
            text = fp.read().strip()
    except FileNotFoundError:
        return header + "\n  · 결과 파일 없음 (프로브 미실행 의심)"
    except Exception as err:
        return header + f"\n  · 요약을 읽지 못함: {err}"

    if not text.startswith("관측일: " + today):
        first_line = text.split("\n")[0] if text else "(빈 파일)"
        return header + f"\n  · 오늘 결과가 아님 ({first_line}) — 프로브 실패 의심"

    return header + "\n" + text


def check_server_reachable(url, timeout=3, retries=2, retry_delay=5):
    """백오피스 서버에 TCP로 빠르게 접속 가능한지 확인.

    Selenium을 띄우기 전에 호출해, 서버 다운/네트워크 단절 시
    120초씩 hang 하지 않고 즉시 판단하기 위함.
    반환: (reachable: bool, detail: str)
    """
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True, ""
        except OSError as e:
            last_error = f"{type(e).__name__}: {e}"
            if attempt < retries:
                import time
                time.sleep(retry_delay)

    return False, f"{host}:{port} 접속 실패 ({last_error})"


def setup_driver():
    """Selenium WebDriver 설정"""
    chrome_options = Options()

    if config.CHROME_HEADLESS:
        chrome_options.add_argument("--headless")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size=1920,1080")

    # WebDriver Manager로 자동 다운로드
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.implicitly_wait(config.IMPLICIT_WAIT)

    return driver


def run_automation():
    """자동화 프로세스 실행"""
    driver = None
    results = {
        'selected_shops': 0,
        'today_log_sum': 0,
        'today_logs_dashboard': 0,
        'month_errors': 0,
        'error_comparison': '미확인',
        'memo_saved': False,
        'checklist_completed': False,
        'all_steps_success': False
    }

    try:
        logger.clear_logs()
        logger.log_step(0, "Cafe24 백오피스 일일 자동화 시작")

        # 드라이버 설정
        driver = setup_driver()
        logger.log("INIT", "DRIVER", "Selenium WebDriver 초기화 완료")

        # ===== STEP 1: Shop 탭 - 로그 수집 =====
        logger.log("MAIN", "STEP1", "=" * 50)
        step1_result = step1_shop_logs.execute(driver)

        if not step1_result['success']:
            logger.log_error("MAIN", "STEP1", step1_result.get('error'))
            return results

        results['selected_shops'] = step1_result.get('shop_count', 0)

        # ===== STEP 2: log stats 탭 - 로그 합계 확인 =====
        logger.log("MAIN", "STEP2", "=" * 50)
        step2_result = step2_log_stats.execute(driver)

        if not step2_result['success']:
            logger.log_error("MAIN", "STEP2", step2_result.get('error'))
            return results

        results['today_log_sum'] = step2_result.get('today_log_sum', 0)
        # 이번달 에러 건수는 step2의 log stats 테이블 합계(column-thisMonthErr)를 신뢰값으로 사용한다.
        # (step3 Dashboard 텍스트 스크랩은 요소를 못 찾아 0을 반환하는 일이 잦아 캐노니컬 소스로 부적합)
        results['month_errors'] = step2_result.get('month_error_sum', 0)

        # ===== STEP 3: Dashboard 탭 - 수치 검증 =====
        logger.log("MAIN", "STEP3", "=" * 50)
        step3_result = step3_dashboard.execute(driver)

        if not step3_result['success']:
            logger.log_error("MAIN", "STEP3", step3_result.get('error'))
            return results

        today_logs = step3_result.get('today_logs', 0)
        # month_errors는 위에서 step2 값으로 확정. step3는 오늘 로그(today_logs) 검증용으로만 사용.
        month_errors = results['month_errors']

        results['today_logs_dashboard'] = today_logs

        # ===== 로그 수치 검증: Step 2 vs Step 3 비교 =====
        log_stats_sum = results['today_log_sum']
        dashboard_today = results['today_logs_dashboard']

        logger.log("MAIN", "VERIFICATION", "=" * 50)
        logger.log("MAIN", "VERIFICATION", f"Log Stats 합계: {log_stats_sum}건")
        logger.log("MAIN", "VERIFICATION", f"Dashboard 오늘 로그: {dashboard_today}건")

        if log_stats_sum == dashboard_today:
            logger.log_success(3, "VERIFICATION", f"✅ 로그 수치 일치: {log_stats_sum}건")
            results['log_verification'] = f"일치 ({log_stats_sum}건)"
        else:
            logger.log_error("STEP3", "VERIFICATION", f"⚠️  로그 수치 불일치!")
            logger.log_error("STEP3", "VERIFICATION", f"   Log Stats: {log_stats_sum}건")
            logger.log_error("STEP3", "VERIFICATION", f"   Dashboard: {dashboard_today}건")
            logger.log_error("STEP3", "VERIFICATION", f"   차이: {abs(log_stats_sum - dashboard_today)}건")
            results['log_verification'] = f"불일치 (Stats: {log_stats_sum}건 vs Dashboard: {dashboard_today}건)"

        # ===== STEP 4: daily check 탭 - 에러 비교 및 메모 저장 =====
        logger.log("MAIN", "STEP4", "=" * 50)
        step4_result = step4_daily_check.execute(
            driver,
            month_errors,  # 오늘 에러 수
            today_logs,    # 대시보드 로그 수
            month_errors,  # 현재월 에러 수
            log_stats_sum,  # Log Stats의 로그 합계
            results.get('log_verification', '')  # 로그 검증 결과
        )

        if not step4_result['success']:
            logger.log_error("MAIN", "STEP4", step4_result.get('error'))
            return results

        # Step 4 결과 저장
        if 'comparison' in step4_result:
            comparison = step4_result['comparison']
            results['error_comparison'] = comparison.get('status', '미확인')

            # 에러가 증가한 경우 이메일 알림 발송
            if comparison.get('status') == '증가':
                logger.log("MAIN", "ALERT", "에러가 증가했습니다. 이메일 알림을 발송합니다.")
                email_notifier.send_error_increase_notification(
                    comparison.get('today', 0),
                    comparison.get('yesterday', 0)
                )

        results['memo_saved'] = step4_result.get('memo_saved', False)
        results['checklist_completed'] = step4_result.get('checklist_completed', False)

        # 에러가 증가한 경우 여기서 종료
        if not step4_result.get('proceed', True):
            logger.log("MAIN", "DECISION", "에러가 증가했으므로 이후 단계를 실행하지 않습니다")
            results['error_comparison'] = '증가 - 중단'
            logger.save_results(results)
            return results

        # 모든 단계 완료
        results['all_steps_success'] = True
        logger.log_step(0, "Cafe24 백오피스 일일 자동화 완료")

        # 성공 알림 이메일 발송
        summary = format_results(results)
        summary_text = "\n".join([f"{k}: {v}" for k, v in summary.items()])
        probe_text = read_cancel_probe_summary()
        summary_text += "\n\n" + probe_text
        email_notifier.send_success_notification(summary_text, summary=summary, probe_text=probe_text)

    except Exception as e:
        logger.log_error("MAIN", "EXECUTION", e)
        import traceback
        logger.log_error("MAIN", "TRACEBACK", traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            logger.log("CLEANUP", "DRIVER", "WebDriver 종료")

    return results


def format_results(results):
    """결과를 정렬된 형식으로 반환"""
    formatted = {
        '✅ 선택된 쇼핑몰 개수': f"{results['selected_shops']}개",
        '✅ Log Stats 오늘 로그 합계': f"{results['today_log_sum']}건",
        '✅ Dashboard 오늘 로그 수': f"{results['today_logs_dashboard']}건",
        '🔍 로그 수치 검증': results.get('log_verification', '미확인'),
        '✅ 이번달 에러 건수': f"{results['month_errors']}건",
        '✅ 에러 비교 결과': results['error_comparison'],
        '✅ 메모 저장 여부': '성공' if results['memo_saved'] else '실패',
        '✅ Daily Check 완료 여부': '성공' if results['checklist_completed'] else '실패',
    }
    return formatted


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("  Cafe24 백오피스 일일 자동화 프로그램")
    print("=" * 60)
    print("  (외부 API 없음 - 완전 로컬 처리)")
    print("=" * 60 + "\n")

    # ===== 사전 연결 점검 =====
    # Selenium을 띄우기 전에 백오피스 서버 도달 여부를 빠르게 확인한다.
    # 서버가 죽었거나 사내망이 끊긴 경우 driver.get()이 120초씩 hang 하므로,
    # 여기서 즉시 '서버 다운' 전용 메일을 보내고 전용 종료코드(2)로 끝낸다.
    # → run_daily.sh는 종료코드 2면 일반 실패 메일을 중복 발송하지 않는다.
    reachable, detail = check_server_reachable(config.CAFE24_URL)
    if not reachable:
        logger.clear_logs()
        logger.log_error("MAIN", "PREFLIGHT", f"백오피스 서버 응답 없음 - {detail}")
        email_notifier.send_server_down_notification(config.CAFE24_URL, detail)
        print(f"\n🔌 백오피스 서버에 접속할 수 없습니다: {detail}")
        print("   서버 다운/네트워크 단절로 판단하여 자동화를 시작하지 않습니다.\n")
        sys.exit(2)

    # 자동화 실행 (일시적 브라우저/세션 오류 시 새 브라우저로 전체 재시도)
    max_attempts = getattr(config, "MAX_RUN_ATTEMPTS", 2)
    results = None
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            logger.log("MAIN", "RETRY", f"일시적 실패로 새 브라우저로 재시도합니다 ({attempt}/{max_attempts})")
        results = run_automation()
        # 정상 완료, 또는 '에러 증가'로 인한 의도된 중단이면 재시도하지 않음
        if results.get('all_steps_success') or results.get('error_comparison') == '증가 - 중단':
            break

    # 결과 출력
    print("\n" + "=" * 60)
    print("  최종 결과 리포트")
    print("=" * 60 + "\n")

    formatted_results = format_results(results)
    for key, value in formatted_results.items():
        print(f"{key}: {value}")

    # 결과 파일 저장
    logger.save_results(formatted_results)

    print("\n" + "=" * 60)
    if results['all_steps_success']:
        print("  ✅ 모든 단계가 성공적으로 완료되었습니다")
    else:
        print("  ⚠️ 일부 단계에서 실패했습니다")
    print("=" * 60 + "\n")

    # 종료 코드: 정상 완료 시 0, 기술적 실패 시 1
    # → run_daily.sh가 exit 1을 보고 ❌ 실패 메일을 발송한다(거짓 성공 방지).
    # 주의: '에러 증가 - 중단'은 all_steps_success=False라 여기서 1로 종료되며,
    #       이때 별도의 에러증가 알림 메일도 이미 발송된 상태다.
    sys.exit(0 if results.get('all_steps_success') else 1)


if __name__ == "__main__":
    main()
