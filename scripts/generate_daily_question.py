#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))

FRONTEND_INTERVIEW_TOPICS = [
    {
        "category": "React Basics",
        "subject": "key를 왜 써야 하는지와 잘못 썼을 때 문제",
        "scenario": "리스트를 렌더링하고 항목 순서가 자주 바뀌는 화면",
        "tradeoff": "index를 key로 쓰는 경우의 위험",
    },
    {
        "category": "React Hooks",
        "subject": "useEffect dependency array 동작 원리",
        "scenario": "API 호출과 상태 업데이트가 함께 있는 컴포넌트",
        "tradeoff": "의존성 누락/과다 지정으로 생기는 버그",
    },
    {
        "category": "React Forms",
        "subject": "controlled와 uncontrolled 컴포넌트 차이",
        "scenario": "입력 폼 유효성 검사가 필요한 페이지",
        "tradeoff": "구현 단순성 vs 상태 제어 용이성",
    },
    {
        "category": "React State",
        "subject": "state 끌어올리기(lifting state up)가 필요한 기준",
        "scenario": "형제 컴포넌트 간 입력값을 동기화해야 하는 화면",
        "tradeoff": "props drilling 증가와 구조 단순성의 균형",
    },
    {
        "category": "TypeScript Basics",
        "subject": "any와 unknown의 차이",
        "scenario": "외부 API 응답 타입이 불확실한 상황",
        "tradeoff": "빠른 개발 vs 타입 안정성",
    },
    {
        "category": "Rendering",
        "subject": "React 렌더링 최적화에서 memo/useMemo/useCallback 차이",
        "scenario": "불필요한 리렌더링이 발생하는 컴포넌트",
        "tradeoff": "최적화 코드 복잡도 증가",
    },
    {
        "category": "Accessibility",
        "subject": "button과 div 클릭 핸들링의 접근성 차이",
        "scenario": "커스텀 클릭 가능한 UI 컴포넌트를 만들 때",
        "tradeoff": "디자인 자유도와 시맨틱/키보드 접근성",
    },
    {
        "category": "Testing Basics",
        "subject": "mock과 stub의 차이",
        "scenario": "컴포넌트 테스트에서 API 호출을 대체할 때",
        "tradeoff": "테스트 신뢰도와 테스트 작성 난이도",
    },
    {
        "category": "Browser Basics",
        "subject": "localStorage/sessionStorage/cookie 차이",
        "scenario": "로그인 상태와 사용자 설정값 저장이 필요한 상황",
        "tradeoff": "보안/만료 정책/용량 제한의 차이",
    },
    {
        "category": "HTTP Basics",
        "subject": "CORS와 preflight 요청이 발생하는 이유",
        "scenario": "다른 도메인의 API를 브라우저에서 호출할 때",
        "tradeoff": "보안 정책 강화와 개발 편의성",
    },
]

CS_INTERVIEW_TOPICS = [
    {
        "category": "DOM Event",
        "subject": "event.target과 event.currentTarget의 차이",
        "scenario": "이벤트 위임으로 리스트 아이템 클릭을 처리할 때",
        "tradeoff": "버블링 활용의 장단점",
    },
    {
        "category": "DOM Event",
        "subject": "event bubbling과 capturing의 차이",
        "scenario": "중첩된 요소에서 클릭 이벤트가 동시에 걸려 있을 때",
        "tradeoff": "핸들러 구성 단순성 vs 예측 가능성",
    },
    {
        "category": "DOM Event",
        "subject": "preventDefault와 stopPropagation 차이",
        "scenario": "링크가 포함된 카드 컴포넌트에서 클릭 동작을 제어할 때",
        "tradeoff": "사용자 기대 동작과 이벤트 흐름 제어",
    },
    {
        "category": "JavaScript Core",
        "subject": "this 바인딩 규칙",
        "scenario": "콜백 함수 안에서 this가 의도와 다르게 동작할 때",
        "tradeoff": "함수 표현식/화살표 함수 선택 기준",
    },
    {
        "category": "JavaScript Core",
        "subject": "closure가 무엇인지와 사용 사례",
        "scenario": "함수 실행이 끝난 뒤에도 내부 변수를 유지해야 할 때",
        "tradeoff": "캡슐화 이점과 메모리 관리 주의점",
    },
    {
        "category": "JavaScript Core",
        "subject": "var, let, const 차이와 호이스팅",
        "scenario": "스코프 버그가 나는 코드를 디버깅할 때",
        "tradeoff": "재할당 가능성/스코프 안정성",
    },
    {
        "category": "Async",
        "subject": "Promise, async/await, then/catch 흐름 차이",
        "scenario": "연속 API 호출에서 에러 처리를 통일해야 할 때",
        "tradeoff": "가독성과 제어 유연성",
    },
    {
        "category": "Event Loop",
        "subject": "microtask와 macrotask의 실행 순서",
        "scenario": "Promise와 setTimeout이 섞인 코드의 출력 순서를 예측할 때",
        "tradeoff": "이해 난이도와 디버깅 시간",
    },
    {
        "category": "Performance",
        "subject": "debounce와 throttle의 차이",
        "scenario": "검색 입력과 스크롤 이벤트를 최적화할 때",
        "tradeoff": "응답성 vs 호출 횟수 감소",
    },
    {
        "category": "Browser Rendering",
        "subject": "Reflow, Repaint, Composite 차이",
        "scenario": "애니메이션 때문에 화면이 끊길 때",
        "tradeoff": "시각 품질과 렌더링 비용",
    },
    {
        "category": "Web Security",
        "subject": "XSS와 CSRF 차이",
        "scenario": "폼 제출과 사용자 입력 렌더링 기능이 함께 있을 때",
        "tradeoff": "보안 강도와 개발 편의성",
    },
]

QUESTION_TEMPLATES = [
    "`{subject}`의 차이/동작을 설명해 주세요. (`{scenario}`)",
    "`{subject}`를 면접에서 답한다면 핵심 포인트를 어떻게 설명하시겠어요? (`{scenario}`)",
    "`{subject}`에서 자주 나오는 함정은 무엇이고, `{tradeoff}` 관점에서 어떻게 정리할 수 있을까요?",
]

FOLLOW_UP_TEMPLATES = [
    "관련된 실제 코드 예시를 하나 들어 설명해 주세요.",
    "초보자가 가장 많이 헷갈리는 포인트는 무엇인가요?",
    "면접에서 1분 내로 답한다면 어떤 순서로 말하겠어요?",
    "실무에서 이 개념을 틀리면 생길 수 있는 버그 예시는 무엇인가요?",
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


def stable_seed(date_key: str, reference_question: str, variation_salt: str = "") -> int:
    seed_source = f"{date_key}|{reference_question}|{variation_salt}".encode("utf-8")
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


def build_dynamic_question(
    date_key: str,
    reference_question: str,
    variation_salt: str = "",
) -> tuple[str, list[str], str, str]:
    seed = stable_seed(
        date_key=date_key,
        reference_question=reference_question,
        variation_salt=variation_salt,
    )
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


def get_int_env(name: str, default: int, min_value: int = 1) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(parsed, min_value)


def is_text_model_candidate(model_name: str) -> bool:
    lowered = model_name.lower()
    blocked_tokens = ["tts", "embedding", "image", "aqa"]
    return not any(token in lowered for token in blocked_tokens)


def build_base_url_candidates(base_url: str) -> list[str]:
    base_url = base_url.rstrip("/")
    candidates = [base_url]
    if "/v1beta" in base_url:
        candidates.append(base_url.replace("/v1beta", "/v1"))
    elif "/v1" in base_url:
        candidates.append(base_url.replace("/v1", "/v1beta"))
    unique: list[str] = []
    for c in candidates:
        if c not in unique:
            unique.append(c)
    return unique


def list_generate_content_models(api_key: str, base_url: str, timeout_sec: int) -> tuple[list[str], str, str]:
    last_error = ""
    for base in build_base_url_candidates(base_url):
        list_endpoint = f"{base}/models?key={quote_plus(api_key)}"
        request = Request(list_endpoint, method="GET")
        try:
            with urlopen(request, timeout=timeout_sec) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as err:
            body = ""
            try:
                body = err.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            last_error = f"models.list HTTP {err.code} on {base}: {body or err.reason}"
            continue
        except (URLError, TimeoutError, json.JSONDecodeError) as err:
            last_error = f"models.list error on {base}: {err}"
            continue

        models = payload.get("models", [])
        available: list[str] = []
        for item in models:
            if not isinstance(item, dict):
                continue
            methods = item.get("supportedGenerationMethods", [])
            if "generateContent" not in methods:
                continue
            name = normalize_gemini_model(str(item.get("name", "")))
            if name and is_text_model_candidate(name):
                available.append(name)
        if available:
            flash_first = [m for m in available if "flash" in m.lower()]
            non_flash = [m for m in available if "flash" not in m.lower()]
            ordered = flash_first + non_flash
            return ordered[:10], base, ""
        last_error = f"models.list returned 0 generateContent models on {base}"

    return [], base_url.rstrip("/"), last_error


def generate_ai_question(
    api_key: str,
    model: str,
    date_key: str,
    track: str,
    topic: dict,
    reference_question: str,
    base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    request_timeout_sec: int = 60,
    max_attempts: int = 7,
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
        "- 프론트엔드 면접 기출 CS(기초 개념) 스타일로 작성해 주세요.\n"
        "- 시스템 디자인/대규모 트래픽/장애 대응/인프라 운영 주제는 제외해 주세요.\n"
        "- 질문은 짧고 명확하게, 그리고 `주제 힌트` 문구를 질문 본문에 그대로 포함해 주세요.\n"
        "- follow-up 2개는 기초 개념 확인형으로 짧게 작성해 주세요.\n"
        "- 예시 스타일: event.target vs event.currentTarget, debounce vs throttle, var/let/const 차이\n"
        "- 반드시 JSON만 반환하세요. 코드블록 금지.\n"
        '형식: {"question":"...","follow_up_1":"...","follow_up_2":"...","category":"..."}'
    )

    base_payload = {
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
            "maxOutputTokens": 320,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING"},
                    "follow_up_1": {"type": "STRING"},
                    "follow_up_2": {"type": "STRING"},
                    "category": {"type": "STRING"},
                },
                "required": ["question", "follow_up_1", "follow_up_2", "category"],
            },
        },
    }
    requested_model = normalize_gemini_model(model)
    discovered_models, working_base_url, discovery_error = list_generate_content_models(
        api_key=api_key,
        base_url=base_url,
        timeout_sec=request_timeout_sec,
    )
    candidates: list[str] = [
        requested_model,
        *discovered_models,
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
    ]
    unique_candidates: list[str] = []
    for name in candidates:
        n = normalize_gemini_model(name)
        if n and is_text_model_candidate(n) and n not in unique_candidates:
            unique_candidates.append(n)

    last_error = ""
    for candidate_model in unique_candidates:
        endpoint = f"{working_base_url}/models/{candidate_model}:generateContent?key={quote_plus(api_key)}"
        for attempt in range(1, max_attempts + 1):
            payload = json.loads(json.dumps(base_payload))
            if attempt >= 2:
                # Retry 시 JSON 형식 요구를 더 강하게 줘서 비정형 응답을 줄인다.
                payload["contents"][0]["parts"][0]["text"] += (
                    "\n중요: 설명 문장 없이 JSON 객체만 반환하세요."
                )
                payload["generationConfig"]["temperature"] = 0.2

            request = Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=request_timeout_sec) as response:
                    response_data = json.loads(response.read().decode("utf-8"))
            except HTTPError as err:
                error_body = ""
                try:
                    error_body = err.read().decode("utf-8", errors="replace")
                except Exception:
                    error_body = ""
                last_error = (
                    f"Gemini API HTTP {err.code} "
                    f"(base={working_base_url}, model={candidate_model}): {error_body or err.reason}"
                )
                error_body_lower = (error_body or "").lower()
                if err.code == 404:
                    break
                if err.code == 400 and (
                    "response modalities" in error_body_lower
                    or "accepts the following combination" in error_body_lower
                    or "invalid_argument" in error_body_lower
                ):
                    # 모델별 입력/출력 제약(예: AUDIO 전용)은 다음 모델로 넘어간다.
                    break
                if err.code in (429, 500, 503):
                    continue
                raise ValueError(last_error) from err
            except (URLError, TimeoutError, json.JSONDecodeError) as err:
                last_error = (
                    "Gemini request failed "
                    f"(base={working_base_url}, model={candidate_model}, attempt={attempt}/{max_attempts}, "
                    f"timeout={request_timeout_sec}s): {err}"
                )
                # 짧은 지수 백오프로 일시적 네트워크 타임아웃 완화
                if attempt < max_attempts:
                    time.sleep(min(1.5 * attempt, 5.0))
                continue

            raw_text = extract_gemini_text(response_data)
            if not raw_text:
                prompt_feedback = response_data.get("promptFeedback", {})
                finish_reason = ""
                candidates_resp = response_data.get("candidates", [])
                if candidates_resp and isinstance(candidates_resp[0], dict):
                    finish_reason = str(candidates_resp[0].get("finishReason", ""))
                last_error = (
                    "Gemini response did not include text "
                    f"(model={candidate_model}, attempt={attempt}, "
                    f"finish_reason={finish_reason}, prompt_feedback={prompt_feedback})"
                )
                continue

            try:
                parsed = parse_ai_json(raw_text)
            except ValueError as err:
                last_error = (
                    f"AI output parse failed (model={candidate_model}, attempt={attempt}): {err}; "
                    f"raw={raw_text[:300]}"
                )
                continue

            question = sanitize_inline(str(parsed.get("question", "")))
            follow_up_1 = sanitize_inline(str(parsed.get("follow_up_1", "")))
            follow_up_2 = sanitize_inline(str(parsed.get("follow_up_2", "")))
            category = sanitize_inline(str(parsed.get("category", topic["category"])))

            if not question or not follow_up_1 or not follow_up_2:
                last_error = (
                    f"AI output missing fields (model={candidate_model}, attempt={attempt}): {parsed}"
                )
                continue
            return question, [follow_up_1, follow_up_2], category, candidate_model

    raise ValueError(
        "No usable Gemini model for generateContent. "
        f"base={working_base_url}; "
        f"tried={', '.join(unique_candidates)}; "
        f"model_discovery_error={discovery_error or 'N/A'}; "
        f"last_error={last_error}"
    )


def sanitize_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def build_pr_title(question: str) -> str:
    plain = sanitize_inline(question).replace("`", "")
    max_len = 180
    if len(plain) > max_len:
        plain = plain[: max_len - 3].rstrip() + "..."
    return plain or "Daily Tech Question"


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

    variation_salt = os.environ.get("QUESTION_VARIATION_SALT", "").strip()
    if not variation_salt:
        run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
        run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "").strip()
        if run_id:
            variation_salt = f"{run_id}-{run_attempt or '1'}"

    seed = stable_seed(
        date_key=date_key,
        reference_question=reference_question,
        variation_salt=variation_salt,
    )
    track = pick_track(seed)
    topic_pool = CS_INTERVIEW_TOPICS if track == "cs" else FRONTEND_INTERVIEW_TOPICS
    topic = topic_pool[seed % len(topic_pool)]

    gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    gemini_base_url = os.environ.get(
        "GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
    ).strip()
    gemini_request_timeout_sec = get_int_env("GEMINI_REQUEST_TIMEOUT_SEC", 60, min_value=5)
    gemini_max_retries = get_int_env("GEMINI_MAX_RETRIES", 7, min_value=1)
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
                request_timeout_sec=gemini_request_timeout_sec,
                max_attempts=gemini_max_retries,
            )
            source_mode = "ai+reference" if reference_question else "ai"
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as err:
            if args.generation_mode == "always":
                raise RuntimeError(f"AI generation failed in always mode: {err}") from err
            question, follow_ups, category, track = build_dynamic_question(
                date_key=date_key,
                reference_question=reference_question,
                variation_salt=variation_salt,
            )
            source_mode = "reference+generated" if reference_question else "generated"
    else:
        question, follow_ups, category, track = build_dynamic_question(
            date_key=date_key,
            reference_question=reference_question,
            variation_salt=variation_salt,
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
