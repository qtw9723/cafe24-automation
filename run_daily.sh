#!/bin/bash
# Cafe24 일일 자동화 실행 스크립트 (크론용)
#   crontab 예: 0 11 * * * /path/to/cafe24_automation/run_daily.sh
# 환경마다 다른 값(백오피스 주소·메일 계정·수신자·프로브 경로)은 .env 에서 읽는다 (.env.example 참고).

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

# Lock 파일 경로
LOCK_FILE="$BASE_DIR/.cron_lock"
LOCK_TIMEOUT=3600  # 1시간 타임아웃

# 날짜 기반 로그 파일
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
mkdir -p "$BASE_DIR/output"
LOG_FILE="$BASE_DIR/output/cron_run_${TIMESTAMP}.log"

# ===== Lock 메커니즘 =====
# 이미 실행 중인지 확인
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE")
    # 프로세스가 여전히 실행 중인지 확인
    if kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] 자동화가 이미 실행 중입니다 (PID: $LOCK_PID)" >> "$LOG_FILE"
        exit 1
    else
        # 프로세스가 종료됨, lock 파일 제거
        rm -f "$LOCK_FILE"
    fi
fi

# Lock 파일 생성 (현재 프로세스 PID 저장)
echo $$ > "$LOCK_FILE"

# 환경변수에서 설정 (Optional)
# .env 파일이 있으면 로드 (주석/공백/괄호가 있어도 안전한 표준 방식)
if [ -f "$BASE_DIR/.env" ]; then
    set -a
    . "$BASE_DIR/.env"
    set +a
fi
RECIPIENT_EMAIL="${RECIPIENT_EMAIL:-$GMAIL_USER}"

# ===== 도메인 해지 감지 프로브 (조회 전용, 2026-09-16 추가) =====
# 백오피스 API를 도메인별로 1회씩 GET 해 해지(401) 여부를 누적한다. 쓰기 없음.
# main.py 보다 먼저 돌려 요약 파일을 만들고, main.py 가 그 내용을 성공 알림 메일에 덧붙인다.
# (메일은 기존대로 main.py 한 곳에서만 보낸다 — 여기서 따로 보내지 않는다)
# 실패해도 일일 자동화를 막지 않는다. 그 경우 메일에 '프로브 실패 의심'으로 표시된다.
# 프로브는 백오피스 저장소(cafe24-monitoring)에 있다. 경로는 .env 의 CANCEL_PROBE_DIR 로 지정.
PROBE_DIR="${CANCEL_PROBE_DIR:-$HOME/IdeaProjects/cafe24-monitoring/cafe24_backoffice/tools/cancel_probe}"
PROBE_SUMMARY="$BASE_DIR/output/cancel_probe_summary.txt"
if [ -f "$PROBE_DIR/probe.py" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 해지 감지 프로브 시작" >> "$LOG_FILE"
    PROBE_BASE_URL="${PROBE_BASE_URL:-$CAFE24_URL}" \
        /usr/bin/python3 "$PROBE_DIR/probe.py" --summary-file "$PROBE_SUMMARY" >> "$LOG_FILE" 2>&1 \
        || echo "[WARN] 해지 감지 프로브 실패(무시) - $TIMESTAMP" >> "$LOG_FILE"
fi

# 프로그램 실행 (로그 저장)
# caffeinate로 감싸 실행 중에는 (소요 시간과 무관하게) 절전 진입을 막는다.
#   -i 유휴 시스템 절전 방지 / -m 디스크 절전 방지 / -s 시스템 절전 방지(AC 전원 시)
/usr/bin/caffeinate -ims /usr/bin/python3 "$BASE_DIR/main.py" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

# Lock 파일 제거
rm -f "$LOCK_FILE"

# 실행 결과 기록
if [ $EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] 일일 자동화 완료 - $TIMESTAMP" >> "$BASE_DIR/output/cron_schedule.log"

    # 성공 알림 메일은 main.py(email_notifier.send_success_notification)에서 실제 수치를 담아 1회 발송한다.
    # 여기서 또 보내면 성공 시 메일이 2통 오므로 발송하지 않는다(중복 방지). 실패 알림은 아래 else에서 처리.
elif [ $EXIT_CODE -eq 2 ]; then
    # 종료코드 2 = 백오피스 서버 다운/네트워크 단절.
    # main.py가 이미 '서버 다운' 전용 메일(send_server_down_notification)을 1회 발송했으므로,
    # 여기서 일반 실패 메일을 또 보내면 중복이 된다 → 발송하지 않고 로그만 남긴다(성공 시와 동일 패턴).
    echo "[SERVER_DOWN] 백오피스 서버 응답 없음 - $TIMESTAMP (종료 코드: $EXIT_CODE)" >> "$BASE_DIR/output/cron_schedule.log"
else
    echo "[ERROR] 일일 자동화 실패 - $TIMESTAMP (종료 코드: $EXIT_CODE)" >> "$BASE_DIR/output/cron_schedule.log"

    # 실패 시 이메일 알림 발송
    EMAIL_SUBJECT="❌ Cafe24 자동화 실패 - $TIMESTAMP"
    EMAIL_BODY="Cafe24 백오피스 일일 자동화 프로그램에서 에러가 발생했습니다.

========================================
시간: $TIMESTAMP
========================================

에러 내용:
$(tail -100 "$LOG_FILE" 2>/dev/null || echo "로그 파일을 읽을 수 없습니다")

========================================

로그 파일: ~/cafe24_automation/output/logs.txt

해결 방법:
1. 로그 파일을 확인하세요
2. 문제를 파악하고 수정하세요
3. 수동으로 실행: python3 ~/cafe24_automation/main.py"

    # HTML 메일(Gmail SMTP)로 발송, 실패 시에만 기존 텍스트 메일로 폴백
    if ! /usr/bin/python3 -m utils.send_failure_mail "$LOG_FILE" "$TIMESTAMP" "$EXIT_CODE" >> "$LOG_FILE" 2>&1; then
        echo "$EMAIL_BODY" | mail -s "$EMAIL_SUBJECT" "$RECIPIENT_EMAIL"
    fi
fi
