"""Text-to-speech via macOS `say` (no-op elsewhere).

Speech runs on a background thread so the next prompt isn't blocked, and text
can be fed sentence by sentence while the reply is still streaming.
"""

import queue
import re
import shutil
import subprocess
import threading

from vector import config

SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")


def _say(text: str) -> None:
    # Text goes on stdin: never through a shell, never parsed as flags.
    try:
        subprocess.run(["say"], input=text, text=True, check=False)
    except OSError as e:
        print(f"⚠️  Speech failed: {e}")


def speak(text: str) -> None:
    """Blocking one-shot speech."""
    if config.SPEAK and text and shutil.which("say"):
        _say(text)


class Speaker:
    """Speaks queued sentences in order on a background thread."""

    def __init__(self, enabled: bool | None = None):
        self.enabled = (config.SPEAK if enabled is None else enabled) and bool(shutil.which("say"))
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._buffer = ""
        self._thread = None
        if self.enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _run(self) -> None:
        while (text := self._queue.get()) is not None:
            _say(text)

    def feed(self, piece: str) -> None:
        """Add streamed text; complete sentences are spoken right away."""
        if not self.enabled:
            return
        self._buffer += piece
        *done, self._buffer = SENTENCE_END.split(self._buffer)
        for sentence in done:
            if sentence.strip():
                self._queue.put(sentence.strip())

    def say(self, sentence: str) -> None:
        """Queue one complete sentence."""
        if self.enabled and sentence.strip():
            self._queue.put(sentence.strip())

    def flush(self) -> None:
        if self.enabled and self._buffer.strip():
            self._queue.put(self._buffer.strip())
        self._buffer = ""

    def close(self) -> None:
        """Finish speaking what's queued, then stop."""
        if self._thread:
            self._queue.put(None)
            self._thread.join()
