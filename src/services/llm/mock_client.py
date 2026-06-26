"""규칙 기반 Mock LLM — API 키 없이 주문 흐름을 시연한다.

완벽한 자연어 이해가 아니라, 메뉴 이름 + 한국어 수량 단어를 단순 매칭한다.
"""
from __future__ import annotations

import re

from src.domain.menu import Menu
from src.services.llm.base import LLMService, OrderItemAction, OrderResult

# 숫자 단어 → 값. "주세요"의 '세' 같은 오인식을 막기 위해
# 단어 뒤에 수량 단위(개/잔/단/봉)가 올 때만 인정한다.
_NUM_WORDS = {
    "하나": 1, "한": 1, "둘": 2, "두": 2, "셋": 3, "세": 3,
    "넷": 4, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8,
}

# Mock 데모용 별칭 (실제 Claude는 불필요)
_ALIASES = {
    "콜라": "coke",
    "제로": "coke_zero",
    "사이다": "sprite",
    "스프라이트": "sprite",
    "너겟": "nuggets",
    "감튀": "fries",
}


def _parse_qty(text: str, name_pos: int) -> int:
    """메뉴 이름 뒤쪽에서 수량을 추정."""
    tail = text[name_pos:name_pos + 8]  # 바로 뒤 일부만 본다
    m = re.search(r"(\d+)\s*(개|잔|단|봉|세트)?", tail)
    if m:
        return max(1, int(m.group(1)))
    for word, n in _NUM_WORDS.items():
        if re.search(rf"{word}\s*(개|잔|단|봉)", tail):
            return n
    return 1


class MockLLM(LLMService):
    def __init__(self, menu: Menu):
        self.menu = menu

    def _recommend(self) -> OrderResult:
        recs = self.menu.recommended() or self.menu.items[:1]
        top = recs[0]
        opts = {"combo": "세트"} if "combo" in top.options else {}
        price = top.price + (top.combo_extra if opts.get("combo") == "세트" else 0)
        suffix = " 세트" if opts.get("combo") == "세트" else ""
        return OrderResult(
            action="recommend",
            items=[OrderItemAction(menu_id=top.id, qty=1, options=opts)],
            speech=f"오늘은 {top.name}{suffix}가 가장 인기예요. {price:,}원입니다. 담아드릴까요?",
        )

    def interpret(self, user_text, cart_summary, history=None) -> OrderResult:
        text = user_text.strip()
        low = text.replace(" ", "")

        # 능동 추천 의도
        if any(k in low for k in ["추천", "아무거나", "뭐가맛있", "뭐먹", "골라줘", "인기"]):
            return self._recommend()

        # "결제까지" 자동 진행 의도 (주문 + 결제 한번에)
        wants_auto_checkout = any(
            k in low for k in ["결제까지", "결제해줘", "주문하고결제", "바로결제", "다해줘", "알아서해"]
        )

        # 단순 결제/완료 의도 (장바구니 검토로)
        if not wants_auto_checkout and any(
            k in low for k in ["결제", "주문완료", "다됐", "그만", "끝"]
        ):
            return OrderResult(action="confirm", speech="장바구니를 확인하겠습니다.")

        # 삭제 의도
        is_remove = any(k in low for k in ["빼", "취소", "삭제", "지워"])

        found: list[OrderItemAction] = []
        seen: set[str] = set()
        for item in self.menu.items:
            pos = text.find(item.name)
            if pos == -1:
                # 별칭으로도 시도
                alias_pos = -1
                for alias, mid in _ALIASES.items():
                    if mid == item.id and alias in text:
                        alias_pos = text.find(alias) + len(alias)
                        break
                if alias_pos == -1:
                    continue
                pos = alias_pos - len(item.name)  # qty 추정 기준 위치 보정
                qty = _parse_qty(text, alias_pos)
            else:
                qty = _parse_qty(text, pos + len(item.name))

            if item.id in seen:
                continue
            seen.add(item.id)
            options: dict[str, str] = {}
            if "세트" in low and "combo" in item.options:
                options["combo"] = "세트"
            elif "단품" in low and "combo" in item.options:
                options["combo"] = "단품"
            found.append(OrderItemAction(menu_id=item.id, qty=qty, options=options))

        if not found:
            if wants_auto_checkout:
                # 메뉴 언급 없이 "결제까지 해줘" → 장바구니 그대로 자동 결제
                return OrderResult(
                    action="checkout",
                    speech="바로 결제로 진행할게요.",
                )
            return OrderResult(
                action="clarify",
                speech="죄송해요, 어떤 메뉴를 원하시는지 잘 못 들었어요. "
                       "예를 들어 '와퍼 세트 하나'처럼 말씀해 주세요. "
                       "추천을 원하시면 '아무거나 추천'이라고 해보세요.",
            )

        if is_remove:
            names = ", ".join(self.menu.get(a.menu_id).name for a in found)
            return OrderResult(
                action="remove_item",
                items=found,
                speech=f"{names}을(를) 장바구니에서 뺐어요.",
            )

        names = ", ".join(
            f"{self.menu.get(a.menu_id).name} {a.qty}개" for a in found
        )
        if wants_auto_checkout:
            return OrderResult(
                action="checkout",
                items=found,
                speech=f"{names} 담고 바로 결제로 진행할게요.",
            )
        return OrderResult(
            action="add_item",
            items=found,
            speech=f"{names} 담았어요. 더 주문하시겠어요?",
        )
