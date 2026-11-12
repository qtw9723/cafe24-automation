"""
Step 5 디버깅 - 페이지의 모든 버튼 텍스트 확인
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 프로젝트 루트(config·utils·steps) import용
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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

def debug():
    driver = setup_driver()
    
    try:
        # 백오피스 접속
        print("백오피스 접속 중...")
        driver.get(os.environ.get("CAFE24_URL", "http://localhost:3001"))
        time.sleep(2)
        
        # daily check 탭 클릭
        print("daily check 탭 클릭 중...")
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
        print(f"결과: {result}")
        time.sleep(3)
        
        # 페이지의 모든 버튼/링크 텍스트 출력
        print("\n=== 📋 페이지의 모든 버튼/링크 텍스트 ===\n")
        
        js_code = """
        const elements = document.querySelectorAll('button, a, div[role="button"]');
        const texts = [];
        elements.forEach((el, idx) => {
            const text = el.textContent.trim();
            if (text.length > 0 && text.length < 200) {
                texts.push({
                    index: idx,
                    tag: el.tagName,
                    text: text.substring(0, 100)
                });
            }
        });
        return texts;
        """
        
        all_texts = driver.execute_script(js_code)
        
        for item in all_texts:
            print(f"[{item['index']}] <{item['tag']}> {item['text']}")
        
        print("\n=== 🔍 날짜 포함 항목 ===\n")
        for item in all_texts:
            if any(char.isdigit() for char in item['text']) and ('월' in item['text'] or '일' in item['text']):
                print(f"✅ [{item['index']}] <{item['tag']}> {item['text']}")
        
        print("\n✅ 디버깅 완료. 위의 결과를 확인해서 실제 날짜 형식을 찾으세요!")
        time.sleep(2)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug()
