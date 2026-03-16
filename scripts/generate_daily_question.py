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
from urllib.parse import quote_plus, urlencode, urlparse, parse_qs, urlunparse
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))

FRONTEND_INTERVIEW_TOPICS = [
    {
        "category": "React",
        "subject": "React에서 key가 왜 필요한지",
        "scenario": "리스트 렌더링에서 항목 순서가 자주 바뀔 때",
        "tradeoff": "index key 사용의 편의성과 상태 꼬임 위험",
    },
    {
        "category": "React",
        "subject": "useEffect cleanup이 필요한 이유",
        "scenario": "이벤트 리스너/타이머/구독이 있는 컴포넌트",
        "tradeoff": "구현 단순성과 메모리 누수 방지",
    },
    {
        "category": "React",
        "subject": "controlled와 uncontrolled input 차이",
        "scenario": "폼 유효성 검사와 실시간 입력 처리",
        "tradeoff": "코드 복잡도와 제어 가능성",
    },
    {
        "category": "Vue",
        "subject": "Vue에서 ref와 reactive의 차이",
        "scenario": "Composition API로 상태를 관리할 때",
        "tradeoff": "가독성과 반응성 추적의 명확성",
    },
    {
        "category": "Vue",
        "subject": "computed와 watch의 차이",
        "scenario": "파생 상태 계산과 부수효과 처리가 함께 필요할 때",
        "tradeoff": "선언적 계산과 제어 로직 복잡도",
    },
    {
        "category": "Vue",
        "subject": "Vue 라이프사이클 훅(onMounted/onUnmounted) 사용 시점",
        "scenario": "데이터 fetch와 리소스 정리가 필요한 컴포넌트",
        "tradeoff": "빠른 구현과 안정적인 정리(cleanup)",
    },
    {
        "category": "TypeScript",
        "subject": "type과 interface 차이",
        "scenario": "컴포넌트 props 타입을 설계할 때",
        "tradeoff": "확장성/표현력과 팀 컨벤션 일관성",
    },
    {
        "category": "TypeScript",
        "subject": "any와 unknown 차이",
        "scenario": "외부 API 응답 타입이 불확실한 코드",
        "tradeoff": "개발 속도와 타입 안정성",
    },
    {
        "category": "TypeScript",
        "subject": "제네릭을 써야 하는 경우",
        "scenario": "재사용 가능한 훅/유틸 함수를 만들 때",
        "tradeoff": "추상화 수준과 코드 복잡도",
    },
    {
        "category": "Browser Architecture",
        "subject": "Critical Rendering Path(CRP)의 단계",
        "scenario": "초기 렌더링이 느린 웹 페이지",
        "tradeoff": "초기 로딩 최적화와 구현 복잡도",
    },
    {
        "category": "Browser Architecture",
        "subject": "Reflow/Repaint/Composite 차이",
        "scenario": "애니메이션에서 프레임 드랍이 발생할 때",
        "tradeoff": "시각 효과와 렌더링 비용",
    },
    {
        "category": "Browser Architecture",
        "subject": "브라우저 저장소(cookie/localStorage/sessionStorage) 차이",
        "scenario": "인증 정보와 사용자 설정을 분리 저장할 때",
        "tradeoff": "보안, 용량, 만료/전송 정책 차이",
    },
]

CS_INTERVIEW_TOPICS = [
    # DOM Event
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
        "category": "DOM Event",
        "subject": "이벤트 위임(event delegation) 패턴",
        "scenario": "동적으로 생성되는 수백 개의 리스트 아이템에 이벤트를 달 때",
        "tradeoff": "메모리 절약과 핸들러 로직 복잡도",
    },
    # JavaScript
    {
        "category": "JavaScript",
        "subject": "this 바인딩 규칙(call/apply/bind 포함)",
        "scenario": "콜백 함수 안에서 this가 의도와 다르게 동작할 때",
        "tradeoff": "함수 표현식/화살표 함수 선택 기준",
    },
    {
        "category": "JavaScript",
        "subject": "closure가 무엇인지와 사용 사례",
        "scenario": "함수 실행이 끝난 뒤에도 내부 변수를 유지해야 할 때",
        "tradeoff": "캡슐화 이점과 메모리 관리 주의점",
    },
    {
        "category": "JavaScript",
        "subject": "var, let, const 차이와 호이스팅",
        "scenario": "스코프 버그가 나는 코드를 디버깅할 때",
        "tradeoff": "재할당 가능성/스코프 안정성",
    },
    {
        "category": "JavaScript",
        "subject": "Promise.all / Promise.allSettled / Promise.race 차이",
        "scenario": "여러 비동기 요청을 함께 처리할 때",
        "tradeoff": "실패 처리 방식과 응답 완료 전략",
    },
    {
        "category": "JavaScript",
        "subject": "프로토타입 체인과 상속 동작 방식",
        "scenario": "클래스 문법 없이 객체 메서드를 공유해야 할 때",
        "tradeoff": "메모리 공유 이점과 체인 탐색 비용",
    },
    {
        "category": "JavaScript",
        "subject": "얕은 복사(shallow copy)와 깊은 복사(deep copy) 차이",
        "scenario": "중첩 객체 상태를 불변하게 업데이트해야 할 때",
        "tradeoff": "구현 단순성과 참조 공유 위험",
    },
    {
        "category": "JavaScript",
        "subject": "Map과 Object의 차이 및 사용 시점",
        "scenario": "키가 동적으로 바뀌는 빈번한 조회/삽입 구조를 설계할 때",
        "tradeoff": "API 편의성과 성능 특성",
    },
    {
        "category": "JavaScript",
        "subject": "Set과 Array의 차이 및 중복 제거",
        "scenario": "대량 데이터에서 유일값 목록을 빠르게 구해야 할 때",
        "tradeoff": "조회 성능과 순서 보장 여부",
    },
    {
        "category": "JavaScript",
        "subject": "제너레이터(generator)와 이터레이터(iterator) 개념",
        "scenario": "무한 스크롤 데이터를 지연 평가로 처리할 때",
        "tradeoff": "메모리 효율과 코드 복잡도",
    },
    {
        "category": "JavaScript",
        "subject": "WeakMap / WeakRef의 용도와 일반 Map과의 차이",
        "scenario": "DOM 노드에 메타데이터를 붙이되 GC를 막고 싶지 않을 때",
        "tradeoff": "메모리 누수 방지와 접근 불확실성",
    },
    {
        "category": "JavaScript",
        "subject": "옵셔널 체이닝(?.)과 널 병합(??) 연산자",
        "scenario": "깊은 중첩 객체에서 안전하게 값을 꺼낼 때",
        "tradeoff": "코드 간결성과 falsy 값 처리 주의점",
    },
    # Async
    {
        "category": "Async",
        "subject": "async/await와 then/catch 차이",
        "scenario": "연속 API 호출에서 에러 처리를 통일해야 할 때",
        "tradeoff": "가독성과 제어 유연성",
    },
    {
        "category": "Async",
        "subject": "AbortController로 fetch 요청을 취소하는 방법",
        "scenario": "사용자가 검색어를 빠르게 바꿔 이전 요청이 불필요해질 때",
        "tradeoff": "UX 개선과 취소 로직 추가 복잡도",
    },
    # Event Loop
    {
        "category": "Event Loop",
        "subject": "microtask와 macrotask의 실행 순서",
        "scenario": "Promise와 setTimeout이 섞인 코드의 출력 순서를 예측할 때",
        "tradeoff": "이해 난이도와 디버깅 시간",
    },
    {
        "category": "Event Loop",
        "subject": "requestAnimationFrame vs setTimeout 애니메이션 차이",
        "scenario": "60fps 애니메이션을 자바스크립트로 구현할 때",
        "tradeoff": "프레임 동기화 정확성과 배터리 소모",
    },
    {
        "category": "Event Loop",
        "subject": "requestIdleCallback 활용 시점",
        "scenario": "분석 이벤트 전송처럼 낮은 우선순위 작업을 처리할 때",
        "tradeoff": "메인 스레드 양보와 실행 보장 불확실성",
    },
    # Performance
    {
        "category": "Performance",
        "subject": "debounce와 throttle의 차이",
        "scenario": "검색 입력과 스크롤 이벤트를 최적화할 때",
        "tradeoff": "응답성 vs 호출 횟수 감소",
    },
    {
        "category": "Performance",
        "subject": "메모이제이션(memoization)이 필요한 상황",
        "scenario": "렌더링마다 비용이 큰 계산이 반복될 때",
        "tradeoff": "CPU 절약과 메모리 증가 트레이드오프",
    },
    {
        "category": "Performance",
        "subject": "Web Worker를 사용해야 하는 상황",
        "scenario": "대용량 JSON 파싱이나 이미지 처리로 UI가 멈출 때",
        "tradeoff": "병렬 처리 이점과 통신 비용·API 제약",
    },
    {
        "category": "Performance",
        "subject": "가상화(windowing/virtualization) 리스트 렌더링",
        "scenario": "수만 건 데이터를 목록으로 보여줄 때",
        "tradeoff": "DOM 노드 절감과 스크롤 위치 관리 복잡도",
    },
    {
        "category": "Performance",
        "subject": "이미지 lazy loading과 Intersection Observer 활용",
        "scenario": "뷰포트 밖 이미지가 많은 긴 페이지를 최적화할 때",
        "tradeoff": "초기 로드 감소와 레이아웃 시프트(CLS) 위험",
    },
    # HTTP & Network
    {
        "category": "HTTP",
        "subject": "CORS와 preflight 요청이 발생하는 이유",
        "scenario": "프론트엔드에서 다른 도메인의 API를 호출할 때",
        "tradeoff": "보안 정책과 개발 편의성",
    },
    {
        "category": "HTTP",
        "subject": "Cache-Control, ETag, Last-Modified 차이",
        "scenario": "브라우저 캐시 전략을 설계할 때",
        "tradeoff": "최신성 보장과 네트워크 절감",
    },
    {
        "category": "HTTP",
        "subject": "HTTP/1.1 vs HTTP/2 vs HTTP/3 주요 차이",
        "scenario": "정적 에셋이 많은 SPA의 네트워크 성능을 개선할 때",
        "tradeoff": "멀티플렉싱 이점과 서버 설정 복잡도",
    },
    {
        "category": "HTTP",
        "subject": "REST API와 GraphQL의 차이",
        "scenario": "한 화면에서 여러 리소스를 조합해 보여줄 때",
        "tradeoff": "오버페칭 해소와 쿼리 복잡도·캐싱 난이도",
    },
    {
        "category": "HTTP",
        "subject": "웹소켓(WebSocket)과 SSE(Server-Sent Events) 차이",
        "scenario": "실시간 알림 또는 채팅 기능을 구현할 때",
        "tradeoff": "양방향 통신 여부와 구현 복잡도",
    },
    {
        "category": "HTTP",
        "subject": "쿠키의 SameSite, HttpOnly, Secure 속성",
        "scenario": "인증 토큰을 쿠키로 관리하며 CSRF를 막아야 할 때",
        "tradeoff": "보안 강도와 크로스 도메인 사용 제한",
    },
    # Browser Architecture
    {
        "category": "Browser Architecture",
        "subject": "싱글 스레드에서 자바스크립트가 동시성을 다루는 방식",
        "scenario": "UI 이벤트와 비동기 작업이 동시에 많은 상황",
        "tradeoff": "단순한 실행 모델과 블로킹 리스크",
    },
    {
        "category": "Browser Architecture",
        "subject": "파서 블로킹 스크립트와 defer/async 속성 차이",
        "scenario": "서드파티 스크립트 로드 때문에 FCP가 늦어질 때",
        "tradeoff": "실행 순서 보장과 초기 렌더링 속도",
    },
    {
        "category": "Browser Architecture",
        "subject": "service worker의 역할과 캐싱 전략",
        "scenario": "오프라인 지원과 반복 방문 속도 개선이 필요할 때",
        "tradeoff": "오프라인 대응과 캐시 무효화 복잡도",
    },
    {
        "category": "Browser Architecture",
        "subject": "브라우저 렌더링 파이프라인(Style→Layout→Paint→Composite)",
        "scenario": "CSS 변경이 성능에 미치는 영향을 분석할 때",
        "tradeoff": "표현 자유도와 GPU 레이어 비용",
    },
    # Web Security
    {
        "category": "Web Security",
        "subject": "XSS와 CSRF 차이",
        "scenario": "폼 제출과 사용자 입력 렌더링 기능이 함께 있을 때",
        "tradeoff": "보안 강도와 개발 편의성",
    },
    {
        "category": "Web Security",
        "subject": "Content Security Policy(CSP) 기본 개념",
        "scenario": "인라인 스크립트 삽입 공격을 차단해야 할 때",
        "tradeoff": "XSS 방어 수준과 정책 설정 유지 비용",
    },
    {
        "category": "Web Security",
        "subject": "JWT 인증 방식과 세션 기반 인증의 차이",
        "scenario": "여러 도메인에 걸친 SSO를 구현할 때",
        "tradeoff": "stateless 확장성과 토큰 탈취 대응 어려움",
    },
    {
        "category": "Web Security",
        "subject": "OAuth 2.0 인가 코드 흐름(Authorization Code Flow)",
        "scenario": "소셜 로그인 연동을 프론트에서 구현할 때",
        "tradeoff": "보안 강도와 리다이렉트 복잡도",
    },
    # CSS & Layout
    {
        "category": "CSS",
        "subject": "Flexbox와 Grid 레이아웃 선택 기준",
        "scenario": "1차원 정렬과 2차원 그리드 배치가 혼재할 때",
        "tradeoff": "코드 단순성과 레이아웃 표현력",
    },
    {
        "category": "CSS",
        "subject": "CSS 박스 모델(box-sizing: content-box vs border-box)",
        "scenario": "패딩을 추가했을 때 요소 크기가 예상과 다를 때",
        "tradeoff": "직관성과 레거시 호환성",
    },
    {
        "category": "CSS",
        "subject": "CSS 특이도(specificity) 계산 규칙",
        "scenario": "여러 스타일 규칙이 충돌해 의도한 스타일이 적용 안 될 때",
        "tradeoff": "선택자 강도와 유지보수성",
    },
    {
        "category": "CSS",
        "subject": "CSS 변수(custom properties)와 전처리기 변수 차이",
        "scenario": "런타임에 테마를 동적으로 변경해야 할 때",
        "tradeoff": "런타임 유연성과 브라우저 지원",
    },
    {
        "category": "CSS",
        "subject": "position: static/relative/absolute/fixed/sticky 차이",
        "scenario": "헤더를 고정하거나 툴팁을 특정 요소 기준으로 배치할 때",
        "tradeoff": "배치 정밀도와 스태킹 컨텍스트 부작용",
    },
    # Rendering Strategy
    {
        "category": "Rendering Strategy",
        "subject": "CSR, SSR, SSG, ISR의 차이와 선택 기준",
        "scenario": "SEO가 중요한 커머스 페이지 아키텍처를 결정할 때",
        "tradeoff": "초기 로드·SEO·서버 비용·데이터 신선도",
    },
    {
        "category": "Rendering Strategy",
        "subject": "하이드레이션(hydration)이란 무엇인지",
        "scenario": "SSR로 내려온 HTML에 리액트가 이벤트를 붙일 때",
        "tradeoff": "TTI 지연과 FCP 이점",
    },
    # Accessibility
    {
        "category": "Accessibility",
        "subject": "WAI-ARIA role, aria-label, aria-hidden 사용법",
        "scenario": "아이콘만 있는 버튼을 스크린 리더가 읽게 할 때",
        "tradeoff": "접근성 향상과 마크업 복잡도",
    },
    {
        "category": "Accessibility",
        "subject": "키보드 포커스 관리와 focus trap 구현",
        "scenario": "모달 다이얼로그가 열렸을 때 포커스를 가두어야 할 때",
        "tradeoff": "접근성 표준 준수와 UX 자연스러움",
    },
    # Design Patterns
    {
        "category": "Design Pattern",
        "subject": "옵저버 패턴과 이벤트 버스",
        "scenario": "컴포넌트 간 직접 의존 없이 상태 변화를 알려야 할 때",
        "tradeoff": "결합도 감소와 흐름 추적 어려움",
    },
    {
        "category": "Design Pattern",
        "subject": "싱글턴 패턴의 장단점과 프론트엔드 적용 사례",
        "scenario": "전역 공유 인스턴스(axios 인스턴스, WebSocket 연결)를 관리할 때",
        "tradeoff": "인스턴스 공유 편의성과 테스트 격리 어려움",
    },
    {
        "category": "Design Pattern",
        "subject": "컴파운드 컴포넌트(compound component) 패턴",
        "scenario": "Tabs, Select처럼 내부 상태를 공유하는 복합 UI를 설계할 때",
        "tradeoff": "유연성과 암묵적 컨텍스트 의존성",
    },
    # Testing
    {
        "category": "Testing",
        "subject": "단위 테스트, 통합 테스트, E2E 테스트 차이",
        "scenario": "프론트엔드 테스트 전략을 처음 수립할 때",
        "tradeoff": "피드백 속도와 실제 동작 신뢰도",
    },
    {
        "category": "Testing",
        "subject": "테스트 더블(mock, stub, spy, fake)의 차이",
        "scenario": "외부 API에 의존하는 컴포넌트를 격리 테스트할 때",
        "tradeoff": "테스트 속도·격리성과 실제 동작 충실도",
    },
    # Build & Module
    {
        "category": "Build & Module",
        "subject": "CommonJS(require)와 ES Module(import)의 차이",
        "scenario": "번들러 설정에서 모듈 형식을 결정할 때",
        "tradeoff": "동기 로드 단순성과 정적 분석·트리 셰이킹 가능 여부",
    },
    {
        "category": "Build & Module",
        "subject": "트리 셰이킹(tree-shaking)이 동작하는 조건",
        "scenario": "라이브러리 번들 사이즈를 줄이려 할 때",
        "tradeoff": "번들 경량화와 사이드이펙트 있는 코드 처리",
    },
    {
        "category": "Build & Module",
        "subject": "코드 스플리팅과 동적 import()의 활용",
        "scenario": "초기 번들이 너무 커 초기 로드가 느릴 때",
        "tradeoff": "초기 로드 감소와 추가 네트워크 요청",
    },
]

QUESTION_TEMPLATES = [
    "`{subject}` 차이를 설명해 주세요.",
    "`{subject}` 핵심 개념을 짧게 설명해 주세요.",
    "`{subject}` 면접 답변 포인트는 무엇인가요?",
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


def inject_dynamic_page(url: str, date: "datetime") -> str:
    """URL에 page 파라미터가 없으면 날짜 기반으로 동적 계산해서 추가한다."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    if "page" in params:
        return url
    # 2025-01-01 기준으로 경과 주 수 → 페이지 순환 (최대 50페이지 가정)
    epoch = datetime(2025, 1, 1, tzinfo=date.tzinfo)
    weeks_elapsed = max(0, (date - epoch).days // 7)
    page = (weeks_elapsed % 50) + 1
    params["page"] = [str(page)]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


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


def compact_question(question: str, subject: str) -> str:
    q = sanitize_inline(question)
    q = re.sub(r"주제\s*힌트\s*:\s*", "", q, flags=re.IGNORECASE)
    q = q.strip(" -")

    too_long = len(q) > 90
    noisy = any(token in q for token in ["트레이드오프", "관점", "상황에서", "설명하고, 각각"])
    if q and not too_long and not noisy:
        return q

    subject_clean = sanitize_inline(subject).strip("` ")
    return f"`{subject_clean}` 차이를 설명해 주세요."


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


def normalize_question_key(question: str) -> str:
    normalized = sanitize_inline(question).lower().replace("`", "")
    normalized = re.sub(r"[^0-9a-z가-힣]+", "", normalized)
    return normalized


def empty_question_db() -> dict:
    return {"version": 1, "updated_at": "", "items": []}


def load_question_db(db_path: Path) -> dict:
    if not db_path.exists():
        return empty_question_db()

    try:
        raw = json.loads(db_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"[warn] failed to parse question db ({db_path}): {err}", file=sys.stderr)
        return empty_question_db()

    if not isinstance(raw, dict):
        return empty_question_db()

    items = raw.get("items", [])
    if not isinstance(items, list):
        items = []

    return {
        "version": int(raw.get("version", 1)),
        "updated_at": str(raw.get("updated_at", "")),
        "items": [item for item in items if isinstance(item, dict)],
    }


def build_used_question_keys(question_db: dict) -> set[str]:
    used_keys: set[str] = set()
    for item in question_db.get("items", []):
        if not isinstance(item, dict):
            continue
        key = sanitize_inline(str(item.get("normalized_question", "")))
        if not key:
            key = normalize_question_key(str(item.get("question", "")))
        if key:
            used_keys.add(key)
    return used_keys


def save_question_db(db_path: Path, question_db: dict) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(
        json.dumps(question_db, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_question_db(
    question_db: dict,
    question_key: str,
    date_key: str,
    question: str,
    category: str,
    track: str,
    source_mode: str,
    markdown_path: Path,
) -> None:
    question_db["items"].append(
        {
            "date": date_key,
            "question": sanitize_inline(question),
            "normalized_question": question_key,
            "category": sanitize_inline(category),
            "track": "CS" if track == "cs" else "Frontend",
            "source_mode": sanitize_inline(source_mode),
            "markdown_file": markdown_path.as_posix(),
        }
    )
    question_db["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_attempt_salt(base_salt: str, attempt: int) -> str:
    if attempt == 0:
        return base_salt
    attempt_tag = f"dedup-{attempt}"
    if not base_salt:
        return attempt_tag
    return f"{base_salt}|{attempt_tag}"


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
    avoid_questions: list[str] | None = None,
    variation_tag: str = "",
) -> tuple[str, list[str], str, str]:
    track_label = "CS" if track == "cs" else "Frontend"
    reference_line = reference_question if reference_question else "N/A"
    avoid_questions = avoid_questions or []
    variation_line = variation_tag or "base"
    avoid_block = ""
    if avoid_questions:
        rendered = "\n".join(
            [f"  - {sanitize_inline(item)}" for item in avoid_questions[:50] if sanitize_inline(item)]
        )
        if rendered:
            avoid_block = (
                "## 이미 출제된 질문 (절대 중복 금지)\n"
                f"{rendered}\n\n"
            )
    prompt = (
        "당신은 프론트엔드 개발자 취업 면접 전문가입니다. "
        "매일 새로운 프론트엔드 CS 면접 질문을 한 개 생성해야 합니다.\n\n"
        f"{avoid_block}"
        "## 생성 규칙\n"
        f"- 오늘 날짜: {date_key} (variation: {variation_line})\n"
        f"- 카테고리 참고(강제 아님): {topic['category']}\n"
        f"- 외부 참고 질문(영감용): {reference_line}\n\n"
        "## 질문 기준\n"
        "- 실제 프론트엔드 개발자 면접에서 자주 나오는 CS 개념 중심\n"
        "- 주제 범위: JavaScript 동작 원리, TypeScript 타입 시스템, React/Vue 내부 동작, "
        "브라우저 렌더링·이벤트 루프·네트워크(HTTP/CORS/캐시/웹소켓), "
        "CSS 레이아웃·스태킹 컨텍스트, 웹 보안(XSS/CSRF/CSP/JWT), "
        "렌더링 전략(CSR/SSR/SSG/하이드레이션), 웹 성능 최적화, "
        "접근성(ARIA), 디자인 패턴, 테스트 전략, 번들링·모듈 시스템\n"
        "- 이미 출제된 질문 목록과 주제가 겹치면 안 됩니다. 반드시 새로운 개념을 선택하세요.\n"
        "- 시스템 디자인·대규모 트래픽·인프라·백엔드 전용 주제는 제외\n\n"
        "## 형식 규칙\n"
        "- 질문: 한 문장, 50자 이내, 명확하고 구체적으로\n"
        "- 배경 설명·트레이드오프 관점 등 부연 설명은 질문 본문에 넣지 마세요\n"
        "- follow_up 2개: 질문 개념을 더 깊이 파는 꼬리 질문, 각 30자 이내\n"
        "- 반드시 JSON만 반환, 코드블록 없음\n\n"
        '{"question":"...","follow_up_1":"...","follow_up_2":"...","category":"..."}'
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

            question = compact_question(str(parsed.get("question", "")), topic["subject"])
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
    db_path: Path,
    dedup_attempt: int,
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
        f.write(f"question_db_path={db_path.as_posix()}\n")
        f.write(f"dedup_attempt={dedup_attempt}\n")


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
    parser.add_argument(
        "--db-path",
        default=os.environ.get("QUESTION_DB_PATH", ""),
        help="Path to question history DB JSON. Default: <output-dir>/db.json",
    )
    parser.add_argument(
        "--dedup-max-attempts",
        type=int,
        default=get_int_env("QUESTION_DEDUP_MAX_ATTEMPTS", 12, min_value=1),
    )
    args = parser.parse_args()

    now = datetime.now(KST if args.tz == "KST" else timezone.utc)
    date_key = now.date().isoformat()

    cookie = os.environ.get("QUESTION_SOURCE_COOKIE", "")
    reference_question = ""
    source_mode = "generated"

    if args.source_url:
        try:
            source_url_with_page = inject_dynamic_page(args.source_url, now)
            reference_question = fetch_source_question(source_url_with_page, cookie)
        except (HTTPError, URLError, TimeoutError, ValueError):
            reference_question = ""

    variation_salt = os.environ.get("QUESTION_VARIATION_SALT", "").strip()
    if not variation_salt:
        run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
        run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "").strip()
        if run_id:
            variation_salt = f"{run_id}-{run_attempt or '1'}"

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

    db_path = Path(args.db_path) if args.db_path else Path(args.output_dir) / "db.json"
    question_db = load_question_db(db_path)
    used_question_keys = build_used_question_keys(question_db)
    recent_questions = [
        sanitize_inline(str(item.get("question", "")))
        for item in question_db.get("items", [])
        if isinstance(item, dict) and sanitize_inline(str(item.get("question", "")))
    ]

    used_ai_model = ""
    dedup_attempt = 0
    question = ""
    follow_ups: list[str] = []
    category = ""
    track = "cs"
    question_key = ""

    max_dedup_attempts = max(args.dedup_max_attempts, 1)
    for attempt in range(max_dedup_attempts):
        dedup_attempt = attempt + 1
        attempt_salt = build_attempt_salt(variation_salt, attempt)

        seed = stable_seed(
            date_key=date_key,
            reference_question=reference_question,
            variation_salt=attempt_salt,
        )
        track = pick_track(seed)
        topic_pool = CS_INTERVIEW_TOPICS if track == "cs" else FRONTEND_INTERVIEW_TOPICS
        topic = topic_pool[seed % len(topic_pool)]

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
                    avoid_questions=recent_questions[-50:],
                    variation_tag=attempt_salt,
                )
                source_mode = "ai+reference" if reference_question else "ai"
            except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as err:
                if args.generation_mode == "always":
                    raise RuntimeError(f"AI generation failed in always mode: {err}") from err
                question, follow_ups, category, track = build_dynamic_question(
                    date_key=date_key,
                    reference_question=reference_question,
                    variation_salt=attempt_salt,
                )
                source_mode = "reference+generated" if reference_question else "generated"
        else:
            question, follow_ups, category, track = build_dynamic_question(
                date_key=date_key,
                reference_question=reference_question,
                variation_salt=attempt_salt,
            )
            source_mode = "reference+generated" if reference_question else "generated"

        question_key = normalize_question_key(question)
        if question_key and question_key not in used_question_keys:
            break
        print(
            f"Duplicate question detected ({dedup_attempt}/{max_dedup_attempts}): {question}",
            file=sys.stderr,
        )
    else:
        raise RuntimeError(
            f"Failed to generate a unique question after {max_dedup_attempts} attempts. "
            f"db={db_path.as_posix()}"
        )

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
        db_path=db_path,
        dedup_attempt=dedup_attempt,
    )
    append_question_db(
        question_db=question_db,
        question_key=question_key,
        date_key=date_key,
        question=question,
        category=category,
        track=track,
        source_mode=source_mode,
        markdown_path=file_path,
    )
    save_question_db(db_path, question_db)

    print(f"Generated: {file_path}")
    print(f"Question DB: {db_path.as_posix()}")
    print(f"Dedup attempt used: {dedup_attempt}/{max_dedup_attempts}")
    print(f"Source mode: {source_mode}")
    if source_mode.startswith("ai"):
        print(f"AI model: {used_ai_model}")
    print(f"Track: {track}")
    print(f"Category: {category}")
    print(f"Question: {question}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
