"""메인 윈도우: 화면 스택 + 네비게이션 + 테마 적용."""
from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from src.config import SCREEN_HEIGHT, SCREEN_WIDTH
from src.ui import theme
from src.ui.app_context import AppContext
from src.ui.screens.cart_screen import CartScreen
from src.ui.screens.done_screen import DoneScreen
from src.ui.screens.order import OrderScreen
from src.ui.screens.payment_screen import PaymentScreen
from src.ui.screens.start import StartScreen


class Navigator:
    """화면 전환 + 테마 적용을 화면에 노출하는 어댑터."""

    def __init__(self, window: "MainWindow"):
        self._window = window

    def __call__(self, name: str) -> None:
        self._window.go(name)

    def apply_theme(self) -> None:
        self._window.apply_theme()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ctx = AppContext()
        self.nav = Navigator(self)

        self.setWindowTitle("버거킹 접근성 키오스크")
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.screens: dict[str, object] = {}
        self._add("start", StartScreen(self.ctx, self.nav))
        self._add("order", OrderScreen(self.ctx, self.nav))
        self._add("cart", CartScreen(self.ctx, self.nav))
        self._add("payment", PaymentScreen(self.ctx, self.nav))
        self._add("done", DoneScreen(self.ctx, self.nav))

        self.apply_theme()
        self.go("start")

    def _add(self, name: str, widget) -> None:
        self.screens[name] = widget
        self.stack.addWidget(widget)

    def go(self, name: str) -> None:
        # order 화면은 저위치 모드 변경을 반영해 매번 새로 만든다.
        if name == "order":
            old = self.screens["order"]
            idx = self.stack.indexOf(old)
            new = OrderScreen(self.ctx, self.nav)
            self.stack.insertWidget(idx, new)
            self.stack.removeWidget(old)
            old.deleteLater()
            self.screens["order"] = new
            self.apply_theme()

        widget = self.screens[name]
        self.stack.setCurrentWidget(widget)
        on_enter = getattr(widget, "on_enter", None)
        if callable(on_enter):
            on_enter()

    def apply_theme(self) -> None:
        self.setStyleSheet(theme.stylesheet(self.ctx.settings))
