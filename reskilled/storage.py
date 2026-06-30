from datetime import datetime
from pathlib import Path
from typing import Optional

_DIR           = Path.home() / ".reskilled"
_RESUME        = _DIR / "resume.md"
_RESUME_HIST   = _DIR / "resume_history"
_PROJECTS      = _DIR / "projects"


def _init() -> None:
    _RESUME_HIST.mkdir(parents=True, exist_ok=True)
    _PROJECTS.mkdir(parents=True, exist_ok=True)


def save_resume(content: str) -> None:
    _init()
    if _RESUME.exists():
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        (_RESUME_HIST / f"{ts}.md").write_text(_RESUME.read_text())
    _RESUME.write_text(content)


def latest_resume() -> str | None:
    return _RESUME.read_text() if _RESUME.exists() else None


def resume_path() -> Path:
    return _RESUME


def resume_last_modified() -> Optional[datetime]:
    if not _RESUME.exists():
        return None
    return datetime.fromtimestamp(_RESUME.stat().st_mtime)


def save_project(topic: str, plan: str) -> None:
    _init()
    ts   = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    slug = topic.lower().replace(" ", "-")
    (_PROJECTS / f"{slug}_{ts}.md").write_text(plan)


def save_application(company: str, role: str, content: str) -> Path:
    _init()
    apps = _DIR / "applications"
    apps.mkdir(exist_ok=True)
    slug = f"{company}-{role}".lower().replace(" ", "-")
    path = apps / f"{slug}.md"
    path.write_text(content)
    return path
