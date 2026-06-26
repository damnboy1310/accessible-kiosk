"""앱 전역 설정 및 환경변수 로딩."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv 미설치 시에도 환경변수만으로 동작
    pass

# 프로젝트 루트 (이 파일 기준 한 단계 위)
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MENU_PATH = DATA_DIR / "menu.json"

# LLM 설정
LLM_MODE = os.getenv("KIOSK_LLM_MODE", "mock").strip().lower()  # mock | claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-opus-4-8"

# 화면 (세로형 9:16)
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 960

# 접근성 기본값
DEFAULT_FONT_PT = 24
DEFAULT_TIMEOUT_SEC = 90
