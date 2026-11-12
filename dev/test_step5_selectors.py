"""
Step 5 체크박스 셀렉터 테스트 스크립트
daily check 페이지에서 8개 항목의 체크박스를 찾을 수 있는지 테스트
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 프로젝트 루트(config·utils·steps) import용
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# Cafe24 설정
CAFE24_URL = os.environ.get("CAFE24_URL", "http://localhost:3001")

# 체크해야 할 항목들
CHECKLIST_ITEMS = [
    "로그 수집 확인",
    "에러 모니터링 확인",
    "API 에러 모니터링 확인",
    "챗봇 동작 확인",
    "신규 도메인 처리 확인",
    "신규 챗봇 동작 검증 확인",
    "해지 도메인 처리 확인",
    "해지 챗봇 처리 확인",
]

def setup_driver():
    """Selenium WebDriver 설정"""
    chrome_options = Options()
    # GUI 모드로 실행 (테스트용)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def test_checkbox_selectors(driver):
    """체크박스 셀렉터 테스트"""
    print("=" * 60)
    print("Step 5 체크박스 셀렉터 테스트")
    print("=" * 60)

    # daily check create 페이지로 이동
    driver.get(CAFE24_URL)
    time.sleep(2)

    # JavaScript로 daily check create 페이지로 이동
    driver.execute_script("window.location.hash = '#/dailyChecks/create';")
    time.sleep(3)

    # 각 항목의 체크박스를 찾아보기
    found_count = 0
    for item_name in CHECKLIST_ITEMS:
        print(f"\n[검색] '{item_name}' 체크박스 찾기")

        # 사용할 셀렉터들
        selectors = [
            (By.XPATH, f"//*[contains(@class, 'MuiFormControlLabel-label') and contains(text(), '{item_name}')]/ancestor::label//input[@type='checkbox']"),
            (By.XPATH, f"//*[contains(@class, 'MuiFormControlLabel-label') and contains(text(), '{item_name}')]/ancestor::*[contains(@class, 'MuiFormControlLabel-root')]//input[@type='checkbox']"),
            (By.XPATH, f"//div[contains(@class, 'MuiFormControlLabel-root')]//*[contains(text(), '{item_name}')]/ancestor::div[contains(@class, 'MuiFormControlLabel-root')]//input[@type='checkbox']"),
            (By.XPATH, f"//label[contains(text(), '{item_name}')]//input[@type='checkbox']"),
            (By.XPATH, f"//*[contains(text(), '{item_name}')]//input[@type='checkbox']"),
        ]

        found = False
        for i, selector in enumerate(selectors):
            try:
                elements = driver.find_elements(*selector)
                if elements:
                    print(f"  ✅ 셀렉터 {i+1} 성공 - {len(elements)}개 요소 찾음")
                    # 첫 번째 요소의 상태 확인
                    checkbox = elements[0]
                    is_checked = checkbox.is_selected()
                    print(f"     상태: {'체크됨' if is_checked else '미체크'}")
                    found = True
                    found_count += 1
                    break
            except Exception as e:
                print(f"  ❌ 셀렉터 {i+1} 실패: {str(e)[:50]}")
                continue

        if not found:
            print(f"  ⚠️  '{item_name}' 체크박스를 찾을 수 없음")

    print("\n" + "=" * 60)
    print(f"결과: {found_count}/{len(CHECKLIST_ITEMS)} 항목 발견")
    print("=" * 60)

    return found_count == len(CHECKLIST_ITEMS)

def main():
    driver = None
    try:
        driver = setup_driver()
        success = test_checkbox_selectors(driver)

        if success:
            print("\n✅ 모든 체크박스를 찾을 수 있습니다!")
        else:
            print("\n⚠️  일부 체크박스를 찾을 수 없습니다.")
            print("    XPath 셀렉터를 조정이 필요합니다.")

        input("\n브라우저를 확인한 후 엔터를 누르세요...")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("테스트 완료")

if __name__ == "__main__":
    main()
