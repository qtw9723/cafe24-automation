"""
3단계: Dashboard 탭 - 수치 검증
- Dashboard 탭 이동
- "Today's 로그" 또는 "Today logs" 수치 확인
- "이번달 에러" 수치 확인
"""
from selenium.webdriver.common.by import By
from utils.logger import logger
from utils.wait import safe_click, wait_for_element, sleep
from utils.parser import extract_first_number, extract_number_with_unit


def click_dashboard_tab(driver):
    """Dashboard 탭 클릭"""
    logger.log_step(3, "Dashboard 탭 클릭")

    try:
        tab_selectors = [
            (By.XPATH, "//a[contains(text(), 'Dashboard')]"),
            (By.CSS_SELECTOR, "a[class*='dashboard']"),
        ]

        for selector in tab_selectors:
            try:
                safe_click(driver, selector)
                sleep(2)
                logger.log_success(3, "CLICK_TAB", "Dashboard 탭 클릭 완료")
                return True
            except:
                continue

        logger.log_error("STEP3", "CLICK_TAB", "Dashboard 탭을 찾을 수 없음")
        return False

    except Exception as e:
        logger.log_error("STEP3", "CLICK_TAB", e)
        return False


def extract_today_logs_value(driver):
    """"Today's 로그" 또는 "Today logs" 수치 추출"""
    logger.log_step(3, "Today's 로그 수치 추출")

    try:
        selectors = [
            (By.XPATH, "//*[contains(text(), \"Today's 로그\")]"),
            (By.XPATH, "//*[contains(text(), 'Today logs')]"),
            (By.XPATH, "//*[contains(text(), '오늘')]"),
        ]

        for selector in selectors:
            try:
                elem = driver.find_element(*selector)
                text = elem.text
                if text:
                    value = extract_first_number(text)
                    if value > 0:
                        logger.log_success(3, "EXTRACT_TODAY", f"Today 로그: {value}건")
                        return value
            except:
                continue

        # 페이지 전체에서 '오늘' 또는 'today' 관련 숫자 찾기
        body = driver.find_element(By.TAG_NAME, "body")
        page_text = body.text
        lines = page_text.split('\n')

        for i, line in enumerate(lines):
            if 'today' in line.lower() or '오늘' in line:
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    value = extract_first_number(next_line)
                    if value > 0:
                        logger.log_success(3, "EXTRACT_TODAY", f"Today 로그: {value}건")
                        return value

        logger.log("STEP3", "EXTRACT_TODAY", "Today 로그 수치를 찾을 수 없음")
        return 0

    except Exception as e:
        logger.log_error("STEP3", "EXTRACT_TODAY", e)
        return 0


def extract_month_error_value(driver):
    """'이번달 에러' 수치 추출 - Dashboard의 월별 에러"""
    logger.log_step(3, "이번달 에러 수치 추출")

    try:
        # Dashboard에서 "6월 에러" 또는 "{월}월 에러" 형식 찾기
        from datetime import datetime
        current_month = datetime.now().month

        # 각 월의 이름
        month_names = ['', '1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
        month_name = month_names[current_month]

        selectors = [
            (By.XPATH, f"//*[contains(text(), '{month_name} 에러')]"),
            (By.XPATH, "//*[contains(text(), '에러') and contains(text(), '건')]"),
        ]

        for selector in selectors:
            try:
                elem = driver.find_element(*selector)
                text = elem.text
                if text:
                    logger.log("STEP3", "EXTRACT_ERROR", f"찾은 텍스트: {text}")
                    value = extract_first_number(text)
                    if value >= 0:
                        logger.log_success(3, "EXTRACT_ERROR", f"이번달 에러: {value}건")
                        return value
            except:
                continue

        logger.log("STEP3", "EXTRACT_ERROR", "이번달 에러를 찾을 수 없음")
        return 0

    except Exception as e:
        logger.log_error("STEP3", "EXTRACT_ERROR", e)
        return 0


def execute(driver):
    """Step 3 실행"""
    try:
        if not click_dashboard_tab(driver):
            return {
                'success': False,
                'error': "Dashboard 탭으로 이동 실패"
            }

        today_logs = extract_today_logs_value(driver)
        month_errors = extract_month_error_value(driver)

        return {
            'success': True,
            'today_logs': today_logs,
            'month_errors': month_errors
        }

    except Exception as e:
        logger.log_error("STEP3", "EXECUTE", e)
        return {
            'success': False,
            'error': str(e)
        }
