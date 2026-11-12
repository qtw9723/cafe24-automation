# OpenAI API 키 설정 가이드

API 키를 3가지 방법으로 설정할 수 있습니다.

## 📌 OpenAI API 키 얻기

1. [OpenAI 웹사이트](https://platform.openai.com) 방문
2. 계정 생성 후 로그인
3. "API keys" 메뉴에서 새 키 생성
4. 키 복사 (`sk-...` 형태)

## 방법 1️⃣: config.py에 직접 입력 (권장 - 간단함)

**파일**: `config.py`

```python
OPENAI_API_KEY = "sk-..."  # 여기에 API 키 입력
OPENAI_MODEL = "gpt-4o-mini"  # 또는 "gpt-3.5-turbo"
```

**장점**: 가장 간단함  
**단점**: 코드에 API 키가 노출됨

---

## 방법 2️⃣: 환경변수로 설정 (권장 - 보안)

### macOS/Linux 환경변수 설정

```bash
# 터미널에서 한 번만 실행 (현재 세션에만 적용)
export OPENAI_API_KEY="sk-ant-..."

# 영구 설정 (매번 적용)
echo 'export OPENAI_API_KEY="sk-ant-..."' >> ~/.zshrc
source ~/.zshrc
```

### 환경변수로 실행

```bash
# 방법 1: 환경변수 설정 후 실행
export OPENAI_API_KEY="sk-ant-..."
python3 main.py

# 방법 2: 한 줄에서 설정하며 실행
OPENAI_API_KEY="sk-ant-..." python3 main.py
```

**장점**: API 키가 코드에 노출되지 않음 (보안)  
**단점**: 매번 설정해야 함

---

## 방법 3️⃣: .env 파일로 설정 (권장 - 가장 안전)

### 1단계: .env 파일 생성

```bash
cd ~/cafe24_automation
cp .env.example .env
```

### 2단계: .env 파일 수정

**파일**: `.env`

```
OPENAI_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-opus-4-7
```

### 3단계: 실행

```bash
python3 main.py
```

스크립트는 자동으로 `.env` 파일을 읽습니다.

**장점**: API 키가 안전하게 보관됨, 자동 로드  
**단점**: .env 파일 관리 필요

---

## 방법 4️⃣: 커맨드 라인 인자로 설정

```bash
# 한 번만 실행할 때
python3 main.py --api-key sk-ant-...

# 모델도 변경하려면
python3 main.py --api-key sk-ant-... --model claude-sonnet-4-6
```

**장점**: 임시로 다른 API 키 사용 가능  
**단점**: 매번 입력해야 함

---

## 🔄 API 키 중간에 바꾸기

프로그램 실행 중 API 키를 바꾸려면 다음과 같이 하세요:

```python
from api.claude_handler import claude

# API 키 변경
claude.set_api_key("sk-ant-new-key-...")

# 모델도 변경 가능
claude.set_model("claude-sonnet-4-6")

# 대화 히스토리 초기화 (선택사항)
claude.reset_conversation()
```

---

## 우선순위

API 키는 다음 순서대로 설정됩니다:

1. **커맨드 라인 인자** (`--api-key`)
2. **환경변수** (`OPENAI_API_KEY`)
3. **.env 파일** 
4. **config.py**

예를 들어, `.env` 파일이 있으면 `config.py`의 설정은 무시됩니다.

---

## 🔐 보안 권장사항

✅ **해야 할 것**:
- `.env` 파일을 사용하세요
- API 키를 환경변수로 관리하세요
- `.env` 파일을 `.gitignore`에 추가하세요

❌ **하지 말아야 할 것**:
- API 키를 `config.py`에 직접 입력하지 마세요
- API 키를 GitHub에 커밋하지 마세요
- API 키를 다른 사람과 공유하지 마세요

---

## 크론 작업에서 API 키 설정

**파일**: `run_daily.sh`

```bash
#!/bin/bash
cd ~/cafe24_automation

# 방법 1: .env 파일에서 로드 (자동)
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# 방법 2: 직접 환경변수 설정
export OPENAI_API_KEY="sk-ant-..."

python3 main.py
```

---

## 📝 API 키 확인

API 키가 올바르게 설정되었는지 테스트하세요:

```bash
# 환경변수 확인
echo $OPENAI_API_KEY

# Python에서 확인
python3 -c "import os; print(os.environ.get('OPENAI_API_KEY', 'Not set'))"

# config.py 확인
python3 -c "import config; print(config.OPENAI_API_KEY)"
```

---

## 🆘 문제 해결

### "API 키가 설정되지 않았습니다" 에러

1. API 키가 올바른지 확인하세요
2. 스페이스가 없는지 확인하세요
3. 환경변수가 정확히 `OPENAI_API_KEY`인지 확인하세요

### API 호출 실패

1. API 키의 유효성 확인
2. API 사용 한도 확인
3. 네트워크 연결 확인

### 여러 API 키 중 어떤 것을 사용했는지 확인

로그 파일(`output/logs.txt`)을 확인하면 어떤 API 키가 사용되었는지 알 수 있습니다.
