"""오프라인 TTS 래퍼 (pyttsx3).

pyttsx3가 없거나 음성 엔진이 없는 환경에서도 앱이 죽지 않도록
모든 호출을 안전하게 감싼다. 음성 출력은 백그라운드 스레드에서 실행.
"""
from __future__ import annotations

import queue
import threading


class TTS:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._engine = None
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._init_engine()
        if self._engine is not None:
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()

    def _init_engine(self) -> None:
        try:
            import pyttsx3  # type: ignore

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 175)
        except Exception as exc:  # 엔진 없음 등 — 콘솔 폴백
            print(f"[TTS] 음성 엔진 초기화 실패, 콘솔 출력으로 대체: {exc}")
            self._engine = None

    def _run(self) -> None:
        while True:
            text = self._queue.get()
            if self._engine is None:
                continue
            try:
                with self._lock:
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception as exc:
                print(f"[TTS] 재생 오류: {exc}")

    def speak(self, text: str) -> None:
        if not text:
            return
        if not self.enabled:
            return
        print(f"[TTS] {text}")  # 데모 가시성을 위해 항상 콘솔에도 출력
        if self._engine is not None:
            self._queue.put(text)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
