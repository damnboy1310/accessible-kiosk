# 버거킹 접근성 키오스크 (Fake Demo)

시각장애·지체장애(휠체어) 사용자를 위한 접근성 중심 키오스크 데모.
PyQt6 UI + 오프라인 TTS + LLM(Claude/Mock) 자연어 주문 + 가짜 결제.

자세한 명세는 [`docs/SPEC.md`](docs/SPEC.md) 참고.

## 설치

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> Linux에서 TTS 음성을 들으려면 `espeak`/`espeak-ng`가 필요합니다.
> (없어도 콘솔에 `[TTS]` 안내문이 출력되어 흐름 확인 가능)

## 실행

```bash
# Mock LLM (API 키 불필요) — 기본값
python -m src.main

# 실제 Claude API 사용
cp .env.example .env   # ANTHROPIC_API_KEY 입력, KIOSK_LLM_MODE=claude
python -m src.main
```

## 웹 버전 — Windows 키오스크

PyQt6 데스크톱 버전과 도메인 로직(`src/`)을 공유하는 Flask 웹 레이어(`web/`).
**세로(포트레이트) / 가로(랜드스케이프) 두 레이아웃을 모두 지원**하며,
기준 디자인을 실제 해상도에 맞춰 자동 확대합니다. FHD 모니터에서는 여백 없이 꽉 차고
글자·버튼·여백이 모두 2배로 커집니다.

---

### 화면 방향 전환 (세로 / 가로)

| 레이아웃 | 기준 디자인 | 화면 구성 |
|---|---|---|
| **세로** (portrait) | 540x960 (9:16) | 1단 — 시작 → 주문 → 장바구니 → 결제 순서대로 이동 |
| **가로** (landscape) | 960x540 (16:9) | 2단 — 왼쪽 메뉴/대화 + **오른쪽 장바구니 상시 노출**, 메뉴 4열 |

전환 방법은 세 가지입니다.

| 방법 | 사용법 | 비고 |
|---|---|---|
| **자동 (기본값)** | 별도 설정 없음 | 모니터 방향을 감지해 자동으로 맞춤 |
| **툴바 버튼** | 접근성 툴바의 `화면 자동` 버튼 | 자동 → 세로 → 가로 순환, 선택은 브라우저에 저장됨 |
| **URL 파라미터** | `?orient=portrait` / `landscape` / `auto` | 키오스크 실행 URL에 고정할 때 사용 |

우선순위는 **URL 파라미터 > 저장된 선택 > 자동**입니다.
레이아웃과 실제 화면 방향이 어긋나면(예: 가로 모니터에서 세로 강제) 화면 가운데에
letterbox 프레임으로 표시되므로, 개발용 노트북에서도 키오스크 화면 그대로 미리보기가 가능합니다.

구현은 `html[data-orient]` 속성으로 CSS를 분기하는 방식입니다
(`web/static/style.css`의 가로형 레이아웃 섹션, `web/static/app.js`의 화면 방향 모듈).

---

### 1. 사전 준비 (키오스크 PC)

| 프로그램 | 비고 |
|---|---|
| [Python 3.10+](https://www.python.org/downloads/windows/) | 설치 시 **"Add python.exe to PATH"** 체크 필수 |
| [Git for Windows](https://git-scm.com/download/win) | 코드 받기 / 업데이트용 |
| Microsoft Edge | Windows 기본 탑재 (키오스크 모드로 사용) |

### 2. 화면 방향 (세로로 설치하는 경우만)

16:9 FHD 모니터를 세로로 세워 설치한다면 Windows 쪽 회전이 필요합니다.

설정 → 시스템 → 디스플레이 → **디스플레이 방향: 세로**

모니터를 어느 쪽으로 눕히느냐에 따라 `세로` 또는 `세로(대칭 이동)`를 고릅니다.
화면이 거꾸로 보이면 반대쪽을 선택하세요. 해상도가 **1080 x 1920**으로 표시되면 정상입니다.

가로(1920 x 1080) 그대로 쓸 거라면 이 단계는 건너뛰면 됩니다 — 앱이 자동으로 2단 가로 레이아웃으로 뜹니다.

### 3. 코드 받기

```
git clone https://github.com/damnboy1310/accessible-kiosk.git
cd accessible-kiosk
```

### 4. Claude API 연결

"말로 주문" 탭의 자연어 주문에만 필요합니다. 메뉴 터치 주문은 API 없이도 동작합니다.

**4-1. API 키 발급** — [console.anthropic.com](https://console.anthropic.com) → API keys → Create Key (`sk-ant-...`)

**4-2. `.env` 작성** — 최초 실행 시 `run-kiosk.bat`이 `.env.example`을 복사하고 메모장을 열어줍니다.
수동으로 만들려면 `.env.example`을 `.env`로 복사한 뒤 편집하세요.

```ini
ANTHROPIC_API_KEY=sk-ant-...
KIOSK_LLM_MODE=claude
```

**4-3. 모드 선택** — `KIOSK_LLM_MODE` 값에 따라 동작이 달라집니다.

| 모드 | 동작 | API 키 |
|---|---|---|
| `mock` | 규칙 기반 가짜 응답으로 주문 흐름만 시연 | 불필요 |
| `claude` | 실제 Claude API로 자연어 주문 처리 | 필요 |

`claude`로 두고 키가 없으면 오류 없이 **자동으로 Mock으로 대체**됩니다 (서버 로그에 안내 출력).

**4-4. 사용 모델과 비용** — `src/config.py`의 `CLAUDE_MODEL`에서 지정합니다.

| 항목 | 값 |
|---|---|
| 모델 | `claude-haiku-4-5` (비용 최적화 선택) |
| 컨텍스트 | 200K 토큰 |
| 가격 | 입력 $1 / 출력 $5 (100만 토큰당) |

주문 1건이 수백~수천 토큰 수준이라 시연·전시 용도의 비용은 미미합니다.

**4-5. 연결 확인** — 서버 기동 시 콘솔(최소화된 `kiosk-server` 창)에 찍히는 로그로 판단합니다.

```
[LLM] Claude API 모드     ← 연결 성공
[LLM] Mock 모드           ← 키 없음 또는 초기화 실패
```

실제 동작 확인은 "말로 주문" 탭에서 `와퍼 세트 하나 주세요`를 입력해보면 됩니다.

> `/healthz`는 `.env`에 **설정된** 모드를 그대로 반환하므로, 키가 없어 Mock으로 대체된 경우에도
> `claude`로 표시됩니다. 실제 동작 모드는 위 콘솔 로그로 확인하세요.

> **`.env`는 절대 커밋하지 마세요.** `.gitignore` 대상이라 저장소에 포함되지 않으며,
> 이 저장소는 **public**입니다.

### 5. 실행

```
run-kiosk.bat
```

최신 코드 pull → 가상환경/의존성 설치 → 서버 기동 → Edge 키오스크 모드 실행까지 한 번에 처리합니다.
서버는 `127.0.0.1:8000`에만 바인딩되므로 **외부 노출이 없습니다.**

- 키오스크 종료: `Alt + F4`
- 콘솔 창을 닫으면 서버도 함께 종료됩니다
- 코드를 수정한 뒤에는 `run-kiosk.bat`을 다시 실행하면 자동으로 pull 받습니다

### 6. 부팅 시 자동 실행

`Win + R` → `shell:startup` → 열린 폴더에 `run-kiosk.bat` **바로가기**를 넣습니다.

### 7. Windows 추가 설정

| 항목 | 설정 위치 | 이유 |
|---|---|---|
| 터치 키보드 | 설정 → 시간 및 언어 → 입력 → 터치 키보드: **항상** | "말로 주문" 텍스트 입력 |
| 화면 절전 끄기 | 설정 → 시스템 → 전원 → 화면 끄기: **안 함** | 무인 운영 |
| 잠금 화면 해제 | 설정 → 개인 설정 → 잠금 화면 → 화면 보호기 없음 | 무인 운영 |
| 한국어 TTS 음성 | 설정 → 시간 및 언어 → 음성 → 음성 추가 (한국어) | 음성 안내(`speechSynthesis`, `ko-KR`) |

---

### Docker (Linux 서버)

```bash
docker compose up -d --build   # http://localhost:8000
```

Windows에서는 gunicorn이 동작하지 않으므로(`fcntl` 의존, Unix 전용)
`requirements-web.txt`가 플랫폼 마커로 Windows에서는 `waitress`를 설치합니다.

## 화면 흐름

```
시작/접근성설정 → 주문(메뉴보기·말로주문) → 장바구니 → 결제(Fake) → 완료
```

## 대화형 주문 예시

- "와퍼 세트 하나 주세요"
- "불고기와퍼랑 콜라 주세요"
- "감자튀김 빼주세요"
- "결제할게요"

## 접근성 기능

- 음성 안내(TTS): 화면 진입·포커스 이동·상태 변화
- 고대비 모드 / 글자 크기 100~200% / 낮은 화면(휠체어) / 음성 ON·OFF / 화면 방향(자동·세로·가로)
- 음성만으로도, 터치(클릭)만으로도 주문 완료 가능한 이중 경로

## 구조

```
src/
├── main.py                # 진입점
├── config.py              # 설정/환경변수
├── domain/                # menu, cart
├── accessibility/         # tts, a11y_settings
├── services/
│   ├── llm/               # base, mock_client, claude_client
│   └── payment.py         # Fake 결제
└── ui/                    # theme, app_context, main_window, screens/
```
