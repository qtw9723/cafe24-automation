"""
Cafe24 자동화 설정 파일
민감하거나 환경마다 다른 값(백오피스 주소·메일 계정)은 .env 로 주입한다 (.env.example 참고).
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 수동 실행(python main.py)에서도 .env 를 읽도록. 크론(run_daily.sh)은 셸에서 먼저 export 하므로
# 이미 설정된 환경변수는 덮어쓰지 않는다(override=False).
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)
except ImportError:
    pass

# Cafe24 백오피스 설정
CAFE24_URL = os.environ.get("CAFE24_URL", "http://localhost:3001")
# 참고: 이미 로그인된 상태에서 실행됩니다 (로그인 불필요)

# Selenium 설정
CHROME_HEADLESS = False  # True면 헤드리스 모드, False면 GUI 표시
IMPLICIT_WAIT = 10
EXPLICIT_WAIT = 15

# 대기 시간 (초)
WAIT_AFTER_LOG_COLLECTION = 8
WAIT_AFTER_SAVE = 2

# 파일 경로
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_FILE = f"{OUTPUT_DIR}/logs.txt"
RESULTS_FILE = f"{OUTPUT_DIR}/results.txt"

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2  # 초
MAX_RUN_ATTEMPTS = 2  # 전체 자동화 재시도 횟수 (invalid session id 등 일시적 브라우저 사망 대비)

# XPath 및 CSS 선택자들
SELECTORS = {
    # Shop 탭
    "shop_tab": "//a[contains(text(), 'Shop')]",
    "select_all_checkbox": "//input[@type='checkbox' and @class='select-all']",
    "today_log_button": "//button[contains(text(), '오늘 로그 수집')]",
    "month_log_button": "//button[contains(text(), '이번달 로그 수집')]",

    # log stats 탭
    "log_stats_tab": "//a[contains(text(), 'log stats')]",
    "today_log_text": "//div[contains(text(), '오늘 로그')]",

    # Dashboard 탭
    "dashboard_tab": "//a[contains(text(), 'Dashboard')]",
    "today_logs_value": "//div[contains(text(), \"Today's 로그\") or contains(text(), 'Today logs')]",
    "month_error_value": "//div[contains(text(), '이번달 에러')]",

    # daily check 탭
    "daily_check_tab": "//a[contains(text(), 'daily check')]",
    "yesterday_item": "//button[contains(text(), 'yesterday_date_placeholder')]",
    "today_item": "//button[contains(text(), 'today_date_placeholder')]",
    "memo_field": "//textarea[@class='memo']",
    "save_button": "//button[contains(text(), 'SAVE') or contains(text(), '저장')]",

    # 체크박스들
    "checkboxes": [
        "//input[@name='log_check']",
        "//input[@name='error_check']",
        "//input[@name='api_error_check']",
        "//input[@name='chatbot_check']",
        "//input[@name='new_domain_check']",
        "//input[@name='new_chatbot_check']",
        "//input[@name='cancel_domain_check']",
        "//input[@name='cancel_chatbot_check']",
    ]
}
