"""
1단계: Shop 탭 - 로그 수집
- 로그인 후 Shop 탭 이동
- '전체 선택' 체크박스 확인/체크
- '오늘 로그 수집' 클릭
- '이번달 로그 수집' 클릭
"""
from selenium.webdriver.common.by import By
import config
from utils.logger import logger
from utils.wait import safe_click, wait_for_element, sleep
from utils.parser import get_current_month


def access_backoffice(driver):
    """Cafe24 백오피스 접속 (로그인 상태 가정)"""
    logger.log_step(1, "백오피스 접속")

    try:
        # 백오피스 URL 접속 (이미 로그인된 상태)
        driver.get(config.CAFE24_URL)
        sleep(2)
        logger.log_success(1, "ACCESS", "백오피스 접속 완료")
        return True

    except Exception as e:
        logger.log_error("STEP1", "ACCESS", e)
        raise e


def click_shop_tab(driver):
    """Shop 탭 클릭"""
    logger.log_step(1, "Shop 탭 클릭")

    try:
        shop_tab = wait_for_element(
            driver,
            (By.XPATH, "//a[contains(text(), 'Shop')]")
        )
        safe_click(driver, (By.XPATH, "//a[contains(text(), 'Shop')]"))
        sleep(2)
        logger.log_success(1, "CLICK_TAB", "Shop 탭 클릭 완료")

    except Exception as e:
        logger.log_error("STEP1", "CLICK_TAB", e)
        raise e


def check_select_all(driver):
    """'전체 선택' 체크박스 확인 및 체크"""
    logger.log_step(1, "'전체 선택' 체크박스 확인")

    try:
        # JavaScript로 span 클래스 확인 (Mui-checked 여부)
        js_code = """
        return (function() {
            const span = document.querySelector('span.select-all');
            if (!span) {
                return {found: false};
            }

            const isChecked = span.classList.contains('Mui-checked');
            return {found: true, checked: isChecked};
        })();
        """

        result = driver.execute_script(js_code)

        if not result.get('found'):
            logger.log_error("STEP1", "CHECK_ALL", "전체 선택 체크박스를 찾을 수 없음")
            return 0

        is_checked = result.get('checked', False)

        if not is_checked:
            logger.log("STEP1", "CHECK_ALL", "전체 선택 체크박스가 체크되지 않음. 클릭 중...")

            # input 요소 클릭
            js_code = """
            return (function() {
                const input = document.querySelector('input[data-indeterminate="false"][aria-label="Select all"]');
                if (input) {
                    input.click();
                    return {success: true};
                }
                return {success: false};
            })();
            """

            click_result = driver.execute_script(js_code)
            sleep(1)

            if click_result.get('success'):
                logger.log_success(1, "CHECK_ALL", "전체 선택 체크 완료")
            else:
                logger.log_error("STEP1", "CHECK_ALL", "전체 선택 클릭 실패")
        else:
            logger.log_success(1, "CHECK_ALL", "이미 전체 선택되어 있음")

        # 선택된 쇼핑몰 개수 파악
        shop_rows = driver.find_elements(By.XPATH, "//tbody/tr")
        shop_count = len(shop_rows)

        logger.log("STEP1", "CHECK_ALL", f"선택된 쇼핑몰: {shop_count}개")
        return shop_count

    except Exception as e:
        logger.log_error("STEP1", "CHECK_ALL", e)
        return 0


def collect_today_logs(driver):
    """'오늘 로그 수집' 버튼 클릭"""
    logger.log_step(1, "'오늘 로그 수집' 버튼 클릭")

    try:
        # JavaScript로 버튼 찾기 (텍스트 포함)
        js_code = """
        return (function() {
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                if (btn.textContent.includes('오늘 로그 수집')) {
                    btn.scrollIntoView(true);
                    btn.click();
                    return {success: true};
                }
            }
            return {success: false};
        })();
        """

        result = driver.execute_script(js_code)

        if result and result.get('success'):
            logger.log("STEP1", "COLLECT_TODAY", "버튼 클릭 완료, 30초 대기 중...")

            # 대기 중에 주기적으로 연결 확인
            for i in range(30):
                sleep(1)
                try:
                    driver.current_url  # 연결 확인
                except:
                    logger.log_error("STEP1", "COLLECT_TODAY", "대기 중 Chrome 연결 끊김!")
                    raise Exception("Chrome 연결이 끊어졌습니다")

            logger.log_success(1, "COLLECT_TODAY", "오늘 로그 수집 완료")
        else:
            logger.log_error("STEP1", "COLLECT_TODAY", "버튼을 찾을 수 없음")

    except Exception as e:
        logger.log_error("STEP1", "COLLECT_TODAY", e)
        raise e


def collect_month_logs(driver):
    """'이번달 로그 수집' 버튼 클릭"""
    logger.log_step(1, "'이번달 로그 수집' 버튼 클릭")

    try:
        month = get_current_month()

        # JavaScript로 버튼 찾기 (텍스트 포함)
        js_code = f"""
        return (function() {{
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {{
                if (btn.textContent.includes('{month}월 로그 수집')) {{
                    btn.scrollIntoView(true);
                    btn.click();
                    return {{success: true}};
                }}
            }}
            return {{success: false}};
        }})();
        """

        result = driver.execute_script(js_code)

        if result and result.get('success'):
            logger.log("STEP1", "COLLECT_MONTH", "버튼 클릭 완료, 120초(2분) 대기 중...")

            # 대기 중에 주기적으로 연결 확인 (10초마다)
            for i in range(12):  # 12 * 10초 = 120초
                sleep(10)
                try:
                    driver.current_url  # 연결 확인
                except:
                    logger.log_error("STEP1", "COLLECT_MONTH", "대기 중 Chrome 연결 끊김!")
                    raise Exception("Chrome 연결이 끊어졌습니다")

            logger.log_success(1, "COLLECT_MONTH", "이번달 로그 수집 완료")
        else:
            logger.log_error("STEP1", "COLLECT_MONTH", "버튼을 찾을 수 없음")

    except Exception as e:
        logger.log_error("STEP1", "COLLECT_MONTH", e)
        raise e


def execute(driver):
    """Step 1 실행"""
    try:
        access_backoffice(driver)
        click_shop_tab(driver)
        shop_count = check_select_all(driver)
        collect_today_logs(driver)
        collect_month_logs(driver)

        return {
            'success': True,
            'shop_count': shop_count
        }

    except Exception as e:
        logger.log_error("STEP1", "EXECUTE", e)
        return {
            'success': False,
            'error': str(e)
        }
