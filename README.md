# Daily Frontend Question PR Bot

매일 프론트엔드 기술 질문을 파일로 생성하고, 해당 변경을 PR로 올리는 GitHub Actions 설정입니다.
질문은 네카라쿠배 면접 스타일(대규모 트래픽/실무 트레이드오프 중심)로 동적 생성됩니다.
프론트엔드 실무 질문과 CS 질문이 함께 섞여 나옵니다.

## What it does

- 매일 `09:05 KST`(=`00:05 UTC`)에 실행됩니다.
- `daily-frontend-questions/YYYY-MM-DD.md` 파일을 생성합니다.
- 변경사항이 있으면 자동으로 브랜치/커밋/PR을 만듭니다.
- `QUESTION_SOURCE_URL`의 질문은 "참고 질문"으로만 사용하고, 최종 질문은 동적으로 생성합니다.
- 생성 질문은 `CS`와 `Frontend(실무)` 트랙이 혼합됩니다(기본 비율: CS 70% / 실무 30%).

## Workflow file

- `.github/workflows/daily-frontend-question-pr.yml`

## Optional repository settings

1. `Settings > Secrets and variables > Actions > Variables`
- `QUESTION_SOURCE_URL`
  - 질문을 가져올 URL
  - 미설정 시 기본값:
    - `https://www.maeil-mail.kr/question/mine/gentlemonster77@likelion.org`

2. `Settings > Secrets and variables > Actions > Secrets`
- `QUESTION_SOURCE_COOKIE` (선택)
  - 로그인/인증이 필요한 페이지에서 질문 추출 시 쿠키 문자열 사용

## Manual run

- GitHub 탭에서 `Actions > Daily Frontend Question PR > Run workflow`로 수동 실행 가능

## Notes

- 소스 URL 파싱 실패 시에도 질문 생성은 계속되며, 로컬 면접 주제 규칙으로 동적 생성됩니다.
- 질문 생성 스크립트:
  - `scripts/generate_daily_question.py`
