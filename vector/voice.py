"""Text-to-speech via macOS `say` (no-op elsewhere)."""

import shutil
import subprocess

from vector import config


def speak(text: str) -> None:
    if not config.SPEAK or not text or shutil.which("say") is None:
        return
    # Text goes on stdin: never through a shell, never parsed as flags.
    try:
        subprocess.run(["say"], input=text, text=True, check=False)
    except OSError as e:
        print(f"⚠️  Speech failed: {e}")
