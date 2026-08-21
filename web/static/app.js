/* 버거킹 접근성 키오스크 — 프론트엔드 로직
 * 장바구니는 클라이언트 보유(서버 무상태). 가격 계산은 cart.py 로직을 미러링한다.
 * (중복은 알려진 기술부채 — docs/DEVLOG.md 참고)
 */
"use strict";

const App = {
  menu: null,          // {currency, categories, items}
  itemsById: {},
  cart: [],            // [{id, qty, options}]
  currentCat: null,
  orderNo: null,
  history: [],         // 대화 맥락 [{role, content}]
  pendingRecommend: null, // 추천 후 확인 대기 중인 items
  autopilot: false,    // "결제까지" 자동 진행 중
  paying: false,       // 결제 처리 중복 방지
  settings: { highContrast: false, fontScale: 1, lowPosition: false, voice: true, orient: "auto" },
};

const AFFIRM = /(^|\s)(응|네|예|그래|좋아|좋아요|담아|담아줘|해줘|그걸로|오케이|콜|ok)($|\s|요|\.)/i;
const NEGATE = /(아니|괜찮|싫|안돼|안 돼|노노|취소|다른)/;

/* ---------- TTS (Web Speech API) ---------- */
function speak(text) {
  if (!App.settings.voice || !text) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "ko-KR";
    u.rate = 1.05;
    window.speechSynthesis.speak(u);
  } catch (e) { /* 미지원 브라우저 무시 */ }
}

/* ---------- 화면 방향(세로/가로) ----------
 * 우선순위: URL 파라미터(?orient=) > localStorage > auto(화면 방향 자동 감지)
 * CSS는 html[data-orient]에 들어가는 "실제 적용된" 방향만 본다.
 */
const ORIENT_MODES = ["auto", "portrait", "landscape"];
const ORIENT_LABEL = { auto: "화면 자동", portrait: "화면 세로", landscape: "화면 가로" };
const ORIENT_KEY = "kiosk.orient";
const portraitMQ = window.matchMedia("(orientation: portrait)");

function effectiveOrient() {
  if (App.settings.orient !== "auto") return App.settings.orient;
  return portraitMQ.matches ? "portrait" : "landscape";
}

function applyOrient() {
  const eff = effectiveOrient();
  document.documentElement.dataset.orient = eff;
  const btn = document.getElementById("btn-orient");
  if (!btn) return;
  btn.textContent = ORIENT_LABEL[App.settings.orient];
  btn.setAttribute("aria-pressed", String(App.settings.orient !== "auto"));
  btn.title = `현재 ${eff === "portrait" ? "세로" : "가로"} 레이아웃`;
}

function setOrient(mode, announce = false) {
  App.settings.orient = ORIENT_MODES.includes(mode) ? mode : "auto";
  try { localStorage.setItem(ORIENT_KEY, App.settings.orient); } catch (e) { /* 사생활 보호 모드 */ }
  applyOrient();
  if (!announce) return;
  const eff = effectiveOrient() === "portrait" ? "세로" : "가로";
  speak(App.settings.orient === "auto"
    ? `화면 방향 자동. 현재 ${eff} 화면입니다.`
    : `화면을 ${eff}로 바꿨습니다.`);
}

function initOrient() {
  let saved = null;
  try { saved = localStorage.getItem(ORIENT_KEY); } catch (e) { /* 무시 */ }
  const param = new URLSearchParams(location.search).get("orient");
  setOrient(param || saved || "auto");

  // auto일 때만 실제 화면 방향 변화를 따라간다
  const onChange = () => { if (App.settings.orient === "auto") applyOrient(); };
  if (portraitMQ.addEventListener) portraitMQ.addEventListener("change", onChange);
  else portraitMQ.addListener(onChange);   // 구형 브라우저
  window.addEventListener("resize", onChange);
}

/* ---------- 화면 전환 ---------- */
function go(name) {
  const leaving = document.body.dataset.screen;
  disarmPhysical();
  // 결제 화면을 완료(done) 외의 경로로 떠나면 = 취소 → 자동조종 해제
  if (leaving === "payment" && name !== "done") App.autopilot = false;
  if (name === "start") App.autopilot = false;

  document.querySelectorAll(".screen").forEach((s) => {
    s.classList.toggle("active", s.dataset.name === name);
  });
  document.body.dataset.screen = name;
  onEnter(name);
}

function onEnter(name) {
  if (name === "start") {
    App.history = [];
    App.pendingRecommend = null;
    const log = document.getElementById("chat-log");
    if (log) log.innerHTML = "";
    speak("환영합니다. 주문을 시작하려면 주문 시작하기 버튼을 누르세요.");
  } else if (name === "order") {
    renderCartCount();
    speak("메뉴를 직접 고르거나, 말로 주문 탭에서 원하시는 메뉴를 입력하세요.");
  } else if (name === "cart") {
    renderCart();
    speak(cartSummary());
  } else if (name === "payment") {
    App.paying = false;
    document.getElementById("pay-amount").textContent = cartTotal().toLocaleString();
    document.querySelectorAll("[data-pay]").forEach((b) => (b.disabled = false));
    if (App.autopilot) {
      // 물리 결제 단계 — 여기서만 멈추고 사용자의 물리적 동작을 기다림
      document.getElementById("pay-status").textContent = "카드를 대거나 화면을 한 번 누르세요";
      speak(`결제하실 금액은 ${cartTotal().toLocaleString()}원입니다. 카드를 단말기에 대거나, 화면을 한 번 누르면 결제가 완료됩니다.`);
      armPhysical();
    } else {
      document.getElementById("pay-status").textContent = "결제 수단을 선택하세요";
      speak(`결제하실 금액은 ${cartTotal().toLocaleString()}원입니다. 결제 수단을 선택하세요.`);
    }
  } else if (name === "done") {
    document.getElementById("order-no").textContent = App.orderNo ?? "-";
    speak(`주문이 완료되었습니다. 주문번호는 ${App.orderNo}번입니다.`);
    setTimeout(() => { if (document.body.dataset.screen === "done") { App.cart = []; go("start"); } }, 15000);
  }
}

/* ---------- 가격/장바구니 (cart.py 미러링) ---------- */
function unitPrice(item, options) {
  let p = item.price;
  if (options && options.combo === "세트") p += item.combo_extra || 0;
  if (options && options.size && item.size_extra && item.size_extra[options.size] != null) {
    p += item.size_extra[options.size];
  }
  return p;
}
function lineSubtotal(line) {
  return unitPrice(App.itemsById[line.id], line.options) * line.qty;
}
function cartTotal() { return App.cart.reduce((s, l) => s + lineSubtotal(l), 0); }
function cartCount() { return App.cart.reduce((s, l) => s + l.qty, 0); }

function sameOptions(a, b) {
  const ka = Object.keys(a || {}).sort(), kb = Object.keys(b || {}).sort();
  if (ka.length !== kb.length) return false;
  return ka.every((k) => a[k] === b[k]);
}

function cartAdd(id, qty = 1, options = {}) {
  const item = App.itemsById[id];
  if (!item) return;
  const found = App.cart.find((l) => l.id === id && sameOptions(l.options, options));
  if (found) found.qty += qty;
  else App.cart.push({ id, qty, options });
  // 가로 모드에서는 장바구니 패널이 상시 노출되므로 담는 즉시 갱신해야 한다
  afterCartChange();
}
function cartRemove(id) { App.cart = App.cart.filter((l) => l.id !== id); }
function cartUpdateQty(id, qty) {
  const l = App.cart.find((x) => x.id === id);
  if (!l) return;
  if (qty <= 0) cartRemove(id); else l.qty = qty;
}

function describeLine(line) {
  const item = App.itemsById[line.id];
  const opt = Object.values(line.options || {});
  const optTxt = opt.length ? ` (${opt.join(", ")})` : "";
  return `${item.name}${optTxt} ${line.qty}개`;
}
function cartSummary() {
  if (!App.cart.length) return "장바구니가 비어 있습니다.";
  return App.cart.map(describeLine).join(", ") + `. 총 ${cartTotal().toLocaleString()}원.`;
}

/* ---------- 렌더링 ---------- */
function renderCartCount() {
  document.getElementById("order-cart-count").textContent = cartCount();
}

function renderCategories() {
  const wrap = document.getElementById("cat-filter");
  wrap.innerHTML = "";
  const all = [{ id: null, name: "전체" }, ...App.menu.categories];
  all.forEach((c) => {
    const b = document.createElement("button");
    b.textContent = c.name;
    b.classList.toggle("active", c.id === App.currentCat);
    b.onclick = () => { App.currentCat = c.id; renderCategories(); renderMenu(); };
    wrap.appendChild(b);
  });
}

function renderMenu() {
  const grid = document.getElementById("menu-grid");
  grid.innerHTML = "";
  App.menu.items
    .filter((i) => !App.currentCat || i.category === App.currentCat)
    .forEach((item) => {
      const card = document.createElement("button");
      card.className = "menu-card";
      card.innerHTML =
        `<span class="name">${item.name}</span>` +
        `<span class="price">${item.price.toLocaleString()}원</span>` +
        `<span class="desc">${item.description || ""}</span>`;
      card.onclick = () => {
        const opts = item.options && item.options.combo ? { combo: "단품" } : {};
        cartAdd(item.id, 1, opts);
        renderCartCount();
        speak(`${item.name} 담았습니다. 현재 ${cartCount()}개.`);
      };
      card.onfocus = () => speak(`${item.name}, ${item.price.toLocaleString()}원. ${item.description || ""}`);
      grid.appendChild(card);
    });
}

function renderCart() {
  const list = document.getElementById("cart-list");
  list.innerHTML = "";
  if (!App.cart.length) {
    list.innerHTML = '<p class="empty">장바구니가 비어 있습니다.</p>';
  } else {
    App.cart.forEach((line) => {
      const row = document.createElement("div");
      row.className = "cart-line";
      const item = App.itemsById[line.id];
      const opt = Object.values(line.options || {});
      row.innerHTML =
        `<div class="info"><strong>${item.name}</strong>` +
        (opt.length ? ` <small>(${opt.join(", ")})</small>` : "") +
        `<br>${lineSubtotal(line).toLocaleString()}원</div>`;
      const minus = mkQtyBtn("−", () => { cartUpdateQty(line.id, line.qty - 1); afterCartChange(); });
      const qty = document.createElement("span");
      qty.textContent = line.qty;
      const plus = mkQtyBtn("+", () => { cartUpdateQty(line.id, line.qty + 1); afterCartChange(); });
      row.append(minus, qty, plus);
      list.appendChild(row);
    });
  }
  document.getElementById("cart-total").textContent = cartTotal().toLocaleString();
}
function mkQtyBtn(label, fn) {
  const b = document.createElement("button");
  b.className = "qty-btn"; b.textContent = label; b.onclick = fn;
  return b;
}
function afterCartChange() { renderCart(); renderCartCount(); }

/* ---------- 대화형 주문 (LLM) ---------- */
function addBubble(text, who) {
  const log = document.getElementById("chat-log");
  const div = document.createElement("div");
  div.className = `bubble ${who}`;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function sendChat(text) {
  addBubble(text, "user");
  App.history.push({ role: "user", content: text });

  // 추천 확인 대기 중이면 간단한 예/아니오를 로컬에서 즉시 처리
  if (App.pendingRecommend) {
    if (AFFIRM.test(text)) {
      const items = App.pendingRecommend;
      App.pendingRecommend = null;
      items.forEach((a) => cartAdd(a.menu_id, a.qty || 1, a.options || {}));
      renderCartCount();
      botSay("담았어요. 더 필요하신가요?");
      return;
    }
    if (NEGATE.test(text)) {
      App.pendingRecommend = null;
      botSay("알겠습니다. 원하시는 메뉴를 말씀해 주세요.");
      return;
    }
    App.pendingRecommend = null; // 그 외엔 일반 흐름으로
  }

  try {
    const res = await fetch("/api/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, cart_summary: cartSummary(), history: App.history.slice(-6) }),
    });
    const data = await res.json();
    applyOrderResult(data);
  } catch (e) {
    botSay("연결 오류가 발생했어요. 다시 시도해 주세요.");
  }
}

function botSay(text) {
  addBubble(text, "bot");
  App.history.push({ role: "assistant", content: text });
  speak(text);
}

function applyOrderResult(r) {
  if (r.action === "add_item") {
    (r.items || []).forEach((a) => cartAdd(a.menu_id, a.qty || 1, a.options || {}));
  } else if (r.action === "remove_item") {
    (r.items || []).forEach((a) => cartRemove(a.menu_id));
  } else if (r.action === "update_qty") {
    (r.items || []).forEach((a) => cartUpdateQty(a.menu_id, a.qty || 0));
  } else if (r.action === "recommend") {
    // 담지 않고 확인 대기 (다음 발화의 예/아니오로 결정)
    App.pendingRecommend = (r.items || []).length ? r.items : null;
  }
  renderCartCount();
  botSay(r.speech);

  if (r.action === "confirm") {
    go("cart");
  } else if (r.action === "checkout") {
    runCheckout(r.items || []);
  }
}

/* ---------- 결제 자동조종 (물리 결제 단계만 멈춤) ---------- */
function runCheckout(items) {
  items.forEach((a) => cartAdd(a.menu_id, a.qty || 1, a.options || {}));
  renderCartCount();
  if (!App.cart.length) {
    botSay("장바구니가 비어 있어요. 먼저 메뉴를 골라 주세요.");
    return;
  }
  App.autopilot = true;
  go("cart"); // 장바구니 음성 안내(자동 통과)
  setTimeout(() => { if (App.autopilot) go("payment"); }, 2200);
}

/* 결제 화면에서 '물리적 동작'을 기다렸다가 한 번의 입력으로 완료 */
function armPhysical() {
  disarmPhysical();
  const section = document.querySelector('[data-name="payment"]');
  // 취소(data-go) 버튼 클릭은 결제로 처리하지 않음 — 그 외 화면 어디든 탭하면 결제 완료
  App._physClick = (e) => { if (e.target.closest("[data-go]")) return; completePhysical(); };
  App._physKey = (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    if (document.activeElement && document.activeElement.closest && document.activeElement.closest("[data-go]")) return;
    e.preventDefault();
    completePhysical();
  };
  section.addEventListener("click", App._physClick);
  document.addEventListener("keydown", App._physKey);
}
function disarmPhysical() {
  const section = document.querySelector('[data-name="payment"]');
  if (App._physClick) section.removeEventListener("click", App._physClick);
  if (App._physKey) document.removeEventListener("keydown", App._physKey);
  App._physClick = App._physKey = null;
}
function completePhysical() {
  disarmPhysical();
  pay();
}

/* ---------- 접근성 토글 ---------- */
function applySettings() {
  document.body.classList.toggle("high-contrast", App.settings.highContrast);
  document.body.classList.toggle("low-position", App.settings.lowPosition);
  document.documentElement.style.setProperty("--font-scale", App.settings.fontScale);
  document.getElementById("btn-contrast").setAttribute("aria-pressed", App.settings.highContrast);
  document.getElementById("btn-low").setAttribute("aria-pressed", App.settings.lowPosition);
  document.getElementById("btn-voice").setAttribute("aria-pressed", App.settings.voice);
  document.getElementById("btn-font").textContent = `글자 ${Math.round(App.settings.fontScale * 100)}%`;
  document.getElementById("btn-voice").textContent = App.settings.voice ? "음성 ON" : "음성 OFF";
}

/* ---------- 결제 ---------- */
async function pay() {
  if (App.paying) return;          // 중복 방지 (자동조종 탭 + 버튼)
  App.paying = true;
  disarmPhysical();
  document.querySelectorAll("[data-pay]").forEach((b) => (b.disabled = true));
  document.getElementById("pay-status").textContent = "결제 중입니다...";
  speak("결제 중입니다. 잠시만 기다려 주세요.");
  await new Promise((r) => setTimeout(r, 1500));
  try {
    const res = await fetch("/api/pay", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: cartTotal() }),
    });
    const data = await res.json();
    if (data.success) {
      App.orderNo = data.order_no;
      App.cart = [];
      App.autopilot = false;
      App.history = [];
      go("done");
    } else {
      document.getElementById("pay-status").textContent = "결제에 실패했습니다. 다시 시도해 주세요.";
      speak("결제에 실패했습니다.");
      document.querySelectorAll("[data-pay]").forEach((b) => (b.disabled = false));
      App.paying = false;
    }
  } catch (e) {
    document.getElementById("pay-status").textContent = "결제 처리 오류.";
    document.querySelectorAll("[data-pay]").forEach((b) => (b.disabled = false));
    App.paying = false;
  }
}

/* ---------- 초기화/이벤트 바인딩 ---------- */
async function init() {
  const res = await fetch("/api/menu");
  App.menu = await res.json();
  App.menu.items.forEach((i) => (App.itemsById[i.id] = i));
  renderCategories();
  renderMenu();

  // 네비게이션
  document.querySelectorAll("[data-go]").forEach((b) => {
    b.addEventListener("click", () => {
      const target = b.dataset.go;
      if (target === "payment" && App.cart.length === 0) {
        speak("장바구니가 비어 있습니다. 먼저 메뉴를 담아주세요.");
        return;
      }
      if (target === "start") App.cart = [];
      go(target);
    });
  });

  // 탭
  document.querySelectorAll(".tab").forEach((t) => {
    t.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
      t.classList.add("active");
      document.querySelectorAll(".tab-panel").forEach((p) => {
        p.classList.toggle("hidden", p.dataset.panel !== t.dataset.tab);
      });
    });
  });

  // 대화형 주문 폼
  document.getElementById("chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendChat(text);
  });

  // 결제 버튼
  document.querySelectorAll("[data-pay]").forEach((b) => b.addEventListener("click", pay));

  // 접근성 토글
  document.getElementById("btn-contrast").onclick = () => {
    App.settings.highContrast = !App.settings.highContrast; applySettings();
    speak("고대비 모드를 변경했습니다.");
  };
  document.getElementById("btn-font").onclick = () => {
    const steps = [1, 1.25, 1.5, 2];
    const i = steps.indexOf(App.settings.fontScale);
    App.settings.fontScale = steps[(i + 1) % steps.length];
    applySettings();
    speak(`글자 크기 ${Math.round(App.settings.fontScale * 100)} 퍼센트.`);
  };
  document.getElementById("btn-low").onclick = () => {
    App.settings.lowPosition = !App.settings.lowPosition; applySettings();
    speak("화면 배치를 변경했습니다.");
  };
  document.getElementById("btn-voice").onclick = () => {
    App.settings.voice = !App.settings.voice; applySettings();
    if (App.settings.voice) speak("음성 안내를 켰습니다.");
  };
  document.getElementById("btn-orient").onclick = () => {
    const i = ORIENT_MODES.indexOf(App.settings.orient);
    setOrient(ORIENT_MODES[(i + 1) % ORIENT_MODES.length], true);
  };

  initOrient();
  applySettings();
  go("start");
}

document.addEventListener("DOMContentLoaded", init);
