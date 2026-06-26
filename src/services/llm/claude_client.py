"""실제 Claude API 기반 주문 해석.

Structured Output(output_config.format)으로 ORDER_SCHEMA 를 강제하여
항상 파싱 가능한 주문 액션을 받는다. 오류 시 clarify 로 안전하게 폴백.
"""
from __future__ import annotations

import json

from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.domain.menu import Menu
from src.services.llm.base import (
    ORDER_SCHEMA,
    LLMService,
    OrderItemAction,
    OrderResult,
)

_SYSTEM = """당신은 버거킹 키오스크의 주문 도우미입니다. 시각장애·지체장애 사용자가 음성으로 듣고 주문합니다.
- 아래 메뉴에 있는 항목만 처리합니다. items의 menu_id는 반드시 아래 목록의 id를 사용하세요.
- speech는 짧고 친절한 한국어 1~2문장(들을 안내문).

[action 선택 규칙]
- 메뉴를 담으려 함 → add_item
- 빼기/취소 → remove_item, 수량 변경 → update_qty
- "추천/아무거나/뭐가 맛있어/골라줘" 등 결정을 맡김 → **recommend**.
  [추천] 표시 메뉴 위주로 1~2개를 능동 제안하되, 담지 말고 "담아드릴까요?"처럼 확인을 요청하세요.
  (사용자가 '응/네/그래'로 답하면 그때 add_item)
- "결제까지 해줘/주문하고 결제/알아서 해줘/다 해줘" 등 끝까지 맡김 → **checkout**.
  주문할 메뉴가 같이 있으면 items에 넣으세요(담은 뒤 결제로 자동 진행됩니다).
- 단순히 "결제할게/주문 끝" (검토 원함) → confirm (장바구니로)
- 모호하면 clarify, 단순 안내는 answer.
- 옵션(단품/세트, 사이즈)이 꼭 필요하면 추측하지 말고 clarify로 되물으세요. 단, 추천/자동결제 맥락이면 합리적 기본값(세트)을 제안해도 됩니다.

[메뉴]
{catalog}
"""


class ClaudeLLM(LLMService):
    def __init__(self, menu: Menu):
        self.menu = menu
        import anthropic  # 지연 import — mock 모드에선 불필요

        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY or None)
        self.system = _SYSTEM.format(catalog=menu.catalog_text())

    def interpret(self, user_text, cart_summary, history=None) -> OrderResult:
        try:
            messages = []
            for turn in (history or [])[-6:]:
                role = turn.get("role")
                content = (turn.get("content") or "").strip()
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
            messages.append({
                "role": "user",
                "content": f"현재 장바구니: {cart_summary}\n사용자 발화: {user_text}",
            })
            resp = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=self.system,
                output_config={"format": {"type": "json_schema", "schema": ORDER_SCHEMA}},
                messages=messages,
            )
            text = next(b.text for b in resp.content if b.type == "text")
            data = json.loads(text)
            return OrderResult(
                action=data["action"],
                speech=data.get("speech", ""),
                items=[
                    OrderItemAction(
                        menu_id=i["menu_id"],
                        qty=int(i.get("qty", 1)),
                        options=i.get("options", {}) or {},
                    )
                    for i in data.get("items", [])
                ],
            )
        except Exception as exc:
            print(f"[ClaudeLLM] 오류, clarify 폴백: {exc}")
            return OrderResult(
                action="clarify",
                speech="죄송해요, 다시 한 번 말씀해 주시겠어요?",
            )
