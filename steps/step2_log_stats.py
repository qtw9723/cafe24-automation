"""
2단계: log stats 탭 - 오늘 로그 합계 확인
- log stats 탭 이동
- '오늘 로그' 관련 텍스트 추출
- 숫자 추출 및 합계 계산 (로컬 처리)
"""
from selenium.webdriver.common.by import By
from utils.logger import logger
from utils.wait import safe_click, wait_for_element, sleep
from utils.parser import extract_numbers


def click_log_stats_tab(driver):
    """log stats 탭 클릭 (JavaScript 사용)"""
    logger.log_step(2, "log stats 탭 클릭")

    try:
        # JavaScript로 탭 찾기
        js_code = """
        return (function() {
            const tabs = document.querySelectorAll('a');
            for (let tab of tabs) {
                const text = tab.textContent.toLowerCase();
                if (text.includes('log') && text.includes('stats')) {
                    tab.scrollIntoView(true);
                    tab.click();
                    return {success: true};
                }
            }
            return {success: false, reason: 'log stats 탭을 찾을 수 없음'};
        })();
        """

        result = driver.execute_script(js_code)

        if result and result.get('success'):
            sleep(2)
            logger.log_success(2, "CLICK_TAB", "log stats 탭 클릭 완료")
            return True
        else:
            logger.log_error("STEP2", "CLICK_TAB", result.get('reason', 'log stats 탭을 찾을 수 없음'))
            return False

    except Exception as e:
        logger.log_error("STEP2", "CLICK_TAB", e)
        return False


def extract_today_log_text(driver):
    """'오늘 로그' 관련 텍스트 추출 (각 로우의 숫자들)"""
    logger.log_step(2, "'오늘 로그' 텍스트 추출")

    try:
        # column-todayLogs 클래스를 가진 모든 td 찾기
        log_cells = driver.find_elements(
            By.XPATH,
            "//td[contains(@class, 'column-todayLogs')]"
        )

        extracted_numbers = []

        for cell in log_cells:
            try:
                # 각 셀의 span > div에서 숫자 추출
                div = cell.find_element(By.XPATH, ".//div")
                text = div.text
                if text and text.isdigit():
                    extracted_numbers.append(text)
            except:
                continue

        # 숫자들을 공백으로 구분해서 반환
        combined_text = ' '.join(extracted_numbers)
        logger.log_success(2, "EXTRACT", f"총 {len(extracted_numbers)}개 숫자 추출 완료")

        return combined_text

    except Exception as e:
        logger.log_error("STEP2", "EXTRACT", e)
        return ""


def extract_month_error_text(driver):
    """'이번달 에러' (6월 오류 등) 관련 텍스트 추출"""
    logger.log_step(2, "'이번달 에러' 텍스트 추출")

    try:
        # column-thisMonthErr 클래스를 가진 모든 td 찾기
        error_cells = driver.find_elements(
            By.XPATH,
            "//td[contains(@class, 'column-thisMonthErr')]"
        )

        extracted_numbers = []

        for cell in error_cells:
            try:
                # 각 셀의 span > div에서 숫자 추출
                div = cell.find_element(By.XPATH, ".//div")
                text = div.text
                if text and text.isdigit():
                    extracted_numbers.append(text)
            except:
                continue

        # 숫자들을 공백으로 구분해서 반환
        combined_text = ' '.join(extracted_numbers)
        logger.log_success(2, "EXTRACT_ERROR", f"총 {len(extracted_numbers)}개 숫자 추출 완료")

        return combined_text

    except Exception as e:
        logger.log_error("STEP2", "EXTRACT_ERROR", e)
        return ""


def calculate_log_sum(text_content):
    """로컬 코드로 로그 합계 계산"""
    logger.log_step(2, "로그 합계 계산 (로컬 처리)")

    try:
        if not text_content:
            logger.log_error("STEP2", "CALCULATE", "추출된 텍스트가 없음")
            return 0

        # 텍스트에서 모든 숫자 추출
        numbers = extract_numbers(text_content)

        if not numbers:
            logger.log("STEP2", "CALCULATE", "숫자를 찾을 수 없음")
            return 0

        # 모든 숫자의 합 계산
        result = sum(numbers)
        logger.log_success(2, "CALCULATE", f"로그 합계: {result}건 (추출된 숫자: {numbers})")
        return result

    except Exception as e:
        logger.log_error("STEP2", "CALCULATE", e)
        return 0


def calculate_error_sum(text_content):
    """로컬 코드로 이번달 에러 합계 계산"""
    logger.log_step(2, "이번달 에러 합계 계산 (로컬 처리)")

    try:
        if not text_content:
            logger.log_error("STEP2", "CALCULATE_ERROR", "추출된 텍스트가 없음")
            return 0

        # 텍스트에서 모든 숫자 추출
        numbers = extract_numbers(text_content)

        if not numbers:
            logger.log("STEP2", "CALCULATE_ERROR", "숫자를 찾을 수 없음")
            return 0

        # 모든 숫자의 합 계산
        result = sum(numbers)
        logger.log_success(2, "CALCULATE_ERROR", f"이번달 에러 합계: {result}건 (추출된 숫자: {numbers})")
        return result

    except Exception as e:
        logger.log_error("STEP2", "CALCULATE_ERROR", e)
        return 0


def execute(driver):
    """Step 2 실행"""
    try:
        if not click_log_stats_tab(driver):
            return {
                'success': False,
                'error': "log stats 탭으로 이동 실패"
            }

        # 오늘 로그 추출
        text_content = extract_today_log_text(driver)
        log_sum = calculate_log_sum(text_content)

        # 이번달 에러 추출
        error_text = extract_month_error_text(driver)
        month_error_sum = calculate_error_sum(error_text)

        return {
            'success': True,
            'today_log_sum': log_sum,
            'month_error_sum': month_error_sum,
            'extracted_text': text_content,
            'error_text': error_text
        }

    except Exception as e:
        logger.log_error("STEP2", "EXECUTE", e)
        return {
            'success': False,
            'error': str(e)
        }
