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

## 웹 버전 (키오스크 배포용)

PyQt6 데스크톱 버전과 도메인 로직(`src/`)을 공유하는 Flask 웹 레이어(`web/`).
화면은 **세로형(포트레이트)** 기준이며, `540x960` 디자인을 실제 해상도에 맞춰 자동 확대합니다.
1080x1920 세로 모니터에서 여백 없이 꽉 차고 글자/버튼도 2배로 커집니다.

### Windows 키오스크에서 실행

세로로 회전한 16:9 FHD 모니터(1080x1920) 기준입니다.

```
git clone https://github.com/damnboy1310/accessible-kiosk.git
cd accessible-kiosk
run-kiosk.bat
```

`run-kiosk.bat`이 최신 코드 pull → 가상환경/의존성 설치 → 서버 기동 → Edge 키오스크 모드 실행까지 한 번에 처리합니다.
서버는 `127.0.0.1:8000`에만 바인딩되므로 외부 노출이 없습니다.

부팅 시 자동 실행하려면 `Win+R` → `shell:startup` 폴더에 `run-kiosk.bat` 바로가기를 넣으세요.

**Windows 사전 설정**

| 항목 | 설정 위치 |
|---|---|
| 화면 세로 회전 | 설정 → 시스템 → 디스플레이 → 디스플레이 방향: **세로** |
| 터치 키보드 (말로주문 입력용) | 설정 → 시간 및 언어 → 입력 → 터치 키보드: **항상** |
| 화면 절전 끄기 | 설정 → 시스템 → 전원 → 화면 끄기: **안 함** |
| 한국어 TTS 음성 | 설정 → 시간 및 언어 → 음성 → 음성 추가 (한국어) |

> `.env`는 `.gitignore` 대상이라 저장소에 없습니다. 키오스크 PC에서 최초 실행 시
> `.env.example`이 자동 복사되고 메모장이 열리므로 거기서 API 키를 넣으세요.
> **public 저장소이므로 `.env`를 커밋하지 마세요.**

### Docker (Linux 서버)

```bash
docker compose up -d --build   # http://localhost:8000
```

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
- 고대비 모드 / 글자 크기 100~200% / 낮은 화면(휠체어) / 음성 ON·OFF
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
