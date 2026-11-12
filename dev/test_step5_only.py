"""
Step 5 단위 테스트 스크립트
daily check 페이지에서 8개 체크박스를 체크하는 기능만 테스트
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 프로젝트 루트(config·utils·steps) import용
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def test_step5():
    driver = setup_driver()
    
    try:
        # 1. 백오피스 접속
        print("\n=== Step 5 단위 테스트 시작 ===")
        print("1️⃣ 백오피스 접속 중...")
        driver.get(os.environ.get("CAFE24_URL", "http://localhost:3001"))
        time.sleep(2)
        
        # 2. daily check 탭 클릭
        print("2️⃣ daily check 탭 클릭 중...")
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
            return {success: false};
        })();
        """
        result = driver.execute_script(js_code)
        print(f"   결과: {result}")
        time.sleep(2)
        
        # 3. Create 버튼 클릭
        print("3️⃣ Create 버튼 클릭 중...")

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
        print(f"   결과: {result}")
        time.sleep(2)
        
        # 4. 체크박스 확인
        print("4️⃣ 8개 체크박스 확인 중...")
        checkbox_names = [
            "log_check_yn",
            "error_monitoring_yn",
            "api_error_monitoring_yn",
            "chatbot_test_yn",
            "new_domain_check_yn",
            "new_chatbot_test_yn",
            "cancel_domain_check_yn",
            "cancel_chatbot_check_yn",
        ]
        
        for name in checkbox_names:
            try:
                checkbox = driver.find_element(By.XPATH, f"//input[@name='{name}']")
                print(f"   ✅ {name}: 발견됨")
            except:
                print(f"   ❌ {name}: 찾을 수 없음")
        
        # 5. 체크박스 체크
        print("5️⃣ 8개 체크박스 체크 중...")
        for name in checkbox_names:
            js_code = f"""
            return (function() {{
                const checkbox = document.querySelector('input[name="{name}"]');
                if (!checkbox) {{
                    return {{found: false}};
                }}

                // MUI Switch는 label을 클릭해야 함
                const checkboxId = checkbox.id;
                const label = document.querySelector('label[for="' + checkboxId + '"]');

                if (label) {{
                    label.click();
                }} else {{
                    const parent = checkbox.closest('div[role="checkbox"], .MuiSwitch-root, div.MuiFormControlLabel-root');
                    if (parent) {{
                        parent.click();
                    }} else {{
                        checkbox.checked = true;
                        const event = new Event('change', {{ bubbles: true }});
                        checkbox.dispatchEvent(event);
                    }}
                }}

                return {{found: true, checked: true}};
            }})();
            """
            result = driver.execute_script(js_code)
            if result.get('found'):
                print(f"   ✅ {name}: 체크 완료")
            else:
                print(f"   ❌ {name}: 찾을 수 없음")
        
        # 6. 저장 버튼 클릭
        print("6️⃣ 저장 버튼 클릭 중...")

        js_code = """
        return (function() {
            // SAVE 버튼 찾기
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                const text = btn.textContent.trim().toUpperCase();
                if (text.includes('SAVE') || text.includes('저장')) {
                    btn.scrollIntoView(true);
                    btn.click();
                    return {success: true, text: btn.textContent};
                }
            }

            // 또는 type='submit' 버튼
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.scrollIntoView(true);
                submitBtn.click();
                return {success: true, text: submitBtn.textContent};
            }

            return {success: false};
        })();
        """

        result = driver.execute_script(js_code)
        if result.get('success'):
            print(f"   ✅ 저장 버튼 클릭 완료!")
            time.sleep(2)
        else:
            print(f"   ❌ 저장 버튼을 찾을 수 없음")
        
        print("\n=== Step 5 단위 테스트 완료 ===\n")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}\n")
        
    finally:
        input("브라우저를 닫으려면 엔터를 누르세요...")
        driver.quit()

if __name__ == "__main__":
    test_step5()
