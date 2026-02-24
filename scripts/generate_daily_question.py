#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))

FRONTEND_INTERVIEW_TOPICS = [
    {
        "category": "React Architecture",
        "subject": "상태 관리 경계",
        "scenario": "검색/필터/정렬이 동시에 바뀌는 대시보드",
        "tradeoff": "지역 상태, 전역 상태, 서버 상태를 어떻게 분리할지",
    },
    {
        "category": "Rendering Performance",
        "subject": "렌더링 병목 진단",
        "scenario": "스크롤 중 카드 리스트가 버벅이는 모바일 웹",
        "tradeoff": "memoization, virtualization, 계산 캐싱의 적용 기준",
    },
    {
        "category": "Browser Internals",
        "subject": "Reflow/Repaint/Composite 최적화",
        "scenario": "실시간 애니메이션이 많은 랜딩 페이지",
        "tradeoff": "레이아웃 변경 최소화와 시각 품질의 균형",
    },
    {
        "category": "TypeScript",
        "subject": "타입 설계 전략",
        "scenario": "빠르게 변하는 백엔드 응답 스키마",
        "tradeoff": "유연성과 타입 안정성 사이의 의사결정",
    },
    {
        "category": "Data Fetching",
        "subject": "캐싱/동기화 정책",
        "scenario": "동일 데이터가 여러 화면에서 동시에 수정되는 서비스",
        "tradeoff": "낙관적 업데이트, 재검증, 롤백 전략",
    },
    {
        "category": "SSR/CSR Strategy",
        "subject": "렌더링 전략 선택",
        "scenario": "SEO와 실시간성이 모두 중요한 커머스 페이지",
        "tradeoff": "초기 로딩 속도와 상호작용 성능 간의 균형",
    },
    {
        "category": "Testing",
        "subject": "테스트 피라미드 설계",
        "scenario": "릴리즈 주기가 매우 짧은 제품 팀",
        "tradeoff": "신뢰도와 유지보수 비용의 균형",
    },
    {
        "category": "Web Security",
        "subject": "브라우저 보안 대응",
        "scenario": "사용자 생성 HTML을 렌더링하는 기능",
        "tradeoff": "보안 강도와 개발 생산성 간의 균형",
    },
    {
        "category": "Accessibility",
        "subject": "키보드/스크린리더 접근성",
        "scenario": "커스텀 컴포넌트 기반 디자인 시스템",
        "tradeoff": "디자인 자유도와 접근성 표준 준수",
    },
    {
        "category": "Bundling",
        "subject": "번들 최적화",
        "scenario": "초기 진입 페이지 번들 크기가 큰 SaaS",
        "tradeoff": "개발 편의성과 런타임 성능의 균형",
    },
]

CS_INTERVIEW_TOPICS = [
    {
        "category": "Data Structures",
        "subject": "배열 vs 연결 리스트 선택",
        "scenario": "잦은 삽입/삭제와 랜덤 접근이 공존하는 UI 상태 저장",
        "tradeoff": "시간복잡도, 메모리 오버헤드, 구현 복잡도의 균형",
    },
    {
        "category": "Algorithms",
        "subject": "정렬/탐색 전략",
        "scenario": "대량 목록 필터링과 정렬이 반복되는 클라이언트 화면",
        "tradeoff": "정확도, 응답속도, CPU 사용량의 균형",
    },
    {
        "category": "Complexity",
        "subject": "시간복잡도 최적화",
        "scenario": "렌더링 전 데이터 가공 단계가 길어지는 대시보드",
        "tradeoff": "사전 계산, 캐시, 메모리 사용량 간의 균형",
    },
    {
        "category": "Network",
        "subject": "TCP/HTTP 동작 이해",
        "scenario": "API 응답 지연으로 초기 화면 표시가 느린 서비스",
        "tradeoff": "요청 병렬화, 커넥션 재사용, 캐시 정책의 균형",
    },
    {
        "category": "Concurrency",
        "subject": "이벤트 루프/비동기 처리",
        "scenario": "사용자 입력, 애니메이션, 데이터 요청이 동시에 발생",
        "tradeoff": "응답성 유지와 작업 순서 보장의 균형",
    },
    {
        "category": "Caching",
        "subject": "캐시 일관성",
        "scenario": "여러 탭에서 동일 리소스를 갱신하는 웹앱",
        "tradeoff": "최신성, 성능, 구현 복잡도 간의 균형",
    },
    {
        "category": "Database Basics",
        "subject": "인덱스와 조회 패턴",
        "scenario": "검색 API 속도가 화면 UX를 좌우하는 서비스",
        "tradeoff": "쓰기 성능 저하와 읽기 성능 향상의 균형",
    },
    {
        "category": "System Design",
        "subject": "확장성/장애 대응",
        "scenario": "트래픽 급증 시 프론트-백엔드 경계에서 장애 전파",
        "tradeoff": "복잡도 증가와 안정성 확보의 균형",
    },
]

QUESTION_TEMPLATES = [
    "`{scenario}` 상황에서 `{subject}`를 어떻게 설계하면 좋을까요? `{tradeoff}` 기준으로 설명해 주세요.",
    "`{scenario}`에서 `{subject}`를 개선하려면 어떤 순서로 접근하시겠어요?",
    "`{scenario}` 기능을 구현할 때 `{subject}` 관점에서 어떤 선택을 하시겠어요?",
]

FOLLOW_UP_TEMPLATES = [
    "가장 먼저 점검할 지표 2가지는 무엇인가요?",
    "팀에서 공통 규칙으로 정하고 싶은 기준 1가지는 무엇인가요?",
    "이 선택을 확인하기 위한 테스트 방법은 어떻게 가져가면 좋을까요?",
    "초기 구현에서 꼭 챙길 최소 기준은 무엇인가요?",
]

REFERENCE_HINT_KEYWORDS = [
    "react",
    "typescript",
    "렌더링",
    "성능",
    "캐싱",
    "상태",
    "접근성",
    "번들",
    "테스트",
    "ssr",
    "csr",
    "graphql",
]


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_question(html_text: str) -> str:
    patterns = [
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']',
        r"<title[^>]*>(.*?)</title>",
        r"<h1[^>]*>(.*?)</h1>",
        r'"question"\s*:\s*"([^"]+)"',
        r'"text"\s*:\s*"([^"]+\?)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        candidate = clean_text(match.group(1))
        if len(candidate) < 8:
            continue
        candidate = re.split(r"\s+[|·-]\s+", candidate, maxsplit=1)[0].strip()
        return candidate
    return ""


def fetch_source_question(source_url: str, cookie: str = "") -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        )
    }
    if cookie:
        headers["Cookie"] = cookie

    request = Request(source_url, headers=headers)
    with urlopen(request, timeout=20) as response:
        html_text = response.read().decode("utf-8", errors="replace")
    question = extract_question(html_text)
    return question


def stable_seed(date_key: str, reference_question: str) -> int:
    seed_source = f"{date_key}|{reference_question}".encode("utf-8")
    return int(hashlib.sha256(seed_source).hexdigest(), 16)


def infer_reference_hint(reference_question: str) -> str:
    if not reference_question:
        return "일반 프론트엔드 핵심 역량"
    lowered = reference_question.lower()
    matched = [kw for kw in REFERENCE_HINT_KEYWORDS if kw in lowered]
    if not matched:
        return "일반 프론트엔드 핵심 역량"
    return ", ".join(matched[:3])


def pick_track(seed: int) -> str:
    # CS 70%, Frontend(실무) 30% 비율로 섞기
    return "cs" if (seed % 10) < 7 else "frontend"


def build_dynamic_question(date_key: str, reference_question: str) -> tuple[str, list[str], str, str]:
    seed = stable_seed(date_key=date_key, reference_question=reference_question)
    track = pick_track(seed)
    topic_pool = CS_INTERVIEW_TOPICS if track == "cs" else FRONTEND_INTERVIEW_TOPICS
    topic = topic_pool[seed % len(topic_pool)]
    template = QUESTION_TEMPLATES[(seed // 7) % len(QUESTION_TEMPLATES)]
    follow_up_start = (seed // 11) % len(FOLLOW_UP_TEMPLATES)

    main_question = template.format(
        scenario=topic["scenario"],
        subject=topic["subject"],
        tradeoff=topic["tradeoff"],
    )
    follow_ups = [
        FOLLOW_UP_TEMPLATES[follow_up_start % len(FOLLOW_UP_TEMPLATES)],
        FOLLOW_UP_TEMPLATES[(follow_up_start + 2) % len(FOLLOW_UP_TEMPLATES)],
    ]
    category = topic["category"]
    return main_question, follow_ups, category, track


def extract_gemini_text(response_payload: dict) -> str:
    candidates = response_payload.get("candidates", [])
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content", {})
        if not isinstance(content, dict):
            continue
        parts = content.get("parts", [])
        for part in parts:
            if not isinstance(part, dict):
                continue
            value = part.get("text")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def parse_ai_json(text: str) -> dict:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("AI output does not include JSON object")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("AI JSON is not an object")
    return parsed


def normalize_gemini_model(model: str) -> str:
    model = model.strip()
    if model.startswith("models/"):
        return model.split("/", 1)[1]
    return model


def generate_ai_question(
    api_key: str,
    model: str,
    date_key: str,
    track: str,
    topic: dict,
    reference_question: str,
    base_url: str = "https://generativelanguage.googleapis.com/v1beta",
) -> tuple[str, list[str], str, str]:
    track_label = "CS" if track == "cs" else "Frontend"
    reference_line = reference_question if reference_question else "N/A"
    prompt = (
        "다음 규칙으로 한국어 기술 질문을 만들어 주세요.\n"
        f"- 날짜: {date_key}\n"
        f"- 트랙: {track_label}\n"
        f"- 카테고리 힌트: {topic['category']}\n"
        f"- 시나리오 힌트: {topic['scenario']}\n"
        f"- 주제 힌트: {topic['subject']}\n"
        f"- 트레이드오프 힌트: {topic['tradeoff']}\n"
        f"- 참고 질문: {reference_line}\n"
        "- 질문 톤은 가볍고 짧게 작성해 주세요.\n"
        "- 면접/네카라쿠배/대규모 트래픽 같은 표현은 쓰지 마세요.\n"
        "- follow-up 2개는 짧고 실용적으로 작성해 주세요.\n"
        "- 반드시 JSON만 반환하세요. 코드블록 금지.\n"
        '형식: {"question":"...","follow_up_1":"...","follow_up_2":"...","category":"..."}'
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": "당신은 프론트엔드 데일리 질문 생성기입니다."}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 600,
            "responseMimeType": "application/json",
        },
    }
    requested_model = normalize_gemini_model(model)
    candidates: list[str] = [
        requested_model,
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
    ]
    unique_candidates: list[str] = []
    for name in candidates:
        n = normalize_gemini_model(name)
        if n and n not in unique_candidates:
            unique_candidates.append(n)

    last_error = ""
    for candidate_model in unique_candidates:
        endpoint = f"{base_url}/models/{candidate_model}:generateContent?key={quote_plus(api_key)}"
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except HTTPError as err:
            error_body = ""
            try:
                error_body = err.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = ""
            last_error = f"Gemini API HTTP {err.code}: {error_body or err.reason}"
            if err.code == 404:
                continue
            raise ValueError(last_error) from err

        raw_text = extract_gemini_text(response_data)
        parsed = parse_ai_json(raw_text)

        question = sanitize_inline(str(parsed.get("question", "")))
        follow_up_1 = sanitize_inline(str(parsed.get("follow_up_1", "")))
        follow_up_2 = sanitize_inline(str(parsed.get("follow_up_2", "")))
        category = sanitize_inline(str(parsed.get("category", topic["category"])))

        if not question or not follow_up_1 or not follow_up_2:
            raise ValueError("AI output is missing required fields")
        return question, [follow_up_1, follow_up_2], category, candidate_model

    raise ValueError(
        "No usable Gemini model for generateContent. "
        f"tried={', '.join(unique_candidates)}; last_error={last_error}"
    )


def sanitize_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def build_pr_title(question: str) -> str:
    plain = sanitize_inline(question).replace("`", "")
    prefix = "chore: daily tech question - "
    max_len = 180
    allowed = max_len - len(prefix)
    if len(plain) > allowed:
        plain = plain[: allowed - 3].rstrip() + "..."
    return f"{prefix}{plain}"


def write_markdown(
    output_dir: Path,
    date_key: str,
    question: str,
    follow_ups: list[str],
    category: str,
    track: str,
    source_url: str,
    source_mode: str,
    reference_question: str,
    reference_hint: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{date_key}.md"
    source_line = source_url if source_mode == "reference+generated" else "Generated from local interview topic bank"
    reference_line = reference_question if reference_question else "참고 질문을 가져오지 못해 로컬 규칙으로 생성"
    track_label = "CS" if track == "cs" else "Frontend"
    content = (
        f"# Frontend Daily Question ({date_key})\n\n"
        "## Track\n"
        f"- {track_label}\n\n"
        "## Category\n"
        f"- {category}\n\n"
        "## Question\n"
        f"{question}\n\n"
        "## Follow-up\n"
        f"1. {follow_ups[0]}\n"
        f"2. {follow_ups[1]}\n\n"
        "## Notes\n"
        "- 답변은 PR 코멘트로 남기거나, 이 문서에 이어서 작성하세요.\n"
        "- 팀 기준/경험을 근거로 답변하면 좋습니다.\n\n"
        "## Reference Hint\n"
        f"- {reference_hint}\n\n"
        "## Reference Question\n"
        f"- {reference_line}\n\n"
        "## Source\n"
        f"- {source_line}\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def set_github_output_extended(
    file_path: Path,
    question: str,
    source_mode: str,
    track: str,
    category: str,
    follow_ups: list[str],
    reference_hint: str,
    reference_question: str,
) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        return

    track_label = "CS" if track == "cs" else "Frontend"
    pr_title = build_pr_title(question)

    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"file_path={file_path.as_posix()}\n")
        f.write(f"source_mode={sanitize_inline(source_mode)}\n")
        f.write(f"question={sanitize_inline(question)}\n")
        f.write(f"track={track_label}\n")
        f.write(f"category={sanitize_inline(category)}\n")
        f.write(f"follow_up_1={sanitize_inline(follow_ups[0])}\n")
        f.write(f"follow_up_2={sanitize_inline(follow_ups[1])}\n")
        f.write(f"reference_hint={sanitize_inline(reference_hint)}\n")
        f.write(f"reference_question={sanitize_inline(reference_question) if reference_question else 'N/A'}\n")
        f.write(f"pr_title={pr_title}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-url",
        default=os.environ.get(
            "QUESTION_SOURCE_URL",
            "https://www.maeil-mail.kr/question/mine/gentlemonster77@likelion.org",
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="daily-frontend-questions",
    )
    parser.add_argument(
        "--tz",
        default="KST",
        choices=["KST", "UTC"],
    )
    parser.add_argument(
        "--generation-mode",
        default=os.environ.get("QUESTION_GENERATION_MODE", "always"),
        choices=["auto", "always", "never"],
    )
    args = parser.parse_args()

    now = datetime.now(KST if args.tz == "KST" else timezone.utc)
    date_key = now.date().isoformat()

    cookie = os.environ.get("QUESTION_SOURCE_COOKIE", "")
    reference_question = ""
    source_mode = "generated"

    if args.source_url:
        try:
            reference_question = fetch_source_question(args.source_url, cookie)
        except (HTTPError, URLError, TimeoutError, ValueError):
            reference_question = ""

    seed = stable_seed(date_key=date_key, reference_question=reference_question)
    track = pick_track(seed)
    topic_pool = CS_INTERVIEW_TOPICS if track == "cs" else FRONTEND_INTERVIEW_TOPICS
    topic = topic_pool[seed % len(topic_pool)]

    gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    gemini_base_url = os.environ.get(
        "GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
    ).strip()
    use_ai = args.generation_mode == "always" or (
        args.generation_mode == "auto" and bool(gemini_api_key)
    )

    if use_ai and not gemini_api_key and args.generation_mode == "always":
        raise RuntimeError("QUESTION_GENERATION_MODE=always requires GEMINI_API_KEY")

    if use_ai and gemini_api_key:
        used_ai_model = ""
        try:
            question, follow_ups, category, used_ai_model = generate_ai_question(
                api_key=gemini_api_key,
                model=gemini_model,
                date_key=date_key,
                track=track,
                topic=topic,
                reference_question=reference_question,
                base_url=gemini_base_url,
            )
            source_mode = "ai+reference" if reference_question else "ai"
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as err:
            if args.generation_mode == "always":
                raise RuntimeError(f"AI generation failed in always mode: {err}") from err
            question, follow_ups, category, track = build_dynamic_question(
                date_key=date_key,
                reference_question=reference_question,
            )
            source_mode = "reference+generated" if reference_question else "generated"
    else:
        question, follow_ups, category, track = build_dynamic_question(
            date_key=date_key,
            reference_question=reference_question,
        )
        source_mode = "reference+generated" if reference_question else "generated"

    reference_hint = infer_reference_hint(reference_question)

    file_path = write_markdown(
        output_dir=Path(args.output_dir),
        date_key=date_key,
        question=question,
        follow_ups=follow_ups,
        category=category,
        track=track,
        source_url=args.source_url,
        source_mode=source_mode,
        reference_question=reference_question,
        reference_hint=reference_hint,
    )
    set_github_output_extended(
        file_path=file_path,
        question=question,
        source_mode=source_mode,
        track=track,
        category=category,
        follow_ups=follow_ups,
        reference_hint=reference_hint,
        reference_question=reference_question,
    )

    print(f"Generated: {file_path}")
    print(f"Source mode: {source_mode}")
    if source_mode.startswith("ai"):
        print(f"AI model: {used_ai_model}")
    print(f"Track: {track}")
    print(f"Category: {category}")
    print(f"Question: {question}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
