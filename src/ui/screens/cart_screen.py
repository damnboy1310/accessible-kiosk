"""F-4 장바구니 화면."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CartScreen(QWidget):
    def __init__(self, ctx, nav):
        super().__init__()
        self.ctx = ctx
        self.nav = nav
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("장바구니")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._announce_line)
        root.addWidget(self.list, stretch=1)

        self.total_label = QLabel("총 0원")
        self.total_label.setObjectName("title")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self.total_label)

        row = QHBoxLayout()
        remove_btn = QPushButton("선택 빼기")
        remove_btn.clicked.connect(self._remove_selected)
        back_btn = QPushButton("계속 주문")
        back_btn.clicked.connect(lambda: self.nav("order"))
        row.addWidget(remove_btn)
        row.addWidget(back_btn)
        root.addLayout(row)

        pay_btn = QPushButton("결제하기")
        pay_btn.setObjectName("primary")
        pay_btn.clicked.connect(self._goto_pay)
        root.addWidget(pay_btn)

    def _refresh(self) -> None:
        self.list.clear()
        for line in self.ctx.cart.lines:
            li = QListWidgetItem(f"{line.describe()}  ·  {line.subtotal:,}원")
            li.setData(Qt.ItemDataRole.UserRole, line.item.id)
            self.list.addItem(li)
        self.total_label.setText(f"총 {self.ctx.cart.total:,}원")

    def _announce_line(self, current: QListWidgetItem | None) -> None:
        if current is not None:
            self.ctx.speak(current.text().replace("·", ","))

    def _remove_selected(self) -> None:
        current = self.list.currentItem()
        if current is None:
            self.ctx.speak("뺄 항목을 선택해 주세요.")
            return
        item_id = current.data(Qt.ItemDataRole.UserRole)
        item = self.ctx.menu.get(item_id)
        self.ctx.cart.remove(item_id)
        self.ctx.speak(f"{item.name}을(를) 뺐습니다.")
        self._refresh()

    def _goto_pay(self) -> None:
        if self.ctx.cart.is_empty():
            self.ctx.speak("장바구니가 비어 있습니다. 먼저 메뉴를 담아주세요.")
            return
        self.nav("payment")

    def on_enter(self) -> None:
        self._refresh()
        self.ctx.speak(self.ctx.cart.summary_text())
