"""화면 간 공유되는 앱 상태/서비스 컨테이너."""
from __future__ import annotations

from src.accessibility.a11y_settings import A11ySettings
from src.accessibility.tts import TTS
from src.config import LLM_MODE
from src.domain.cart import Cart
from src.domain.menu import Menu
from src.services.llm.base import LLMService
from src.services.payment import FakePayment


def _build_llm(menu: Menu) -> LLMService:
    if LLM_MODE == "claude":
        try:
            from src.services.llm.claude_client import ClaudeLLM

            print("[LLM] Claude API 모드")
            return ClaudeLLM(menu)
        except Exception as exc:
            print(f"[LLM] Claude 초기화 실패, Mock으로 대체: {exc}")
    from src.services.llm.mock_client import MockLLM

    print("[LLM] Mock 모드")
    return MockLLM(menu)


class AppContext:
    def __init__(self):
        self.menu = Menu.load()
        self.settings = A11ySettings()
        self.tts = TTS(enabled=self.settings.voice_enabled)
        self.cart = Cart(self.menu)
        self.llm = _build_llm(self.menu)
        self.payment = FakePayment()
        self.last_order_no: int | None = None

    def speak(self, text: str) -> None:
        self.tts.set_enabled(self.settings.voice_enabled)
        self.tts.speak(text)
