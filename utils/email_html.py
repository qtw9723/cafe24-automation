"""
알림 메일 HTML 렌더러 (다크 테마 고정).

메일 클라이언트(Outlook/Gmail)는 <style> 지원이 들쭉날쭉하므로 전부 인라인 스타일 + table 레이아웃.
color-scheme 메타로 '이미 다크'임을 알려 클라이언트가 색을 뒤집지 않게 한다.
plain-text 본문은 email_notifier가 함께 보낸다(multipart/alternative) — 이 모듈은 HTML만 만든다.
"""
import re
from html import escape

# ---- 팔레트 ----
BG = "#05070a"
CARD = "#12161c"
CARD_2 = "#0b0e12"
BORDER = "#2b323c"
TEXT = "#f0f3f6"
MUTED = "#a3acb7"
DIM = "#7d8590"
GREEN = "#3fb950"
RED = "#f85149"
AMBER = "#d29922"
BLUE = "#58a6ff"
MONO = "SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic','Segoe UI',sans-serif"

STATUS = {
    "ok":   (GREEN, "성공"),
    "fail": (RED, "실패"),
    "warn": (AMBER, "경고"),
    "down": (RED, "서버 응답 없음"),
}

STEP_NAMES = {
    1: "Shop 탭 · 로그 수집",
    2: "log stats · 로그 합계",
    3: "Dashboard · 수치 검증",
    4: "daily check · 메모 저장",
    5: "체크리스트 · 8개 항목",
}


def tone_of(value):
    """값 텍스트로 색을 고른다."""
    v = str(value)
    if any(k in v for k in ("실패", "불일치", "증가", "에러", "의심", "없음")):
        return RED if "실패" in v or "불일치" in v or "증가" in v else AMBER
    if any(k in v for k in ("성공", "일치", "동일", "감소", "변화 없음")):
        return GREEN
    if "미확인" in v:
        return DIM
    return TEXT


def clean_label(label):
    """'✅ 메모 저장 여부' → '메모 저장 여부' (이모지 접두어 제거)."""
    return re.sub(r"^[^\w가-힣]+", "", str(label)).strip()


# ---- 블록 ----
def section(title, inner):
    return f"""
<tr><td style="padding:0 24px 20px 24px;">
  <div style="font:600 12px {SANS};color:{MUTED};letter-spacing:.06em;text-transform:uppercase;margin:0 0 8px 2px;">{escape(title)}</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{CARD}" style="background:{CARD};background-color:{CARD};border:1px solid {BORDER};border-radius:10px;border-collapse:separate;">
    {inner}
  </table>
</td></tr>"""


def kv_rows(pairs):
    """[(label, value)] → 2열 표. 값 색은 tone_of로 자동."""
    rows = []
    last = len(pairs) - 1
    for i, (label, value) in enumerate(pairs):
        line = "" if i == last else f"border-bottom:1px solid {BORDER};"
        rows.append(f"""
    <tr>
      <td style="padding:11px 16px;{line}font:14px {SANS};color:{MUTED};">{escape(clean_label(label))}</td>
      <td align="right" style="padding:11px 16px;{line}font:600 14px {SANS};color:{tone_of(value)};">{escape(str(value))}</td>
    </tr>""")
    return "".join(rows)


def metric_tiles(tiles):
    """[(label, big_value, tone_color)] → 가로 타일(최대 3개)."""
    cells = []
    for label, value, color in tiles:
        cells.append(f"""
      <td width="{100 // max(len(tiles), 1)}%" style="padding:14px 16px;text-align:left;vertical-align:top;">
        <div style="font:12px {SANS};color:{MUTED};margin-bottom:4px;">{escape(label)}</div>
        <div style="font:700 22px {SANS};color:{color};">{escape(str(value))}</div>
      </td>""")
    return f"<tr>{''.join(cells)}</tr>"


def steps_rows(states):
    """states: {1:'ok'|'fail'|'skip'} → 단계 진행표."""
    marks = {"ok": (GREEN, "●", "완료"), "fail": (RED, "●", "실패"), "skip": (DIM, "○", "미실행")}
    rows = []
    for n in sorted(STEP_NAMES):
        color, dot, word = marks[states.get(n, "skip")]
        line = "" if n == max(STEP_NAMES) else f"border-bottom:1px solid {BORDER};"
        rows.append(f"""
    <tr>
      <td width="28" style="padding:10px 0 10px 16px;{line}font:14px {SANS};color:{color};">{dot}</td>
      <td style="padding:10px 8px;{line}font:14px {SANS};color:{TEXT};"><span style="color:{DIM};">STEP {n}</span>&nbsp;&nbsp;{escape(STEP_NAMES[n])}</td>
      <td align="right" style="padding:10px 16px;{line}font:600 13px {SANS};color:{color};">{word}</td>
    </tr>""")
    return "".join(rows)


def callout(title, body, color=RED):
    return f"""
<tr><td style="padding:0 24px 20px 24px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{CARD}" style="background:{CARD};background-color:{CARD};border:1px solid {BORDER};border-left:4px solid {color};border-radius:10px;border-collapse:separate;">
    <tr><td style="padding:14px 16px;">
      <div style="font:600 14px {SANS};color:{color};margin-bottom:6px;">{escape(title)}</div>
      <div style="font:13px/1.6 {MONO};color:{TEXT};white-space:pre-wrap;word-break:break-word;">{escape(body)}</div>
    </td></tr>
  </table>
</td></tr>"""


def text_rows(text, mono=False):
    font = f"13px/1.65 {MONO}" if mono else f"14px/1.65 {SANS}"
    return f"""<tr><td style="padding:14px 16px;font:{font};color:{TEXT};white-space:pre-wrap;word-break:break-word;">{escape(text)}</td></tr>"""


def ordered_rows(items):
    lis = "".join(
        f'<div style="margin:0 0 6px 0;"><span style="color:{BLUE};font-weight:600;">{i}.</span>&nbsp; {escape(t)}</div>'
        for i, t in enumerate(items, 1)
    )
    return f"""<tr><td style="padding:14px 16px 8px 16px;font:14px/1.6 {SANS};color:{TEXT};">{lis}</td></tr>"""


_LOG_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} )?(\d{2}:\d{2}:\d{2})\]\s*(.*)$")


def log_rows(lines):
    """로그 줄을 레벨별로 색칠. 시각은 HH:MM:SS만, 구분선(=====)은 생략."""
    out = []
    for raw in lines:
        line = raw.rstrip()
        if not line or set(line.strip()) <= {"=", "-"} or line.strip().endswith("=" * 10):
            continue
        m = _LOG_RE.match(line)
        if m:
            ts, msg = m.group(2), m.group(3)
        else:
            ts, msg = "", line
        if "[ERROR]" in msg or "Traceback" in msg:
            color = RED
        elif "[SUCCESS]" in msg:
            color = GREEN
        elif "[WARN" in msg:
            color = AMBER
        elif msg.startswith("  ") or msg.startswith("…"):
            color = DIM
        else:
            color = TEXT
        msg = re.sub(r"\s*\[(INFO|SUCCESS|ERROR)\]\s*(\[INFO\])?", lambda k: f" [{k.group(1)}] " if k.group(1) != "INFO" else " ", msg)
        msg = re.sub(r"\(추출된 숫자: \[[^\]]*\]\)", "(숫자 목록 생략)", msg)
        msg = msg.split("; For documentation")[0]
        out.append(
            f'<div style="white-space:pre-wrap;word-break:break-word;color:{color};">'
            f'<span style="color:{DIM};">{escape(ts)}</span>{"&nbsp;&nbsp;" if ts else ""}{escape(msg.strip())}</div>'
        )
    return f"""<tr><td bgcolor="{CARD_2}" style="padding:12px 14px;background:{CARD_2};background-color:{CARD_2};border-radius:10px;font:12px/1.7 {MONO};">{''.join(out)}</td></tr>"""


def _expand_font(m):
    """font: 단축 표기 → 개별 속성 (Outlook이 단축 표기를 지워버림)."""
    v = m.group(1).strip()
    fm = re.match(r"^(?:(\d{3})\s+)?(\d+px)(?:/([\d.]+))?\s+(.+)$", v)
    if not fm:
        return m.group(0)
    w, size, lh, fam = fm.groups()
    out = f"font-family:{fam};font-size:{size};"
    if w:
        out += f"font-weight:{w};"
    if lh:
        out += f"line-height:{lh};"
    return out


def _outlook_proof(html):
    """Outlook 다크모드 색 재계산 회피.
    Outlook은 background-color 를 자체 회색으로 바꾸지만 background-image 는 건드리지 않는다
    → 같은 색 linear-gradient 를 겹쳐 칠해 원래 색을 유지한다."""
    html = re.sub(r"font:([^;\"]+);", _expand_font, html)
    # Outlook(Mac/새 Outlook) 다크모드는 배경 관련 속성(background-color·bgcolor·background-image)을
    # 보낸 값과 무관하게 고정 회색 rgb(80,81,83)으로 덮어쓴다(2026-11-05 실측, 흰색·검정 모두 동일).
    # 글자·테두리 색은 건드리지 않음 → 안쪽 box-shadow 로 배경을 한 겹 더 칠한다.
    html = re.sub(r"background:(#[0-9a-fA-F]{6});(?:background-color:\1;)?",
                  r"background-color:\1;box-shadow:inset 0 0 0 9999px \1;", html)
    # background-color 만 쓴 칸(바깥 td 등)에도 그림자 — 빠지면 그 칸 여백이 회색 테두리로 남는다
    html = re.sub(r"background-color:(#[0-9a-fA-F]{6});(?!box-shadow)",
                  r"background-color:\1;box-shadow:inset 0 0 0 9999px \1;", html)
    # body 는 바깥쪽으로도 그림자를 퍼뜨려 Outlook 읽기 창 자체 여백(베젤)까지 덮는다
    html = re.sub(r'(<body[^>]*?box-shadow:)inset 0 0 0 9999px (#[0-9a-fA-F]{6});',
                  r"\1inset 0 0 0 9999px \2,0 0 0 9999px \2;", html, count=1)
    return html


def page(title, status, subtitle, body_sections, footer_paths=()):
    return _outlook_proof(_page(title, status, subtitle, body_sections, footer_paths))


def _page(title, status, subtitle, body_sections, footer_paths=()):
    color, word = STATUS[status]
    paths = "".join(f'<div style="font:12px {MONO};color:{MUTED};">{escape(p)}</div>' for p in footer_paths)
    return f"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="supported-color-schemes" content="dark">
<title>{escape(title)}</title>
</head>
<body bgcolor="{BG}" style="margin:0;padding:0;background:{BG};background-color:{BG};color:{TEXT};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{BG}" style="background:{BG};background-color:{BG};">
<tr><td align="center" bgcolor="{BG}" style="padding:24px 8px;background-color:{BG};">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" bgcolor="{BG}" style="max-width:640px;width:100%;background:{BG};background-color:{BG};">
  <tr><td style="padding:8px 24px 22px 24px;">
    <div style="display:inline-block;padding:4px 10px;border-radius:999px;background:{CARD};border:1px solid {color};font:600 12px {SANS};color:{color};">● {escape(word)}</div>
    <div style="font:700 22px/1.35 {SANS};color:{TEXT};margin:12px 0 4px 0;">{escape(title)}</div>
    <div style="font:13px {SANS};color:{MUTED};">{escape(subtitle)}</div>
  </td></tr>
  {''.join(body_sections)}
  <tr><td style="padding:4px 24px 8px 24px;border-top:1px solid {BORDER};">
    <div style="font:12px {SANS};color:{DIM};margin:14px 0 6px 0;">로그 위치</div>
    {paths}
    <div style="font:11px {SANS};color:{DIM};margin-top:14px;">Cafe24 백오피스 일일 자동화 · 자동 발송 메일</div>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""


# ---- 실행 로그 파싱 (실패 메일용) ----
def collapse_stacktrace(lines):
    """chromedriver/파이썬 스택 덤프를 한 줄 요약으로 접는다."""
    out, skipped = [], 0
    for line in lines:
        s = line.strip()
        if re.match(r"^\d+\s+(chromedriver|dyld|libsystem|Google Chrome)", s) or s == "Stacktrace:":
            skipped += 1
            continue
        if skipped:
            out.append(f"  … 스택 트레이스 {skipped}줄 생략")
            skipped = 0
        out.append(line)
    if skipped:
        out.append(f"  … 스택 트레이스 {skipped}줄 생략")
    return out


KNOWN_ERRORS = [
    ("invalid session id", "브라우저(크롬) 세션이 실행 도중 끊겼습니다. 대부분 일시적이라 재실행으로 해결됩니다."),
    ("Read timed out", "chromedriver가 응답하지 않았습니다(브라우저 멈춤). 일시적인 경우가 많습니다."),
    ("no such window", "자동화 크롬 창이 닫혔습니다. 실행 중 창을 닫지 않았는지 확인하세요."),
    ("Connection refused", "백오피스 서버 또는 chromedriver에 연결할 수 없습니다."),
]


def diagnose(msg):
    for key, hint in KNOWN_ERRORS:
        if key.lower() in (msg or "").lower():
            return hint
    return ""


def short_error(msg):
    """'Message: invalid session id; For documentation ...' → 핵심만."""
    msg = msg.split("; For documentation")[0]
    msg = msg.split("\nStacktrace")[0]
    return msg.strip()


def parse_run_log(text):
    # 자동 재시도가 있으면 로그에 여러 회차가 섞인다 → 마지막 회차만 판정, 앞 회차 에러는 따로 요약
    marker = "자동화 시작"
    starts = [i for i, l in enumerate(text.splitlines()) if marker in l and "[STEP0]" in l]
    all_lines = text.splitlines()
    earlier = []
    if len(starts) > 1:
        for l in all_lines[starts[0]:starts[-1]]:
            m = re.search(r"\[(STEP\d)\]\s*\[([A-Z_0-9]+)\]\s*\[ERROR\]\s*(.*)", l)
            if m and not any(e[0] == m.group(1) for e in earlier):
                earlier.append((m.group(1), m.group(2), short_error(m.group(3))))
        text = "\n".join(all_lines[starts[-1]:])
    lines = text.splitlines()
    # 최종 리포트
    report, in_report = [], False
    for line in lines:
        if "최종 결과 리포트" in line:
            in_report = True
            continue
        if in_report:
            s = line.strip()
            if s.startswith("최종 결과가") or "실패했습니다" in s or "성공적으로" in s:
                break
            if ":" in s and not s.startswith("="):
                k, v = s.split(":", 1)
                report.append((k.strip(), v.strip()))
    # 단계 상태
    states = {}
    for n in STEP_NAMES:
        if re.search(rf"\[(STEP{n})\].*\[ERROR\]", text):
            states[n] = "fail"
        elif re.search(rf"\] \[{n}\] \[[A-Z_]+\] \[SUCCESS\]", text):
            states[n] = "ok"
        else:
            states[n] = "skip"
    # 실패 단계 이후는 미실행 처리, 실패 단계 확정
    failed = [n for n, s in states.items() if s == "fail"]
    if failed:
        for n in STEP_NAMES:
            if n > min(failed):
                states[n] = "skip"
    # 첫 에러(스택 제외)
    first_err = None
    for i, line in enumerate(lines):
        if "[ERROR]" in line:
            m = re.search(r"\[(STEP\d|MAIN|INIT|EMAIL)\]\s*\[([A-Z_0-9]+)\]\s*\[ERROR\]\s*(.*)", line)
            if m:
                first_err = (m.group(1), m.group(2), short_error(m.group(3)))
            else:
                first_err = ("", "", short_error(line))
            break
    return {"report": report, "states": states, "first_error": first_err, "lines": lines,
            "attempts": max(len(starts), 1), "earlier_errors": earlier}
