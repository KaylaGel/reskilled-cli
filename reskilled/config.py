import json
from pathlib import Path

_DIR = Path.home() / ".reskilled"
_FILE = _DIR / "config.json"


def load() -> dict:
    if not _FILE.exists():
        return {}
    return json.loads(_FILE.read_text())


def save(config: dict) -> None:
    _DIR.mkdir(exist_ok=True)
    _FILE.write_text(json.dumps(config, indent=2))


def is_configured() -> bool:
    return bool(load().get("model"))
