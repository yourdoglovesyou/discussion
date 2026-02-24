# Daily Frontend Question PR Bot

매일 프론트엔드 기술 질문을 파일로 생성하고, 해당 변경을 PR로 올리는 GitHub Actions 설정입니다.
질문은 프론트엔드 면접 기출 CS(기초 개념) 스타일로 동적 생성됩니다.
예: `event.target vs event.currentTarget`, `debounce vs throttle`, `var/let/const 차이`

## What it does

- 매일 `09:05 KST`(=`00:05 UTC`)에 실행됩니다.
- `daily-frontend-questions/YYYY-MM-DD.md` 파일을 생성합니다.
- 변경사항이 있으면 자동으로 브랜치/커밋/PR을 만듭니다.
- `QUESTION_SOURCE_URL`의 질문은 "참고 질문"으로만 사용하고, 최종 질문은 동적으로 생성합니다.
- 생성 질문은 프론트엔드 CS 중심이며, 개념 설명형 질문을 우선 생성합니다.
- PR 제목은 당일 기술 질문으로 생성되고, PR 본문에는 트랙/카테고리/후속 질문 등 세부 정보가 포함됩니다.
- 기본 동작은 AI 전용 생성입니다(`QUESTION_GENERATION_MODE=always`).
- `GEMINI_API_KEY`가 없거나 AI 생성이 실패하면 워크플로가 실패합니다.

## Workflow file

- `.github/workflows/daily-frontend-question-pr.yml`

## Optional repository settings

1. `Settings > Secrets and variables > Actions > Variables`
- `QUESTION_SOURCE_URL`
  - 질문을 가져올 URL
  - 미설정 시 기본값:
    - `https://www.maeil-mail.kr/question/mine/gentlemonster77@likelion.org?category=frontend`
- `QUESTION_GENERATION_MODE`
  - `auto` | `always` | `never`
  - 기본값: `always`
- `GEMINI_MODEL` (선택)
  - 기본값: `gemini-2.5-flash`
- `GEMINI_REQUEST_TIMEOUT_SEC` (선택)
  - 기본값: `60`
- `GEMINI_MAX_RETRIES` (선택)
  - 기본값: `7`

2. `Settings > Secrets and variables > Actions > Secrets`
- `QUESTION_SOURCE_COOKIE` (선택)
  - 로그인/인증이 필요한 페이지에서 질문 추출 시 쿠키 문자열 사용
- `GEMINI_API_KEY` (선택)
  - 설정 시 AI로 질문 생성

## Manual run

- GitHub 탭에서 `Actions > Daily Frontend Question PR > Run workflow`로 수동 실행 가능

## Notes

- 소스 URL 파싱 실패 시에도 질문 생성은 계속됩니다.
- `always` 모드에서는 AI 생성 실패 시 fallback 없이 실패합니다.
- 지정한 Gemini 모델이 404일 경우, 스크립트가 호환 모델 후보를 자동 재시도합니다.
- 계정에서 허용된 Gemini 모델을 `models.list`로 조회해, 사용 가능한 모델을 우선 선택합니다.
- `tts/embedding/image` 등 텍스트 질문 생성에 맞지 않는 모델은 자동 제외합니다.
- Gemini 응답이 JSON 형식이 아니거나 비어 있으면 동일 모델에서 재시도 후 다음 후보 모델로 넘어갑니다.
- 일시적 네트워크 타임아웃은 동일 모델에서 재시도합니다(`GEMINI_REQUEST_TIMEOUT_SEC`, `GEMINI_MAX_RETRIES`로 조정 가능).
- 질문 생성 스크립트:
  - `scripts/generate_daily_question.py`
