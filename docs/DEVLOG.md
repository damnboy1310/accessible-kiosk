# DEVLOG — 버거킹 접근성 키오스크

> 세션 간 연속성을 위한 단일 추적 문서. 새 세션 시작 시 **이 파일을 먼저 읽고**,
> 작업 후 해당 섹션을 갱신한다. (명세는 `docs/SPEC.md`, 실행법은 `README.md`)

최종 업데이트: **2026-06-22**

---

## 0. 한눈에 보기 (현재 상태)

- **단계**: 웹 데모(Fake) 배포 완료. 실 LLM/STT/결제는 미연동.
- **빌드**: PyQt6 → **웹(Flask + HTML/JS)로 전환 완료**. Qt 코드는 참고용으로 보존(`src/ui/`).
- **재사용 코어**: `src/domain`, `src/services`, `src/config` (Qt·웹 공용)
- **LLM**: 현재 **mock 모드** 배포(키 불필요). claude 모드는 키 추가 시 전환.

### 배포 정보 (호스팅: `~/docker` 규칙, tailnet 전용)
| 항목 | 값 |
|------|-----|
| URL | https://hanium.xcdww.com (tailnet 접속 시) |
| 포트 | 19900 (sandbox), `127.0.0.1:19900→8000` |
| 컨테이너 | `hanium` (Flask + gunicorn 2 workers) |
| 서비스 폴더 | `~/docker/hanium/` (compose + .env) |
| 빌드 컨텍스트 | `~/projects/accessible-kiosk` (Dockerfile 루트) |
| LLM 모드 env | `~/docker/hanium/.env` → `KIOSK_LLM_MODE` |

---

## 1. 진행 상황 (마일스톤)

- [x] M1 — UI 골격 (시작→주문→장바구니→결제→완료)
- [x] M2 — 접근성 (고대비/글자크기/낮은화면/음성, Web Speech TTS)
- [x] M3 — Mock LLM 자연어 주문 흐름
- [x] **웹 전환** — Flask 백엔드 + HTML/JS 프론트, 코어 재사용
- [x] **웹 배포** — Docker + Caddy + DNS, https://hanium.xcdww.com
- [x] **능동 추천 + 결제 자동조종** — action `recommend`(확인 후 담기) / `checkout`(물리 결제만 멈춤). mock 동작 검증, claude 코드 준비됨
- [ ] M4 — 실제 Claude API 연동 검증 (코드 완비, **키 미투입 → 미검증**)
- [ ] M5 — 세트 옵션(사이드/음료 선택) 다이얼로그
- [ ] M6 — 데모 시나리오/실패케이스 다듬기

### 에이전트 동작 모델 (현재)
| action | 트리거 예 | 동작 |
|--------|----------|------|
| `recommend` | "아무거나 추천", "뭐가 맛있어" | [추천]메뉴 제안 → **담지 않고** "담아드릴까요?" → 다음 '응/네'에 담음(프론트 로컬 확정) |
| `checkout` | "와퍼 세트 시키고 결제까지", "알아서 해줘" | items 담고 → 장바구니 음성통과 → 결제화면, **물리 결제(카드태그/화면탭)만 멈춤** → 완료 자동 |
| add/remove/update/confirm/clarify/answer | — | 기존 |

- `recommend` 확인-담기는 프론트(`app.js`)에서 직전 추천을 기억(`pendingRecommend`)했다가 '응/네/그래…'(정규식 `AFFIRM`)면 즉시 담음 → mock·claude 공통 결정적 동작.
- claude 모드는 `history`(최근 6턴)도 함께 전송해 맥락 유지.
- 물리 결제 시뮬: 결제화면에서 **화면 아무 곳 탭 / Enter·Space**로 완료(시각장애 사용자 TTS 안내). '취소' 버튼은 제외.

---

## 2. 보안 (Security)

### 현재 양호 ✅
- **Claude API 키는 서버에만**: `/api/order`가 서버에서 LLM 호출, 키가 프론트로 안 나감.
- **tailnet 전용**: 인터넷 비공개(DNS가 100.x CGNAT IP). 외부 노출 0.
- **127.0.0.1 바인딩** + Caddy만 `proxy`로 라우팅.
- 키는 `.env`(env_file)로만 주입, compose/로그 평문 없음.

### 점검/수정 필요 ⚠️
- [ ] **claude 모드 시 프롬프트 인젝션**: `/api/order`의 user text가 LLM에 직접 전달.
      system 프롬프트로 메뉴 범위 제한은 하지만, 악의적 입력 방어는 약함. (tailnet 전용이라 위험도 낮음)
- [ ] **엔드포인트 레이트리밋 없음**: `/api/order`·`/api/pay` 무제한 호출 가능 (DoS). tailnet이라 우선순위 낮음.
- [ ] **입력 검증 최소**: `/api/pay`의 `amount`를 서버가 신뢰(클라가 보냄). Fake라 무해하나, 실 결제 연동 시 **서버가 장바구니로 금액 재계산** 필수.
- [ ] **앱 자체 인증 없음**: 키오스크 특성상 OK. 단, 관리/디버그 엔드포인트 추가 시 보호 필요.

---

## 3. 개발 부채 (Tech Debt)

- [ ] **가격 로직 중복**: `src/domain/cart.py`(Python)와 `web/static/app.js`(JS)에 동일 계산 로직.
      메뉴 옵션/가격 규칙 바꾸면 **양쪽 동기화 필요**. → 향후 서버가 가격/소계 계산해 내려주는 방식으로 통합 고려.
- [ ] **장바구니 클라이언트 보유**: 서버 무상태(stateless) 선택. 멀티기기/세션복구 불가(데모엔 무방).
- [ ] **Qt UI 분기**: `src/ui/`(PyQt6)는 보존했지만 웹과 기능이 갈라짐. 캐노니컬 UI를 웹으로 확정할지 결정 필요.
- [ ] **Mock LLM 한계**: 키워드 매칭. "콜라"=코카콜라 등 별칭 일부만. 복잡한 발화엔 약함(실 Claude로 해결).
- [ ] **세트 옵션 미완**: 세트 선택해도 사이드/음료를 못 고름(기본값). M5에서 다이얼로그 필요.
- [ ] **웹 레이어 테스트 없음**: 도메인/Mock은 수동 검증함. `web/app.py` 자동 테스트 부재.
- [ ] **compose 빌드 컨텍스트가 절대경로**: `~/docker/hanium/docker-compose.yml`이 `/home/damnboy/projects/...` 하드코딩. 프로젝트 이동 시 깨짐.

### ⚠️ 운영 함정 (배포 시 기억할 것)
- **Caddyfile은 단일 파일 바인드 마운트(`./Caddyfile:...:ro`)** — 편집하면 inode가 바뀌어
  `caddy reload`가 "config is unchanged"로 옛 파일을 본다. 라우트 추가 후엔
  **`cd ~/docker/caddy && docker compose up -d --force-recreate`** 로 재마운트해야 반영됨.
  (이번 배포에서 실제로 겪음)

---

## 4. 확장 로드맵 (Phase 2+)

- [ ] **실시간 음성인식(STT)**: 마이크 → STT(Web Speech `SpeechRecognition` API 또는 Whisper/Vosk) → `/api/order`로 전달. 프론트 훅만 추가하면 기존 파이프라인 재사용.
- [ ] **실제 결제(PG)**: `/api/pay`를 PG사 SDK로 교체. 금액 서버 재계산 + 멱등성 키 필수.
- [ ] **키오스크 OS 이식**: (a) 웹 그대로 풀스크린 키오스크 모드(브라우저 락다운) 또는 (b) 보존된 Qt 코어 재사용해 네이티브 앱.
- [ ] **세트 구성 UI**: 버거+사이드+음료 선택 플로우.
- [ ] **다국어/수어 영상**: 외국인·청각장애 확장.
- [ ] **메뉴 관리(admin)**: `menu.json` 편집 UI.

---

## 5. 운영 명령 (자주 쓰는 것)

```bash
# 코드 수정 후 재배포 (이미지 리빌드)
cd ~/docker/hanium && docker compose up -d --build

# 로그 / 상태
docker logs hanium --tail 30 ; docker ps --filter name=hanium

# 로컬 검증 (Caddy 거치지 않고)
curl -sf http://127.0.0.1:19900/healthz

# tailnet 검증
curl -sf https://hanium.xcdww.com/healthz

# LLM 모드 전환: ~/docker/hanium/.env 편집 후
#   KIOSK_LLM_MODE=claude  +  ANTHROPIC_API_KEY=sk-ant-...
docker compose -f ~/docker/hanium/docker-compose.yml up -d   # env 반영 재기동

# Caddyfile 수정했는데 반영 안 될 때(inode 함정)
cd ~/docker/caddy && docker compose up -d --force-recreate
```

---

## 6. 세션 로그

### 2026-06-22
- 명세서(`SPEC.md`) 확정: 버거킹 / 오프라인→웹 / 세로형 / 마우스키보드.
- PyQt6 데모 골격(M1~M5) 구현 → **웹(Flask+JS)으로 전환**.
- 메뉴 12종(버거6/사이드3/음료3) `data/menu.json`.
- 재사용 코어(domain/services/config) 유지, 웹 레이어 `web/` 신설.
- Mock LLM 파서 버그 2건 수정(‘주세요’의 ‘세’ 오인식, ‘콜라’↔‘코카콜라’).
- **배포 완료**: hanium.xcdww.com (포트 19900, mock 모드). Caddy inode 함정 1건 겪고 recreate로 해결.
- 검증: /healthz·/api/menu·/api/order·/api/pay, https 200, 기존 memos 영향 없음.

### 2026-06-22 (2차)
- 사용자 피드백: "아무거나 추천"에 clarify만 나옴 → **능동 추천 + 결제 자동조종** 요구.
- 결정: 실제 Claude / 추천은 확인 후 담기 / 물리 결제만 멈추는 자동조종.
- 구현: action `recommend`·`checkout` 추가(schema·mock·claude 프롬프트), menu에 `recommended` 메타, claude에 `history` 전달, 프론트 추천확인·자동조종·물리결제 대기 로직.
- 검증: mock에서 추천/자동결제 정상, 배포본 https 200. (claude는 키 대기)

#### 다음 세션 할 일 (TODO)
1. **실제 Claude 키 투입 → claude 모드 검증 (M4)** ← 키만 넣으면 됨
2. 세트 옵션 다이얼로그 (M5) — 추천/자동결제 시 사이드·음료까지 제안
3. 가격 로직 중복 제거(서버 계산 일원화) 검토
4. recommend 확인-담기를 claude 멀티턴에 맡길지(현재 프론트 로컬 확정) 정리
