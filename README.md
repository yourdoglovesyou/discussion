# Daily Frontend Question PR Bot

매일 프론트엔드 기술 질문을 파일로 생성하고, 해당 변경을 PR로 올리는 GitHub Actions 설정입니다.
질문은 가볍게 답할 수 있는 기술 질문 형태로 동적 생성됩니다.
프론트엔드 실무 질문과 CS 질문이 함께 섞여 나옵니다.

## What it does

- 매일 `09:05 KST`(=`00:05 UTC`)에 실행됩니다.
- `daily-frontend-questions/YYYY-MM-DD.md` 파일을 생성합니다.
- 변경사항이 있으면 자동으로 브랜치/커밋/PR을 만듭니다.
- `QUESTION_SOURCE_URL`의 질문은 "참고 질문"으로만 사용하고, 최종 질문은 동적으로 생성합니다.
- 생성 질문은 `CS`와 `Frontend(실무)` 트랙이 혼합됩니다(기본 비율: CS 70% / 실무 30%).
- PR 제목은 당일 기술 질문으로 생성되고, PR 본문에는 트랙/카테고리/후속 질문 등 세부 정보가 포함됩니다.
- `OPENAI_API_KEY`가 있으면 AI로 질문을 생성하고, 없거나 실패하면 로컬 규칙으로 fallback 됩니다.

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
  - 기본값: `auto`
- `OPENAI_MODEL` (선택)
  - 기본값: `gpt-4.1-mini`

2. `Settings > Secrets and variables > Actions > Secrets`
- `QUESTION_SOURCE_COOKIE` (선택)
  - 로그인/인증이 필요한 페이지에서 질문 추출 시 쿠키 문자열 사용
- `OPENAI_API_KEY` (선택)
  - 설정 시 AI로 질문 생성

## Manual run

- GitHub 탭에서 `Actions > Daily Frontend Question PR > Run workflow`로 수동 실행 가능

## Notes

- 소스 URL 파싱 실패 시에도 질문 생성은 계속됩니다.
- AI 생성 실패 시 로컬 규칙 기반 질문으로 자동 fallback 됩니다.
- 질문 생성 스크립트:
  - `scripts/generate_daily_question.py`
