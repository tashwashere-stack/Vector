import json
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  Could not read {path.name}: {e}")
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def compact(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
