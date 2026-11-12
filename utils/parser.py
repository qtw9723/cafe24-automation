"""
텍스트 파싱 유틸리티
"""
import re
from datetime import datetime, timedelta


def extract_numbers(text):
    """텍스트에서 모든 숫자 추출"""
    numbers = re.findall(r'\d+', text)
    return [int(n) for n in numbers]


def extract_first_number(text):
    """텍스트에서 첫 번째 숫자 추출"""
    numbers = extract_numbers(text)
    return numbers[0] if numbers else 0


def extract_number_with_unit(text, unit='건'):
    """'건' 같은 단위가 붙은 숫자 추출"""
    pattern = rf'(\d+)\s*{unit}'
    match = re.search(pattern, text)
    return int(match.group(1)) if match else 0


def get_today_date_string():
    """오늘 날짜를 문자열로 반환 (YYYY-MM-DD)"""
    return datetime.now().strftime("%Y-%m-%d")


def get_yesterday_date_string():
    """어제 날짜를 문자열로 반환 (YYYY-MM-DD)"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def get_current_month():
    """현재 월을 정수로 반환"""
    return datetime.now().month


def parse_table_to_dict(table_element):
    """테이블을 딕셔너리로 파싱"""
    rows = table_element.find_elements("tag name", "tr")
    data = []

    for row in rows:
        cells = row.find_elements("tag name", "td")
        row_data = [cell.text for cell in cells]
        data.append(row_data)

    return data


def clean_text(text):
    """텍스트 정제 (공백, 특수문자 제거)"""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def format_memo(dashboard_logs, month, error_count):
    """메모 포맷팅"""
    return f"오늘 로그: {dashboard_logs}건 / {month}월 에러: {error_count}건"
