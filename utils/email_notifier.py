"""
이메일 알림 전송 (Gmail SMTP 인증 발송)

기존에는 macOS `mail` 명령으로 발송했으나, 회사 메일(Office365)이
발신 PC의 공인 IP를 보고 차단(550 5.7.1)하여 사내망 IP가 아니면 모두 반송됐다.
인증 SMTP(Gmail 587 STARTTLS)는 IP가 아니라 계정 인증으로 발송하므로 망/IP와 무관하게 배달된다.
계정은 .env의 GMAIL_USER / GMAIL_APP_PASSWORD 사용.
이 .env는 주간보고 자동화(~/weekly-report/)도 함께 읽는다 — 바꾸면 양쪽에 반영된다.
"""
import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import email_html as H
from email.header import Header
from email.utils import formataddr
from datetime import datetime
from utils.logger import logger


def _load_env_file():
    """cron이 아닌 수동 실행(python3 main.py)에서도 .env를 읽도록 직접 로드한다.
    이미 os.environ에 있는 값은 덮어쓰지 않는다(run_daily.sh가 export한 값 우선)."""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


_load_env_file()


class EmailNotifier:
    def __init__(self, recipient_email):
        self.recipient_email = recipient_email

    def send_error_notification(self, error_message, step_name=""):
        """에러 발생 시 이메일 전송"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            subject = f"❌ Cafe24 자동화 실패 - {timestamp}"
            if step_name:
                subject += f" ({step_name})"

            body = f"""Cafe24 백오피스 일일 자동화 프로그램에서 에러가 발생했습니다.

{'='*50}
⏰ 시간: {timestamp}
{'='*50}

📝 에러 내용:
{error_message}

{'='*50}

📂 로그 파일:
~/cafe24_automation/output/logs.txt

🔧 해결 방법:
1. 로그 파일을 확인하세요
2. 문제를 파악하고 수정하세요
3. 수동으로 실행: python3 ~/cafe24_automation/main.py

---
이 메시지는 자동으로 생성되었습니다."""

            html = H.page(
                "일일 자동화 실패", "fail", f"{timestamp}" + (f" · {step_name}" if step_name else ""),
                [H.callout("에러 내용", str(error_message)),
                 H.section("해결 방법", H.ordered_rows([
                     "아래 로그 파일을 확인하세요",
                     "문제를 파악하고 수정하세요",
                     "수동 실행: python3 ~/cafe24_automation/main.py"]))],
                ["~/cafe24_automation/output/logs.txt"])
            self._send_email(subject, body, html)
            logger.log("EMAIL", "SEND", "에러 알림 이메일 전송 완료")
            return True

        except Exception as e:
            logger.log_error("EMAIL", "SEND", f"이메일 전송 실패: {e}")
            return False

    def send_success_notification(self, summary_text, summary=None, probe_text=None):
        """성공 알림 이메일 전송"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            subject = f"✅ Cafe24 자동화 완료 - {timestamp}"

            body = f"""Cafe24 백오피스 일일 자동화 프로그램이 성공적으로 완료되었습니다.

{'='*50}
⏰ 시간: {timestamp}
{'='*50}

📊 실행 결과:
{summary_text}

{'='*50}

✓ 모든 단계 완료:
1. Shop 탭 - 로그 수집
2. log stats - 로그 합계 확인
3. Dashboard - 수치 검증
4. daily check - 메모 입력 및 저장
5. 체크리스트 - 8개 항목 체크 및 저장

📂 로그 파일:
~/cafe24_automation/output/logs.txt
~/cafe24_automation/output/results.txt

---
이 메시지는 자동으로 생성되었습니다."""

            html = self._success_html(timestamp, summary_text, summary, probe_text)
            self._send_email(subject, body, html)
            logger.log("EMAIL", "SEND", "성공 알림 이메일 전송 완료")
            return True

        except Exception as e:
            logger.log_error("EMAIL", "SEND", f"이메일 전송 실패: {e}")
            return False

    def send_server_down_notification(self, url, detail=""):
        """백오피스 서버 미응답(다운/네트워크 단절) 전용 알림 이메일 전송"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            subject = f"🔌 Cafe24 백오피스 서버 응답 없음 - {timestamp}"

            body = f"""Cafe24 백오피스 서버에 접속할 수 없어 일일 자동화를 시작하지 못했습니다.

{'='*50}
⏰ 시간: {timestamp}
{'='*50}

🔌 서버가 응답하지 않습니다 (다운 또는 네트워크 단절).
   대상 주소: {url}
{f"   진단: {detail}" if detail else ""}

{'='*50}

ℹ️  이번 실행은 브라우저 자동화를 시작하기 전에 중단되었습니다.
    (코드 오류가 아니라 서버/네트워크 문제입니다.)

🔧 점검 항목:
1. 백오피스 서버({url})가 켜져 있는지 확인
2. 이 PC가 사내망에 연결되어 있는지 확인
3. 서버 복구 후 수동 실행: ~/cafe24_automation/run_daily.sh

---
이 메시지는 자동으로 생성되었습니다."""

            html = H.page(
                "백오피스 서버 응답 없음", "down", timestamp,
                [H.callout("서버가 응답하지 않습니다 (다운 또는 네트워크 단절)",
                           f"대상 주소: {url}" + (f"\n진단: {detail}" if detail else "")),
                 H.section("안내", H.text_rows(
                     "브라우저 자동화를 시작하기 전에 중단했습니다.\n코드 오류가 아니라 서버/네트워크 문제입니다.")),
                 H.section("점검 항목", H.ordered_rows([
                     f"백오피스 서버({url})가 켜져 있는지 확인",
                     "이 PC가 사내망에 연결되어 있는지 확인",
                     "서버 복구 후 수동 실행: ~/cafe24_automation/run_daily.sh"]))],
                ["~/cafe24_automation/output/logs.txt"])
            self._send_email(subject, body, html)
            logger.log("EMAIL", "SEND", "서버 다운 알림 이메일 전송 완료")
            return True

        except Exception as e:
            logger.log_error("EMAIL", "SEND", f"이메일 전송 실패: {e}")
            return False

    def send_error_increase_notification(self, today_errors, yesterday_errors):
        """에러 수 증가 알림 이메일 전송"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            increase = today_errors - yesterday_errors

            subject = f"⚠️  Cafe24 에러 증가 경고 - {timestamp}"

            body = f"""Cafe24 백오피스 에러 수가 전날보다 증가했습니다!

{'='*50}
⏰ 시간: {timestamp}
{'='*50}

📊 에러 현황:
어제 에러: {yesterday_errors}건
오늘 에러: {today_errors}건
증가량: {increase}건 ⬆️

{'='*50}

⚠️  주의:
월별 에러 수가 증가했으므로 시스템을 점검하세요.

📂 로그 파일:
~/cafe24_automation/output/logs.txt
~/cafe24_automation/output/results.txt

🔍 점검 항목:
1. 시스템 에러 로그 확인
2. API 연동 상태 확인
3. 데이터베이스 연결 확인

---
이 메시지는 자동으로 생성되었습니다."""

            html = H.page(
                "에러 수 증가 — 자동화 중단", "warn", timestamp,
                [H.section("에러 현황", H.metric_tiles([
                     ("어제 에러", f"{yesterday_errors}건", H.TEXT),
                     ("오늘 에러", f"{today_errors}건", H.RED),
                     ("증가량", f"+{increase}건", H.AMBER)])),
                 H.section("점검 항목", H.ordered_rows([
                     "시스템 에러 로그 확인", "API 연동 상태 확인", "데이터베이스 연결 확인"]))],
                ["~/cafe24_automation/output/logs.txt", "~/cafe24_automation/output/results.txt"])
            self._send_email(subject, body, html)
            logger.log("EMAIL", "SEND", "에러 증가 알림 이메일 전송 완료")
            return True

        except Exception as e:
            logger.log_error("EMAIL", "SEND", f"이메일 전송 실패: {e}")
            return False

    def _success_html(self, timestamp, summary_text, summary, probe_text):
        if summary:
            pairs = list(summary.items())
        else:
            pairs = [tuple(x.split(":", 1)) for x in summary_text.split("\n\n")[0].split("\n") if ":" in x]
            pairs = [(k.strip(), v.strip()) for k, v in pairs]
        d = {H.clean_label(k): v for k, v in pairs}
        tiles = [
            ("오늘 로그", d.get("Dashboard 오늘 로그 수", "-"), H.TEXT),
            ("이번달 에러", d.get("이번달 에러 건수", "-"), H.GREEN if d.get("이번달 에러 건수") == "0건" else H.AMBER),
            ("쇼핑몰", d.get("선택된 쇼핑몰 개수", "-"), H.TEXT),
        ]
        sections = [
            H.section("오늘 요약", H.metric_tiles(tiles)),
            H.section("실행 결과", H.kv_rows(pairs)),
            H.section("단계", H.steps_rows({n: "ok" for n in H.STEP_NAMES})),
        ]
        if probe_text:
            lines = probe_text.strip().split("\n")
            if lines and lines[0].startswith("["):
                lines = lines[1:]
            sections.append(H.section("도메인 해지 감지", H.text_rows("\n".join(lines).strip(), mono=True)))
        return H.page("일일 자동화 완료", "ok", timestamp, sections,
                      ["~/cafe24_automation/output/logs.txt", "~/cafe24_automation/output/results.txt"])

    def _send_email(self, subject, body, html=None):
        """Gmail SMTP(587 STARTTLS) 인증 발송. returncode 0이 곧 '큐 접수'였던
        기존 mail 방식과 달리, 서버가 250 응답을 줘야만 성공으로 처리되므로
        '발송 완료' 로그가 실제 배달을 보장한다(반송은 SMTP 단계에서 예외로 드러남)."""
        user = os.environ.get("GMAIL_USER")
        app_pw = (os.environ.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")
        if not user or not app_pw:
            raise Exception(
                "GMAIL_USER/GMAIL_APP_PASSWORD 미설정 — ~/cafe24_automation/.env 확인"
            )

        recipients = [r.strip() for r in self.recipient_email.split(",") if r.strip()]

        if html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
        else:
            msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = str(Header(subject, "utf-8"))
        msg["From"] = formataddr(("Cafe24 자동화", user))
        msg["To"] = ", ".join(recipients)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.starttls(context=context)
                server.login(user, app_pw)
                server.sendmail(user, recipients, msg.as_string())

            logger.log(
                "EMAIL", "COMMAND",
                f"{self.recipient_email}로 이메일 발송 완료 (Gmail SMTP / {user})"
            )

        except Exception as e:
            logger.log_error("EMAIL", "COMMAND", f"Gmail SMTP 발송 실패: {e}")
            raise e


# 전역 이메일 알림 인스턴스
# 수신 주소는 .env의 RECIPIENT_EMAIL로 덮어쓸 수 있다(콤마로 여러 명 지정 가능).
email_notifier = EmailNotifier(
    os.environ.get("RECIPIENT_EMAIL") or os.environ.get("GMAIL_USER", "")
)
