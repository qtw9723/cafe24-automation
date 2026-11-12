"""
로깅 유틸리티
"""
import os
from datetime import datetime
import config


class Logger:
    def __init__(self):
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        self.log_file = config.LOGS_FILE
        self.results_file = config.RESULTS_FILE

    def log(self, step, action, message, status="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{step}] [{action}] [{status}] {message}"

        # 콘솔 출력
        print(log_message)

        # 파일 저장
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')

    def log_step(self, step_num, message):
        self.log(f"STEP{step_num}", "INFO", message)

    def log_error(self, step, action, error):
        self.log(step, action, str(error), status="ERROR")

    def log_success(self, step, action, message="Success"):
        self.log(step, action, message, status="SUCCESS")

    def save_results(self, results):
        """최종 결과를 파일에 저장"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.results_file, 'w', encoding='utf-8') as f:
            f.write(f"[{timestamp}] Cafe24 일일 자동화 완료\n")
            f.write("=" * 50 + "\n\n")

            for key, value in results.items():
                f.write(f"✅ {key}: {value}\n")

            f.write("\n" + "=" * 50 + "\n")

        print(f"\n최종 결과가 {self.results_file}에 저장되었습니다.")

    def clear_logs(self):
        """로그 파일 초기화"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("")


# 전역 logger 인스턴스
logger = Logger()
