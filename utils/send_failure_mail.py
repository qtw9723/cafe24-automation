"""
cron 실패 알림 메일 (run_daily.sh 에서 호출).
  python3 -m utils.send_failure_mail <실행 로그 파일> <타임스탬프> [종료코드]
실행 로그를 파싱해 단계 진행·핵심 에러·최종 리포트·색칠된 로그를 다크 HTML로 보낸다.
이 스크립트가 실패하면 run_daily.sh 가 기존 텍스트 메일(mail)로 폴백한다.
"""
import os
import sys
from utils.email_notifier import email_notifier
from utils import email_html as H


def main():
    log_file, ts = sys.argv[1], sys.argv[2]
    code = sys.argv[3] if len(sys.argv) > 3 else "?"
    try:
        text = open(log_file, encoding="utf-8", errors="replace").read()
    except Exception as e:
        text = f"[ERROR] 로그 파일을 읽을 수 없습니다: {e}"
    info = H.parse_run_log(text)
    # 로그 표시는 마지막 시도만, 최종 리포트 직전까지(리포트는 위 표로 따로 보여줌)
    body_lines = info["lines"]
    for i, l in enumerate(body_lines):
        if "최종 결과 리포트" in l:
            body_lines = body_lines[:i]
            break
    tail = H.collapse_stacktrace(body_lines[-100:])

    sections = []
    if info["first_error"]:
        where, tag, msg = info["first_error"]
        title = f"{where} · {tag}" if where else "에러"
        hint = H.diagnose(msg)
        sections.append(H.callout(title, msg + (f"\n\n→ {hint}" if hint else "")))
    if info["earlier_errors"]:
        body = "\n".join(f"{w} · {t}: {m}" + (f"\n→ {H.diagnose(m)}" if H.diagnose(m) else "")
                          for w, t, m in info["earlier_errors"])
        sections.append(H.callout(f"이전 시도 실패 (총 {info['attempts']}회 시도)", body, H.AMBER))
    sections.append(H.section(f"단계 진행 (마지막 시도 {info['attempts']}회차)" if info["attempts"] > 1 else "단계 진행",
                              H.steps_rows(info["states"])))
    if info["report"]:
        sections.append(H.section("최종 결과", H.kv_rows(info["report"])))
    sections.append(H.section("해결 방법", H.ordered_rows([
        "아래 실행 로그에서 빨간 줄을 확인하세요",
        "일시적 오류(브라우저 세션 끊김 등)면 재실행만으로 해결됩니다",
        "수동 실행: python3 ~/cafe24_automation/main.py",
    ])))
    sections.append(H.section("실행 로그 (마지막 시도)", H.log_rows(tail)))

    html = H.page("일일 자동화 실패", "fail", f"{ts} · 종료 코드 {code}", sections,
                  [log_file.replace(os.path.expanduser("~"), "~"), "~/cafe24_automation/output/logs.txt"])
    plain = (f"Cafe24 백오피스 일일 자동화 프로그램에서 에러가 발생했습니다.\n\n시간: {ts}\n\n"
             + "\n".join(tail)
             + "\n\n수동 실행: python3 ~/cafe24_automation/main.py")
    email_notifier._send_email(f"❌ Cafe24 자동화 실패 - {ts}", plain, html)


if __name__ == "__main__":
    main()
