"""F-2/F-3 주문 화면: 메뉴 탐색(터치) + 대화형 주문(LLM) 두 경로."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.llm.base import OrderResult


class OrderScreen(QWidget):
    def __init__(self, ctx, nav):
        super().__init__()
        self.ctx = ctx
        self.nav = nav
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        header = QLabel("무엇을 주문할까요?")
        header.setObjectName("title")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tabs = QTabWidget()
        tabs.addTab(self._build_menu_tab(), "메뉴 보기")
        tabs.addTab(self._build_chat_tab(), "말로 주문")

        # 하단 고정 영역 (장바구니로 이동) — 저위치 모드 대응
        self.cart_btn = QPushButton("장바구니 보기")
        self.cart_btn.setObjectName("primary")
        self.cart_btn.clicked.connect(lambda: self.nav("cart"))

        if self.ctx.settings.low_position:
            # 휠체어 모드: 조작 영역을 아래로
            root.addWidget(tabs, stretch=1)
            root.addWidget(header)
            root.addWidget(self.cart_btn)
        else:
            root.addWidget(header)
            root.addWidget(tabs, stretch=1)
            root.addWidget(self.cart_btn)

    # ---- 메뉴 탐색 탭 ----
    def _build_menu_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self.menu_list = QListWidget()
        for item in self.ctx.menu.items:
            li = QListWidgetItem(f"{item.name}  ·  {item.price:,}원")
            li.setData(Qt.ItemDataRole.UserRole, item.id)
            self.menu_list.addItem(li)
        self.menu_list.currentItemChanged.connect(self._announce_item)
        lay.addWidget(self.menu_list)

        add_btn = QPushButton("선택 메뉴 담기")
        add_btn.clicked.connect(self._add_selected)
        lay.addWidget(add_btn)
        return w

    def _announce_item(self, current: QListWidgetItem | None) -> None:
        if current is None:
            return
        item = self.ctx.menu.get(current.data(Qt.ItemDataRole.UserRole))
        if item:
            self.ctx.speak(f"{item.name}, {item.price:,}원. {item.description}")

    def _add_selected(self) -> None:
        current = self.menu_list.currentItem()
        if current is None:
            self.ctx.speak("먼저 메뉴를 선택해 주세요.")
            return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        item = self.ctx.menu.get(item_id)
        options = {"combo": "단품"} if "combo" in item.options else {}
        self.ctx.cart.add(item_id, qty=1, options=options)
        self.ctx.speak(f"{item.name} 담았습니다. 현재 {self.ctx.cart.count}개.")

    # ---- 대화형 주문 탭 ----
    def _build_chat_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        guide = QLabel("예: \"와퍼 세트 하나랑 콜라 주세요\"")
        guide.setObjectName("subtitle")
        guide.setWordWrap(True)
        lay.addWidget(guide)

        self.chat_log = QLabel("")
        self.chat_log.setWordWrap(True)
        self.chat_log.setMinimumHeight(120)
        self.chat_log.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.addWidget(self.chat_log, stretch=1)

        row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("주문 내용을 입력하세요")
        self.chat_input.returnPressed.connect(self._send_chat)
        send_btn = QPushButton("보내기")
        send_btn.clicked.connect(self._send_chat)
        row.addWidget(self.chat_input, stretch=1)
        row.addWidget(send_btn)
        lay.addLayout(row)
        return w

    def _send_chat(self) -> None:
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self._append_log(f"나: {text}")
        result = self.ctx.llm.interpret(text, self.ctx.cart.summary_text())
        self._apply_result(result)

    def _append_log(self, line: str) -> None:
        prev = self.chat_log.text()
        self.chat_log.setText((prev + "\n" + line).strip())

    def _apply_result(self, result: OrderResult) -> None:
        if result.action == "add_item":
            for a in result.items:
                self.ctx.cart.add(a.menu_id, a.qty, a.options)
        elif result.action == "remove_item":
            for a in result.items:
                self.ctx.cart.remove(a.menu_id)
        elif result.action == "update_qty":
            for a in result.items:
                self.ctx.cart.update_qty(a.menu_id, a.qty)
        elif result.action == "confirm":
            self._append_log(f"키오스크: {result.speech}")
            self.ctx.speak(result.speech)
            self.nav("cart")
            return

        self._append_log(f"키오스크: {result.speech}")
        self.ctx.speak(result.speech)

    def on_enter(self) -> None:
        self.ctx.speak(
            "메뉴를 직접 고르거나, 말로 주문 탭에서 원하시는 메뉴를 입력하세요."
        )
