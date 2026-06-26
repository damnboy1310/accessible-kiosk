"""웹 키오스크 백엔드 (Flask).

기존 Python 코어(domain / services / config)를 그대로 재사용한다.
- 장바구니는 클라이언트(JS)가 보유 → 서버는 무상태(stateless).
- Claude API 키는 서버에만 존재 → 프론트로 노출되지 않음.

실행(로컬): python -m web.app   (컨테이너: gunicorn)
"""
from __future__ import annotations

import json

from flask import Flask, jsonify, request, send_from_directory

from src.config import ANTHROPIC_API_KEY, LLM_MODE, MENU_PATH
from src.domain.menu import Menu
from src.services.payment import FakePayment

app = Flask(__name__, static_folder="static", static_url_path="")

_menu = Menu.load()
_payment = FakePayment()


def _build_llm():
    if LLM_MODE == "claude" and ANTHROPIC_API_KEY:
        try:
            from src.services.llm.claude_client import ClaudeLLM

            print("[LLM] Claude API 모드")
            return ClaudeLLM(_menu)
        except Exception as exc:
            print(f"[LLM] Claude 초기화 실패, Mock으로 대체: {exc}")
    elif LLM_MODE == "claude":
        print("[LLM] claude 모드지만 ANTHROPIC_API_KEY 없음 → Mock으로 대체")

    from src.services.llm.mock_client import MockLLM

    print("[LLM] Mock 모드")
    return MockLLM(_menu)


_llm = _build_llm()


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/healthz")
def healthz():
    return jsonify(status="ok", llm_mode=LLM_MODE)


@app.get("/api/menu")
def api_menu():
    # 프론트가 가격/옵션을 계산할 수 있도록 원본 메뉴 JSON 그대로 제공
    return jsonify(json.loads(MENU_PATH.read_text(encoding="utf-8")))


@app.post("/api/order")
def api_order():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    cart_summary = data.get("cart_summary") or "장바구니 비어 있음"
    history = data.get("history") or []
    if not text:
        return jsonify(action="clarify", speech="주문 내용을 입력해 주세요.", items=[])
    result = _llm.interpret(text, cart_summary, history)
    return jsonify(
        action=result.action,
        speech=result.speech,
        items=[
            {"menu_id": a.menu_id, "qty": a.qty, "options": a.options}
            for a in result.items
        ],
    )


@app.post("/api/pay")
def api_pay():
    data = request.get_json(silent=True) or {}
    amount = int(data.get("amount") or 0)
    ok, order_no = _payment.charge(amount)
    return jsonify(success=ok, order_no=order_no)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
