"""F-5 결제 화면 (Fake)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class PaymentScreen(QWidget):
    def __init__(self, ctx, nav):
        super().__init__()
        self.ctx = ctx
        self.nav = nav
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("결제")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.status = QLabel("결제 수단을 선택하세요")
        self.status.setObjectName("subtitle")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.amount = QLabel("0원")
        self.amount.setObjectName("title")
        self.amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.amount)

        root.addStretch(1)

        self.card_btn = QPushButton("카드로 결제")
        self.card_btn.setObjectName("primary")
        self.card_btn.clicked.connect(self._pay)
        root.addWidget(self.card_btn)

        self.mobile_btn = QPushButton("모바일로 결제")
        self.mobile_btn.clicked.connect(self._pay)
        root.addWidget(self.mobile_btn)

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(lambda: self.nav("cart"))
        root.addWidget(cancel_btn)

    def _set_buttons(self, enabled: bool) -> None:
        self.card_btn.setEnabled(enabled)
        self.mobile_btn.setEnabled(enabled)

    def _pay(self) -> None:
        self._set_buttons(False)
        self.status.setText("결제 중입니다...")
        self.ctx.speak("결제 중입니다. 잠시만 기다려 주세요.")
        QTimer.singleShot(2000, self._finish)

    def _finish(self) -> None:
        ok, order_no = self.ctx.payment.charge(self.ctx.cart.total)
        if ok:
            self.ctx.last_order_no = order_no
            self.nav("done")
        else:
            self.status.setText("결제에 실패했습니다. 다시 시도해 주세요.")
            self.ctx.speak("결제에 실패했습니다. 다시 시도해 주세요.")
            self._set_buttons(True)

    def on_enter(self) -> None:
        self._set_buttons(True)
        self.status.setText("결제 수단을 선택하세요")
        self.amount.setText(f"{self.ctx.cart.total:,}원")
        self.ctx.speak(
            f"결제하실 금액은 {self.ctx.cart.total:,}원입니다. 결제 수단을 선택하세요."
        )
