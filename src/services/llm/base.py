"""LLM 주문 서비스 인터페이스 및 공통 데이터 구조."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OrderItemAction:
    menu_id: str
    qty: int = 1
    options: dict[str, str] = field(default_factory=dict)


@dataclass
class OrderResult:
    """LLM이 사용자 발화를 해석한 결과.

    action:
      - add_item    : items 를 장바구니에 추가
      - remove_item : items 의 메뉴를 장바구니에서 제거
      - update_qty  : items 의 수량으로 갱신
      - recommend   : 능동 추천 (items=추천메뉴). 담지 말고 "담아드릴까요?" 식으로 확인 요청
      - checkout    : 주문+결제까지 자동 진행. items 있으면 먼저 담고 결제로 이동
      - confirm     : 장바구니(검토) 단계로 진행
      - clarify     : 되물음 (speech 만 사용)
      - answer      : 단순 안내/답변 (speech 만 사용)
    """
    action: str
    speech: str
    items: list[OrderItemAction] = field(default_factory=list)


# LLM이 따라야 할 JSON 스키마 (Structured Output / Mock 공통 참조)
ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "add_item", "remove_item", "update_qty",
                "recommend", "checkout", "confirm", "clarify", "answer",
            ],
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "menu_id": {"type": "string"},
                    "qty": {"type": "integer"},
                    "options": {"type": "object", "additionalProperties": {"type": "string"}},
                },
                "required": ["menu_id", "qty"],
                "additionalProperties": False,
            },
        },
        "speech": {"type": "string"},
    },
    "required": ["action", "items", "speech"],
    "additionalProperties": False,
}


class LLMService:
    """주문 해석 서비스 인터페이스.

    history: 직전 대화 턴 [{"role": "user"|"assistant", "content": str}, ...] (선택).
    """

    def interpret(
        self, user_text: str, cart_summary: str, history: list | None = None
    ) -> OrderResult:
        raise NotImplementedError
