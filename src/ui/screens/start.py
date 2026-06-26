"""F-1 시작 화면 + 접근성 빠른 설정."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class StartScreen(QWidget):
    def __init__(self, ctx, nav):
        super().__init__()
        self.ctx = ctx
        self.nav = nav
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(18)

        title = QLabel("버거킹\n접근성 키오스크")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        sub = QLabel("화면을 누르거나 음성으로 주문하세요")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(sub)

        root.addStretch(1)

        start_btn = QPushButton("주문 시작하기")
        start_btn.setObjectName("primary")
        start_btn.clicked.connect(lambda: self.nav("order"))
        root.addWidget(start_btn)

        root.addStretch(1)

        # 접근성 빠른 설정
        a11y_label = QLabel("접근성 설정")
        a11y_label.setObjectName("subtitle")
        root.addWidget(a11y_label)

        row1 = QHBoxLayout()
        self.hc_btn = QPushButton()
        self.hc_btn.clicked.connect(self._toggle_contrast)
        self.font_btn = QPushButton()
        self.font_btn.clicked.connect(self._cycle_font)
        row1.addWidget(self.hc_btn)
        row1.addWidget(self.font_btn)
        root.addLayout(row1)

        row2 = QHBoxLayout()
        self.low_btn = QPushButton()
        self.low_btn.clicked.connect(self._toggle_low)
        self.voice_btn = QPushButton()
        self.voice_btn.clicked.connect(self._toggle_voice)
        row2.addWidget(self.low_btn)
        row2.addWidget(self.voice_btn)
        root.addLayout(row2)

        self._refresh_labels()

    def _refresh_labels(self) -> None:
        s = self.ctx.settings
        self.hc_btn.setText(f"고대비: {'켜짐' if s.high_contrast else '꺼짐'}")
        self.font_btn.setText(f"글자크기: {int(s.font_scale * 100)}%")
        self.low_btn.setText(f"낮은화면: {'켜짐' if s.low_position else '꺼짐'}")
        self.voice_btn.setText(f"음성안내: {'켜짐' if s.voice_enabled else '꺼짐'}")

    def _toggle_contrast(self) -> None:
        self.ctx.settings.high_contrast = not self.ctx.settings.high_contrast
        self.ctx.speak("고대비 모드를 변경했습니다.")
        self._apply()

    def _cycle_font(self) -> None:
        self.ctx.settings.cycle_font_scale()
        self.ctx.speak(f"글자 크기 {int(self.ctx.settings.font_scale * 100)} 퍼센트.")
        self._apply()

    def _toggle_low(self) -> None:
        self.ctx.settings.low_position = not self.ctx.settings.low_position
        self.ctx.speak("화면 배치를 변경했습니다.")
        self._apply()

    def _toggle_voice(self) -> None:
        self.ctx.settings.voice_enabled = not self.ctx.settings.voice_enabled
        self._refresh_labels()
        self.ctx.speak("음성 안내를 켰습니다.")

    def _apply(self) -> None:
        self._refresh_labels()
        self.nav.apply_theme()

    def on_enter(self) -> None:
        self._refresh_labels()
        self.ctx.speak("환영합니다. 주문을 시작하려면 주문 시작하기 버튼을 누르세요.")
