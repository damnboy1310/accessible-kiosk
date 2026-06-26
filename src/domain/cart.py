"""장바구니 모델."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.menu import Menu, MenuItem


@dataclass
class CartLine:
    item: MenuItem
    qty: int
    options: dict[str, str] = field(default_factory=dict)

    @property
    def unit_price(self) -> int:
        price = self.item.price
        if self.options.get("combo") == "세트":
            price += self.item.combo_extra
        size = self.options.get("size")
        if size and size in self.item.size_extra:
            price += self.item.size_extra[size]
        return price

    @property
    def subtotal(self) -> int:
        return self.unit_price * self.qty

    def describe(self) -> str:
        opt = ""
        if self.options:
            opt = " (" + ", ".join(self.options.values()) + ")"
        return f"{self.item.name}{opt} {self.qty}개"


class Cart:
    def __init__(self, menu: Menu):
        self.menu = menu
        self.lines: list[CartLine] = []

    def _key(self, item_id: str, options: dict[str, str]) -> tuple:
        return (item_id, tuple(sorted(options.items())))

    def add(self, item_id: str, qty: int = 1, options: dict[str, str] | None = None) -> bool:
        item = self.menu.get(item_id)
        if item is None:
            return False
        options = options or {}
        for line in self.lines:
            if self._key(line.item.id, line.options) == self._key(item_id, options):
                line.qty += qty
                return True
        self.lines.append(CartLine(item=item, qty=qty, options=options))
        return True

    def remove(self, item_id: str) -> bool:
        before = len(self.lines)
        self.lines = [l for l in self.lines if l.item.id != item_id]
        return len(self.lines) < before

    def update_qty(self, item_id: str, qty: int) -> bool:
        for line in self.lines:
            if line.item.id == item_id:
                if qty <= 0:
                    return self.remove(item_id)
                line.qty = qty
                return True
        return False

    def clear(self) -> None:
        self.lines = []

    @property
    def total(self) -> int:
        return sum(line.subtotal for line in self.lines)

    @property
    def count(self) -> int:
        return sum(line.qty for line in self.lines)

    def is_empty(self) -> bool:
        return not self.lines

    def summary_text(self) -> str:
        if self.is_empty():
            return "장바구니가 비어 있습니다."
        parts = [line.describe() for line in self.lines]
        return ", ".join(parts) + f". 총 {self.total:,}원."
