"""F-6 완료 / 영수증 화면."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class DoneScreen(QWidget):
    def __init__(self, ctx, nav):
        super().__init__()
        self.ctx = ctx
        self.nav = nav
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        root.addStretch(1)

        check = QLabel("✓")
        check.setObjectName("title")
        check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(check)

        self.msg = QLabel("주문이 완료되었습니다")
        self.msg.setObjectName("title")
        self.msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg.setWordWrap(True)
        root.addWidget(self.msg)

        self.order_no = QLabel("")
        self.order_no.setObjectName("subtitle")
        self.order_no.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.order_no)

        root.addStretch(1)

        home_btn = QPushButton("처음으로")
        home_btn.setObjectName("primary")
        home_btn.clicked.connect(self._home)
        root.addWidget(home_btn)

    def _home(self) -> None:
        self.ctx.cart.clear()
        self.nav("start")

    def on_enter(self) -> None:
        no = self.ctx.last_order_no
        self.order_no.setText(f"주문번호 {no}번")
        self.ctx.speak(
            f"주문이 완료되었습니다. 주문번호는 {no}번입니다. "
            "음식이 준비되면 번호로 안내해 드립니다."
        )
        # 일정 시간 후 자동으로 시작 화면 복귀
        QTimer.singleShot(15000, self._home)
