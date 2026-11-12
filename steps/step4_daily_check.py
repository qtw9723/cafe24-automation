"""
4단계: daily check 탭 - 에러 비교 및 메모 저장
- daily check 탭 이동
- 어제 날짜 항목 클릭 → 메모에서 에러 건수 추출
- 에러 비교 (오늘 vs 어제) - 로컬 처리
- 비교 결과에 따라 진행 여부 결정
- 오늘 날짜 항목 클릭
- 메모 작성 - 로컬 처리
- 메모 입력 및 저장
"""
from selenium.webdriver.common.by import By
from utils.logger import logger
from utils.wait import safe_click, wait_for_element, safe_fill_text, sleep
from utils.parser import extract_first_number, get_today_date_string, get_yesterday_date_string, get_current_month, format_memo
import config


def click_daily_check_tab(driver):
    """daily check 탭 클릭 (JavaScript 사용)"""
    logger.log_step(4, "daily check 탭 클릭")

    try:
        # JavaScript로 탭 찾기
        js_code = """
        return (function() {
            const tabs = document.querySelectorAll('a');
            for (let tab of tabs) {
                const text = tab.textContent.toLowerCase();
                if (text.includes('daily') && text.includes('check')) {
                    tab.scrollIntoView(true);
                    tab.click();
                    return {success: true};
                }
            }
            return {success: false, reason: 'daily check 탭을 찾을 수 없음'};
        })();
        """

        result = driver.execute_script(js_code)

        if result and result.get('success'):
            sleep(2)
            logger.log_success(4, "CLICK_TAB", "daily check 탭 클릭 완료")
            return True
        else:
            logger.log_error("STEP4", "CLICK_TAB", result.get('reason', 'daily check 탭을 찾을 수 없음'))
            return False

    except Exception as e:
        logger.log_error("STEP4", "CLICK_TAB", e)
        return False


def click_yesterday_item(driver):
    """어제 날짜 항목 클릭"""
    logger.log_step(4, "어제 날짜 항목 클릭")

    try:
        yesterday_date = get_yesterday_date_string()
        logger.log("STEP4", "CLICK_YESTERDAY", f"어제 날짜: {yesterday_date}")

        # 어제 날짜를 한글로 변환 (예: 2026-05-11 -> 2026년 5월 11일)
        year, month, day = yesterday_date.split('-')
        korean_date = f"{year}년 {int(month)}월 {int(day)}일"
        logger.log("STEP4", "CLICK_YESTERDAY", f"한글 형식: {korean_date}")

        # 어제 날짜로 항목 찾기
        item_selectors = [
            (By.XPATH, f"//span[contains(text(), '{korean_date}')]"),
            (By.XPATH, f"//td[contains(text(), '{korean_date}')]"),
            (By.XPATH, f"//tr[contains(., '{korean_date}')]"),
            (By.XPATH, f"//button[contains(text(), '{yesterday_date}')]"),
        ]

        for selector in item_selectors:
            try:
                element = driver.find_element(*selector)
                # 클릭 가능한 부모 요소 찾기
                clickable = element
                for _ in range(5):  # 최대 5개 부모 레벨까지 확인
                    try:
                        clickable.click()
                        sleep(1)
                        logger.log_success(4, "CLICK_YESTERDAY", "어제 항목 클릭 완료")
                        return True
                    except:
                        clickable = clickable.find_element(By.XPATH, "..")
                        continue
            except:
                continue

        logger.log_error("STEP4", "CLICK_YESTERDAY", f"어제({korean_date}) 항목을 찾을 수 없음")
        return False

    except Exception as e:
        logger.log_error("STEP4", "CLICK_YESTERDAY", e)
        return False


def extract_yesterday_error_count(driver):
    """어제 메모에서 에러 건수 추출"""
    logger.log_step(4, "어제 메모에서 에러 건수 추출")

    try:
        # 메모 필드 또는 메모 내용 찾기
        memo_selectors = [
            (By.XPATH, "//textarea[@class='memo']"),
            (By.XPATH, "//textarea[contains(@class, 'memo')]"),
            (By.XPATH, "//*[@class='memo-content']"),
            (By.XPATH, "//*[contains(@class, 'memo')]"),
        ]

        memo_text = ""
        for selector in memo_selectors:
            try:
                elem = driver.find_element(*selector)
                memo_text = elem.text or elem.get_attribute('value')
                if memo_text:
                    break
            except:
                continue

        if not memo_text:
            # 페이지 텍스트에서 메모 찾기
            body = driver.find_element(By.TAG_NAME, "body")
            page_text = body.text
            lines = page_text.split('\n')

            for line in lines:
                if '에러' in line:
                    memo_text += line + '\n'

        logger.log("STEP4", "EXTRACT_ERROR", f"추출된 메모: {memo_text}")

        # 메모에서 에러 수 추출
        # 메모 형식: "오늘 로그: 47건 / 11월 에러: 0건" → 첫 숫자(로그 수)가 아니라 '에러:' 뒤 숫자를 읽는다
        import re
        m = re.search(r'에러\s*[:：]\s*(\d+)', memo_text or '')
        error_count = int(m.group(1)) if m else extract_first_number(memo_text)
        logger.log_success(4, "EXTRACT_ERROR", f"어제 에러: {error_count}건")
        return error_count

    except Exception as e:
        logger.log_error("STEP4", "EXTRACT_ERROR", e)
        return 0


def compare_and_decide(today_errors, yesterday_errors):
    """로컬 코드로 에러 비교 및 진행 여부 결정"""
    logger.log_step(4, "에러 비교 (로컬 처리)")

    try:
        # 에러 비교
        if today_errors == yesterday_errors:
            status = "동일"
            proceed = True
        elif today_errors < yesterday_errors:
            status = "감소"
            proceed = True
        else:  # today_errors > yesterday_errors
            status = "증가"
            proceed = False

        logger.log("STEP4", "COMPARE", f"비교 결과: {status}")
        logger.log("STEP4", "COMPARE", f"진행 여부: {'진행' if proceed else '중단'}")

        return {
            'status': status,
            'proceed': proceed,
            'today': today_errors,
            'yesterday': yesterday_errors
        }

    except Exception as e:
        logger.log_error("STEP4", "COMPARE", e)
        # 기본값: 동일로 간주하고 진행
        return {
            'status': '동일',
            'proceed': True,
            'today': today_errors,
            'yesterday': yesterday_errors
        }


def click_today_item(driver):
    """오늘 날짜 항목 클릭 또는 새로 생성"""
    logger.log_step(4, "오늘 날짜 항목 클릭 또는 생성")

    try:
        today_date = get_today_date_string()
        logger.log("STEP4", "CLICK_TODAY", f"오늘 날짜: {today_date}")

        # 오늘 날짜를 한글로 변환 (예: 2026-05-12 -> 2026년 5월 12일)
        year, month, day = today_date.split('-')
        korean_date = f"{year}년 {int(month)}월 {int(day)}일"
        logger.log("STEP4", "CLICK_TODAY", f"한글 형식: {korean_date}")

        item_selectors = [
            (By.XPATH, f"//span[contains(text(), '{korean_date}')]"),
            (By.XPATH, f"//td[contains(text(), '{korean_date}')]"),
            (By.XPATH, f"//tr[contains(., '{korean_date}')]"),
            (By.XPATH, f"//button[contains(text(), '{today_date}')]"),
        ]

        for selector in item_selectors:
            try:
                element = driver.find_element(*selector)
                # 클릭 가능한 부모 요소 찾기
                clickable = element
                for _ in range(5):  # 최대 5개 부모 레벨까지 확인
                    try:
                        clickable.click()
                        sleep(1)
                        logger.log_success(4, "CLICK_TODAY", "오늘 항목 클릭 완료")
                        return True
                    except:
                        clickable = clickable.find_element(By.XPATH, "..")
                        continue
            except:
                continue

        # 오늘 항목이 없으면 새 항목(Create) 생성
        logger.log("STEP4", "CLICK_TODAY", "오늘 항목이 없음. 새 항목 생성 시도")

        try:
            # 1) Create 버튼을 '텍스트'로 탐색해 클릭 (이 백오피스는 MUI SPA라
            #    a[href*='create'] 같은 정적 링크가 없음 → 버튼 텍스트로 찾는다)
            js_find_create = """
            return (function() {
                const els = document.querySelectorAll('button, a');
                for (let el of els) {
                    const t = (el.textContent || '').trim().toUpperCase();
                    if (t === 'CREATE' || t === 'NEW' || t === 'ADD' ||
                        t.includes('생성') || t.includes('추가') || t.includes('등록')) {
                        el.scrollIntoView(true);
                        el.click();
                        return {clicked: true, label: t};
                    }
                }
                return {clicked: false};
            })();
            """
            res = driver.execute_script(js_find_create)
            if res and res.get('clicked'):
                sleep(2)
                logger.log_success(4, "CLICK_TODAY", f"Create 버튼 클릭 완료 ('{res.get('label')}')")
                return True

            # 2) 버튼을 못 찾으면 해시 라우팅으로 직접 이동 (검증된 폴백)
            logger.log("STEP4", "CLICK_TODAY", "Create 버튼 미발견 → 해시 라우팅으로 이동")
            driver.execute_script("window.location.hash = '#/dailyChecks/create';")
            sleep(2)
            logger.log_success(4, "CLICK_TODAY", "Create 페이지로 이동 완료")
            return True

        except Exception as e:
            logger.log_error("STEP4", "CLICK_TODAY", f"Create 페이지 이동 실패: {e}")
            return False

    except Exception as e:
        logger.log_error("STEP4", "CLICK_TODAY", e)
        return False


def generate_and_fill_memo(driver, dashboard_logs, month_errors, log_stats_sum=None, log_verification=None):
    """메모 생성 및 입력 (저장 안 함)"""
    logger.log_step(4, "메모 생성 및 입력 (로컬 처리)")

    try:
        # 로컬 코드로 메모 생성
        month = get_current_month()

        # 기본 메모 생성
        memo_text = format_memo(dashboard_logs, month, month_errors)

        # 로그 검증 결과 추가
        if log_stats_sum is not None and log_verification:
            memo_text += f"\n[로그 검증] Stats: {log_stats_sum}건 | Dashboard: {dashboard_logs}건 | {log_verification}"

        logger.log("STEP4", "GENERATE_MEMO", f"생성된 메모: {memo_text}")

        # 메모 필드 찾기
        memo_field_selectors = [
            (By.XPATH, "//textarea[@class='memo']"),
            (By.XPATH, "//textarea[contains(@class, 'memo')]"),
            (By.XPATH, "//textarea"),
        ]

        memo_filled = False
        for selector in memo_field_selectors:
            try:
                safe_fill_text(driver, selector, memo_text)
                logger.log_success(4, "FILL_MEMO", "메모 입력 완료")
                memo_filled = True
                break
            except:
                continue

        if not memo_filled:
            logger.log_error("STEP4", "FILL_MEMO", "메모 필드를 찾을 수 없음")
            return False

        return True

    except Exception as e:
        logger.log_error("STEP4", "FILL_MEMO", e)
        return False


def execute(driver, today_errors, dashboard_logs, month_errors, log_stats_sum=None, log_verification=None):
    """Step 4 실행"""
    try:
        # daily check 탭으로 이동
        if not click_daily_check_tab(driver):
            return {
                'success': False,
                'error': "daily check 탭으로 이동 실패",
                'proceed': False
            }

        # 어제 항목 클릭 및 에러 수 추출
        if not click_yesterday_item(driver):
            logger.log("STEP4", "INFO", "어제 항목을 찾을 수 없어 에러 비교를 스킵합니다")
            yesterday_errors = today_errors
        else:
            yesterday_errors = extract_yesterday_error_count(driver)

        # 에러 비교
        comparison = compare_and_decide(today_errors, yesterday_errors)

        # 진행 여부 결정
        if not comparison['proceed']:
            logger.log("STEP4", "DECISION", "에러가 증가했으므로 작업을 중단합니다")
            return {
                'success': True,
                'proceed': False,
                'comparison': comparison,
                'memo_saved': False
            }

        # 오늘 항목 클릭
        if not click_today_item(driver):
            return {
                'success': False,
                'error': "오늘 항목으로 이동 실패",
                'proceed': False
            }

        # 메모 생성 및 입력 (저장은 아직 안 함)
        memo_filled = generate_and_fill_memo(driver, dashboard_logs, month_errors, log_stats_sum, log_verification)

        # ===== STEP 5: 체크리스트 체크 (같은 페이지에서) =====
        logger.log_step(5, "체크리스트 항목 체크")

        # Step 5 체크박스 체크
        checklist_items = [
            "log_check_yn",
            "error_monitoring_yn",
            "api_error_monitoring_yn",
            "chatbot_test_yn",
            "new_domain_check_yn",
            "new_chatbot_test_yn",
            "cancel_domain_check_yn",
            "cancel_chatbot_check_yn",
        ]

        checked_count = 0
        for item in checklist_items:
            if check_and_verify_checkbox(driver, item):
                checked_count += 1

        logger.log("STEP5", "CHECK_ALL", f"체크된 항목: {checked_count}/{len(checklist_items)}")

        # 메모 + 체크박스 모두 완료 후 한 번에 저장
        all_saved = save_checklist(driver)

        return {
            'success': True,
            'proceed': True,
            'comparison': comparison,
            'memo_saved': memo_filled and all_saved,
            'checklist_completed': all_saved,
            'checked_count': checked_count,
            'memo_text': f"오늘 로그: {dashboard_logs}건 / {get_current_month()}월 에러: {month_errors}건"
        }

    except Exception as e:
        logger.log_error("STEP4", "EXECUTE", e)
        return {
            'success': False,
            'error': str(e),
            'proceed': False
        }


def check_and_verify_checkbox(driver, input_name):
    """특정 항목의 체크박스 체크 - MUI Switch 직접 제어"""
    logger.log_step(5, f"'{input_name}' 체크박스 체크")

    try:
        # 1단계: checkbox 찾기 및 상태 확인
        js_code = f"""
        return (function() {{
            const checkbox = document.querySelector('input[name="{input_name}"]');
            if (!checkbox) {{
                return {{'found': false}};
            }}
            return {{'found': true, 'checked': checkbox.checked}};
        }})();
        """

        result = driver.execute_script(js_code)

        if not result.get('found'):
            logger.log_error("STEP5", "CHECK_ITEM", f"'{input_name}' 체크박스를 찾을 수 없음")
            return False

        # 이미 체크되어 있으면 반환
        if result.get('checked'):
            logger.log("STEP5", "CHECK_ITEM", f"'{input_name}' 이미 체크됨")
            return True

        # 2단계: MUI Switch의 span 요소를 찾아서 클릭
        js_code = f"""
        return (function() {{
            const checkbox = document.querySelector('input[name="{input_name}"]');

            // MUI Switch의 부모 찾기 (여러 클래스 시도)
            let switchElement = checkbox.closest('.MuiSwitch-root');

            if (!switchElement) {{
                switchElement = checkbox.closest('.MuiFormControlLabel-root');
            }}

            if (!switchElement) {{
                // 부모가 없으면 input 자체를 클릭
                switchElement = checkbox;
            }}

            // span이나 다른 클릭 가능한 요소 찾기
            let clickTarget = switchElement.querySelector('.MuiSwitch-switchBase');
            if (!clickTarget) {{
                clickTarget = switchElement.querySelector('span[role="checkbox"]');
            }}
            if (!clickTarget) {{
                clickTarget = switchElement.querySelector('label');
            }}
            if (!clickTarget) {{
                clickTarget = switchElement;
            }}

            // 클릭 실행
            if (clickTarget) {{
                clickTarget.click();
                return {{'clicked': true}};
            }}
            return {{'clicked': false}};
        }})();
        """

        click_result = driver.execute_script(js_code)
        sleep(1)  # MUI 업데이트 대기

        # 3단계: 상태 재확인
        js_code = f"""
        return (function() {{
            const checkbox = document.querySelector('input[name="{input_name}"]');
            return {{'checked': checkbox.checked}};
        }})();
        """

        verify_result = driver.execute_script(js_code)

        if verify_result.get('checked'):
            logger.log_success(5, "CHECK_ITEM", f"'{input_name}' 체크 완료")
            sleep(0.3)
            return True
        else:
            logger.log_error("STEP5", "CHECK_ITEM", f"'{input_name}' 체크 실패 (클릭됨: {click_result.get('clicked')}, 최종상태: {verify_result.get('checked')})")
            return False

    except Exception as e:
        logger.log_error("STEP5", "CHECK_ITEM", f"{input_name} 체크 실패: {e}")
        return False


def save_checklist(driver):
    """체크리스트 저장"""
    logger.log_step(5, "체크리스트 저장")

    try:
        js_code = """
        return (function() {
            // SAVE 버튼 찾기
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                const text = btn.textContent.trim().toUpperCase();
                if (text.includes('SAVE') || text.includes('저장')) {
                    btn.scrollIntoView(true);
                    btn.click();
                    return {success: true};
                }
            }

            // 또는 type='submit' 버튼
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.scrollIntoView(true);
                submitBtn.click();
                return {success: true};
            }

            return {success: false};
        })();
        """

        result = driver.execute_script(js_code)

        if result.get('success'):
            sleep(config.WAIT_AFTER_SAVE)
            logger.log_success(5, "SAVE", "체크리스트 저장 완료")
            return True
        else:
            logger.log_error("STEP5", "SAVE", "저장 버튼을 찾을 수 없음")
            return False

    except Exception as e:
        logger.log_error("STEP5", "SAVE", e)
        return False


# config import 추가
import config
