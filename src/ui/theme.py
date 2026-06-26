"""테마 / 스타일시트 생성 (고대비 · 글자 크기 반영)."""
from __future__ import annotations

from src.accessibility.a11y_settings import A11ySettings

# 버거킹 느낌의 기본 팔레트
NORMAL = {
    "bg": "#FFF6E9",
    "fg": "#3B1E0E",
    "primary": "#D62300",      # 버거킹 레드
    "primary_fg": "#FFFFFF",
    "card": "#FFFFFF",
    "accent": "#F5A623",       # 옐로우
    "muted": "#7A6A5E",
}

# 고대비 팔레트 (명도 대비 강화)
HIGH_CONTRAST = {
    "bg": "#000000",
    "fg": "#FFFFFF",
    "primary": "#FFD400",
    "primary_fg": "#000000",
    "card": "#111111",
    "accent": "#00E5FF",
    "muted": "#DDDDDD",
}


def palette(settings: A11ySettings) -> dict[str, str]:
    return HIGH_CONTRAST if settings.high_contrast else NORMAL


def stylesheet(settings: A11ySettings) -> str:
    p = palette(settings)
    base = settings.font_pt
    return f"""
    QWidget {{
        background-color: {p['bg']};
        color: {p['fg']};
        font-family: 'Noto Sans CJK KR', 'Malgun Gothic', sans-serif;
        font-size: {base}px;
    }}
    QLabel#title {{
        font-size: {int(base * 1.6)}px;
        font-weight: bold;
        color: {p['primary']};
    }}
    QLabel#subtitle {{
        font-size: {int(base * 0.85)}px;
        color: {p['muted']};
    }}
    QPushButton {{
        background-color: {p['card']};
        color: {p['fg']};
        border: 3px solid {p['primary']};
        border-radius: 16px;
        padding: 18px;
        min-height: 60px;
        font-size: {base}px;
    }}
    QPushButton:focus {{
        border: 5px solid {p['accent']};
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {p['accent']};
        color: {p['primary_fg']};
    }}
    QPushButton#primary {{
        background-color: {p['primary']};
        color: {p['primary_fg']};
        font-weight: bold;
        min-height: 80px;
        font-size: {int(base * 1.2)}px;
    }}
    QLineEdit {{
        background-color: {p['card']};
        color: {p['fg']};
        border: 3px solid {p['primary']};
        border-radius: 12px;
        padding: 16px;
        font-size: {base}px;
    }}
    QListWidget {{
        background-color: {p['card']};
        border: 2px solid {p['muted']};
        border-radius: 12px;
        font-size: {base}px;
    }}
    """
