"""Long-term crewmate profile + short-term conversation memory."""

import shutil
from pathlib import Path

from vector import config
from vector.storage import load_json, save_json

# Keys managed by code; everything else is the hand-written crewmate profile.
RUNTIME_KEYS = ("profile", "short_term")

PROFILE_TRIGGERS = {
    "sleep_issue": ("sleep", "insomnia"),
    "high_stress": ("stress", "pressure", "overwhelm"),
    "cognitive_fatigue": ("tired", "confused", "exhausted", "blank"),
}


class Memory:
    def __init__(self, path: Path = config.MEMORY_FILE, max_history: int = config.MAX_HISTORY):
        self.path = path
        self.max_history = max_history
        if not path.exists() and config.MEMORY_TEMPLATE.exists() and path == config.MEMORY_FILE:
            shutil.copy(config.MEMORY_TEMPLATE, path)
            print(f"🆕 Created {path.name} from template — edit it to describe yourself.")
        self.data = load_json(path, {})
        self.data.setdefault("profile", {})
        self.data.setdefault("short_term", [])

    @property
    def history(self) -> list[dict]:
        return self.data["short_term"]

    @property
    def flags(self) -> list[str]:
        return self.data["profile"].setdefault("flags", [])

    def static_profile(self) -> dict:
        return {k: v for k, v in self.data.items() if k not in RUNTIME_KEYS}

    def observe(self, user_input: str) -> None:
        text = user_input.lower()
        for flag, words in PROFILE_TRIGGERS.items():
            if flag not in self.flags and any(w in text for w in words):
                self.flags.append(flag)

    def remember(self, user: str, reply: str) -> None:
        self.history.append({"user": user, "vector": reply})
        self.data["short_term"] = self.history[-self.max_history:]
        self.save()

    def save(self) -> None:
        save_json(self.path, self.data)
