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
