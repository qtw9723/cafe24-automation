"""
5단계: daily check - 8개 항목 완료 처리
- 오늘 날짜 항목 확인
- 다음 8개 항목의 체크박스를 모두 ON으로 체크:
  1. 로그 수집 확인 (log_check_yn)
  2. 에러 모니터링 확인 (error_check_yn)
  3. API 에러 모니터링 확인 (api_error_check_yn)
  4. 챗봇 동작 확인 (chatbot_check_yn)
  5. 신규 도메인 처리 확인 (new_domain_check_yn)
  6. 신규 챗봇 동작 검증 확인 (new_chatbot_check_yn)
  7. 해지 도메인 처리 확인 (cancel_domain_check_yn)
  8. 해지 챗봇 처리 확인 (cancel_chatbot_check_yn)
- SAVE 또는 저장 버튼 클릭
"""
from selenium.webdriver.common.by import By
import config
from utils.logger import logger
from utils.wait import safe_click, sleep


# 체크해야 할 항목들 (name 속성)
CHECKLIST_ITEMS = [
    "log_check_yn",
    "error_monitoring_yn",
    "api_error_monitoring_yn",
    "chatbot_test_yn",
    "new_domain_check_yn",
    "new_chatbot_test_yn",
    "cancel_domain_check_yn",
    "cancel_chatbot_check_yn",
]


def check_checkbox(driver, input_name):
    """특정 항목의 체크박스 체크 - name 속성 기반"""
    logger.log_step(5, f"'{input_name}' 체크박스 체크")

    try:
        # 1단계: checkbox 찾기 및 상태 확인
        js_code = f"""
        return (function() {{
            const checkbox = document.querySelector('input[name="{input_name}"]');
            if (!checkbox) {{
                return {{'found': false}};
            }}
            return {{'found': true, 'already_checked': checkbox.checked}};
        }})();
        """

        result = driver.execute_script(js_code)

        if not result.get('found'):
            logger.log_error("STEP5", "CHECK_ITEM", f"'{input_name}' 체크박스를 찾을 수 없음")
            return False

        # 이미 체크되어 있으면 반환
        if result.get('already_checked'):
            logger.log("STEP5", "CHECK_ITEM", f"'{input_name}' 이미 체크됨")
            return True

        # 2단계: label 클릭 (MUI Switch)
        js_code = f"""
        return (function() {{
            const checkbox = document.querySelector('input[name="{input_name}"]');
            const checkboxId = checkbox.id;
            const label = document.querySelector('label[for="' + checkboxId + '"]');

            if (label) {{
                label.click();
                return {{'clicked': true}};
            }}
            return {{'clicked': false}};
        }})();
        """

        click_result = driver.execute_script(js_code)
        sleep(0.5)

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
            logger.log_error("STEP5", "CHECK_ITEM", f"'{input_name}' 체크 실패: label 클릭 후에도 체크되지 않음")
            return False

    except Exception as e:
        logger.log_error("STEP5", "CHECK_ITEM", f"{input_name} 체크 실패: {e}")
        return False


def check_all_items(driver):
    """모든 체크리스트 항목 체크"""
    logger.log_step(5, "모든 체크리스트 항목 체크")

    checked_count = 0
    for item in CHECKLIST_ITEMS:
        if check_checkbox(driver, item):
            checked_count += 1

    logger.log("STEP5", "CHECK_ALL", f"체크된 항목: {checked_count}/{len(CHECKLIST_ITEMS)}")
    return checked_count


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


def execute(driver):
    """Step 5 실행"""
    try:
        # daily check 탭이 올바르게 로드되었는지 확인
        logger.log_step(5, "daily check 페이지 확인")

        # 항상 Create 버튼 클릭 (step4 후 상태 관계없이 새로운 페이지 로드)
        logger.log("STEP5", "PAGE_CHECK", "Create 버튼 클릭 중...")

        js_code = """
        return (function() {
            // Create 버튼 찾기 (aria-label="Create"인 a 태그)
            const links = document.querySelectorAll('a[aria-label="Create"]');
            if (links.length > 0) {
                links[0].scrollIntoView(true);
                links[0].click();
                return {success: true};
            }

            // 또는 "Create" 텍스트를 포함한 a 태그 찾기
            const allLinks = document.querySelectorAll('a');
            for (let link of allLinks) {
                if (link.textContent.includes('Create')) {
                    link.scrollIntoView(true);
                    link.click();
                    return {success: true};
                }
            }
            return {success: false};
        })();
        """

        result = driver.execute_script(js_code)
        sleep(2)

        # 모든 체크박스 체크
        checked_count = check_all_items(driver)

        # 저장
        saved = save_checklist(driver)

        return {
            'success': saved,
            'checked_count': checked_count,
            'total_items': len(CHECKLIST_ITEMS),
            'all_checked': checked_count == len(CHECKLIST_ITEMS),
            'saved': saved
        }

    except Exception as e:
        logger.log_error("STEP5", "EXECUTE", e)
        return {
            'success': False,
            'error': str(e)
        }
