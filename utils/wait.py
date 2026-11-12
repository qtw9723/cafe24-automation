"""
Selenium 대기 유틸리티
"""
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import config
from utils.logger import logger


def wait_for_element(driver, locator, timeout=config.EXPLICIT_WAIT):
    """요소가 나타날 때까지 대기"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return element
    except TimeoutException:
        raise TimeoutException(f"요소를 찾을 수 없음: {locator}")


def wait_for_clickable(driver, locator, timeout=config.EXPLICIT_WAIT):
    """요소가 클릭 가능할 때까지 대기"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        return element
    except TimeoutException:
        raise TimeoutException(f"요소가 클릭 불가능: {locator}")


def wait_for_visibility(driver, locator, timeout=config.EXPLICIT_WAIT):
    """요소가 보일 때까지 대기"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
        return element
    except TimeoutException:
        raise TimeoutException(f"요소가 보이지 않음: {locator}")


def safe_click(driver, locator, retry_count=config.MAX_RETRIES):
    """안전한 클릭 (재시도 포함)"""
    for attempt in range(retry_count):
        try:
            element = wait_for_clickable(driver, locator)
            element.click()
            return True
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(config.RETRY_DELAY)
            else:
                raise e
    return False


def safe_fill_text(driver, locator, text, retry_count=config.MAX_RETRIES):
    """안전한 텍스트 입력 (재시도 포함)"""
    for attempt in range(retry_count):
        try:
            element = wait_for_element(driver, locator)
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(config.RETRY_DELAY)
            else:
                raise e
    return False


def safe_get_text(driver, locator, retry_count=config.MAX_RETRIES):
    """안전한 텍스트 추출 (재시도 포함)"""
    for attempt in range(retry_count):
        try:
            element = wait_for_visibility(driver, locator)
            return element.text
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(config.RETRY_DELAY)
            else:
                raise e
    return ""


def sleep(seconds):
    """대기"""
    time.sleep(seconds)
