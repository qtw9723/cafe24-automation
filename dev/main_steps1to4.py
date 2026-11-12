"""
Cafe24 백오피스 일일 자동화 메인 실행 파일
Step 1-4만 실행 (Step 5 제외)

실행 방법:
    python main_steps1to4.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 프로젝트 루트(config·utils·steps) import용
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import config
from utils.logger import logger
from utils.email_notifier import email_notifier
from steps import step1_shop_logs, step2_log_stats, step3_dashboard, step4_daily_check


def setup_driver():
    """Selenium WebDriver 설정"""
    chrome_options = Options()

    if config.CHROME_HEADLESS:
        chrome_options.add_argument("--headless")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(config.IMPLICIT_WAIT)

    return driver


def run_automation():
    """자동화 프로세스 실행 (Step 1-4)"""
    driver = None
    results = {
        'selected_shops': 0,
        'today_log_sum': 0,
        'today_logs_dashboard': 0,
        'month_errors': 0,
        'error_comparison': '미확인',
        'memo_saved': False,
        'all_steps_success': False
    }

    try:
        logger.clear_logs()
        logger.log_step(0, "Cafe24 백오피스 일일 자동화 시작 (Step 1-4만)")

        driver = setup_driver()
        logger.log("INIT", "DRIVER", "Selenium WebDriver 초기화 완료")

        # ===== STEP 1 =====
        logger.log("MAIN", "STEP1", "=" * 50)
        step1_result = step1_shop_logs.execute(driver)
        if not step1_result['success']:
            logger.log_error("MAIN", "STEP1", step1_result.get('error'))
            return results
        results['selected_shops'] = step1_result.get('shop_count', 0)

        # ===== STEP 2 =====
        logger.log("MAIN", "STEP2", "=" * 50)
        step2_result = step2_log_stats.execute(driver)
        if not step2_result['success']:
            logger.log_error("MAIN", "STEP2", step2_result.get('error'))
            return results
        results['today_log_sum'] = step2_result.get('today_log_sum', 0)

        # ===== STEP 3 =====
        logger.log("MAIN", "STEP3", "=" * 50)
        step3_result = step3_dashboard.execute(driver)
        if not step3_result['success']:
            logger.log_error("MAIN", "STEP3", step3_result.get('error'))
            return results
        results['today_logs_dashboard'] = step3_result.get('today_logs', 0)
        results['month_errors'] = step3_result.get('month_errors', 0)

        # ===== STEP 4 =====
        logger.log("MAIN", "STEP4", "=" * 50)
        step4_result = step4_daily_check.execute(
            driver,
            results['month_errors'],
            results['today_logs_dashboard'],
            results['month_errors']
        )
        if not step4_result['success']:
            logger.log_error("MAIN", "STEP4", step4_result.get('error'))
            return results
        results['memo_saved'] = step4_result.get('memo_saved', False)

        results['all_steps_success'] = True
        logger.log_step(0, "Cafe24 백오피스 일일 자동화 (Step 1-4) 완료")

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
        '✅ 이번달 에러 건수': f"{results['month_errors']}건",
        '✅ 에러 비교 결과': results['error_comparison'],
        '✅ 메모 저장 여부': '성공' if results['memo_saved'] else '실패',
    }
    return formatted


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("  Cafe24 백오피스 일일 자동화 프로그램")
    print("  (Step 1-4만 실행)")
    print("=" * 60 + "\n")

    results = run_automation()

    print("\n" + "=" * 60)
    print("  최종 결과 리포트")
    print("=" * 60 + "\n")

    formatted_results = format_results(results)
    for key, value in formatted_results.items():
        print(f"{key}: {value}")

    logger.save_results(formatted_results)

    print("\n" + "=" * 60)
    if results['all_steps_success']:
        print("  ✅ Step 1-4가 성공적으로 완료되었습니다")
    else:
        print("  ⚠️ 일부 단계에서 실패했습니다")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
