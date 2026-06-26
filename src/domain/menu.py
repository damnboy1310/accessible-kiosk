"""메뉴 카탈로그 로딩 및 조회."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.config import MENU_PATH


@dataclass(frozen=True)
class MenuItem:
    id: str
    name: str
    category: str
    price: int
    description: str
    options: dict[str, list[str]] = field(default_factory=dict)
    combo_extra: int = 0
    size_extra: dict[str, int] = field(default_factory=dict)
    recommended: bool = False


@dataclass(frozen=True)
class Category:
    id: str
    name: str


class Menu:
    """메뉴 데이터 접근 객체."""

    def __init__(self, categories: list[Category], items: list[MenuItem]):
        self.categories = categories
        self.items = items
        self._by_id = {item.id: item for item in items}

    @classmethod
    def load(cls, path: Path = MENU_PATH) -> "Menu":
        raw = json.loads(path.read_text(encoding="utf-8"))
        categories = [Category(**c) for c in raw["categories"]]
        items = [
            MenuItem(
                id=i["id"],
                name=i["name"],
                category=i["category"],
                price=i["price"],
                description=i.get("description", ""),
                options=i.get("options", {}),
                combo_extra=i.get("combo_extra", 0),
                size_extra=i.get("size_extra", {}),
                recommended=i.get("recommended", False),
            )
            for i in raw["items"]
        ]
        return cls(categories, items)

    def get(self, item_id: str) -> MenuItem | None:
        return self._by_id.get(item_id)

    def by_category(self, category_id: str) -> list[MenuItem]:
        return [i for i in self.items if i.category == category_id]

    def recommended(self) -> list[MenuItem]:
        return [i for i in self.items if i.recommended]

    def find_by_name(self, name: str) -> MenuItem | None:
        """이름(부분 일치 포함)으로 메뉴 찾기 — LLM 결과 매칭 보조용."""
        name = name.strip()
        for item in self.items:
            if item.name == name:
                return item
        for item in self.items:
            if name and (name in item.name or item.name in name):
                return item
        return None

    def catalog_text(self) -> str:
        """LLM 시스템 프롬프트에 넣을 메뉴 요약 텍스트."""
        lines = []
        for cat in self.categories:
            lines.append(f"[{cat.name}]")
            for item in self.by_category(cat.id):
                opt = ""
                if item.options:
                    opt = " 옵션: " + ", ".join(
                        f"{k}({'/'.join(v)})" for k, v in item.options.items()
                    )
                rec = " [추천]" if item.recommended else ""
                lines.append(f"- {item.id} | {item.name} | {item.price}원{opt}{rec}")
        return "\n".join(lines)
