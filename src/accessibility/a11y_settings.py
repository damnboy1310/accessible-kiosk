"""접근성 설정 상태 (고대비 / 글자 크기 / 저위치 / 음성)."""
from __future__ import annotations

from dataclasses import dataclass

from src.config import DEFAULT_FONT_PT


@dataclass
class A11ySettings:
    high_contrast: bool = False
    font_scale: float = 1.0          # 1.0 ~ 2.0
    low_position: bool = False        # 휠체어용 하단 배치
    voice_enabled: bool = True

    @property
    def font_pt(self) -> int:
        return int(DEFAULT_FONT_PT * self.font_scale)

    def cycle_font_scale(self) -> None:
        steps = [1.0, 1.25, 1.5, 2.0]
        idx = steps.index(self.font_scale) if self.font_scale in steps else 0
        self.font_scale = steps[(idx + 1) % len(steps)]
