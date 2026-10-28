"""Small shared helpers: project paths, logging setup, append-only JSONL files, time."""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIGS = PROJECT_ROOT / "configs"
RUNS = PROJECT_ROOT / "runs"


def find_env_file() -> Path | None:
    """The .env holding the Azure settings: $BILI_SANDBOX_ENV_FILE, else the nearest `.env` at or above the project root."""
    explicit = os.environ.get("BILI_SANDBOX_ENV_FILE")
    if explicit:
        return Path(explicit)
    for d in (PROJECT_ROOT, *PROJECT_ROOT.parents):
        if (d / ".env").is_file():
            return d / ".env"
    return None


def setup_logging(level: str = "INFO", log_file: Path | None = None, rich_console: bool = True) -> None:
    """Console logging (rich if available) plus an optional plain-text file that is flushed per record."""
    handlers: list[logging.Handler] = []
    if rich_console:
        from rich.logging import RichHandler
        handlers.append(RichHandler(rich_tracebacks=True, show_path=False, log_time_format="%H:%M:%S"))
    else:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handlers.append(h)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handlers.append(fh)
    logging.basicConfig(level=level.upper(), handlers=handlers, force=True)
    for noisy in ("aiohttp.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class JsonlWriter:
    """Append-only JSONL file. Each record is written, flushed and fsynced before `write` returns,
    so a crash never loses an acknowledged record and readers can tail the file while a run is live."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except ValueError as e:
            raise ValueError(f"{path}:{n}: invalid JSON line: {e}") from e
    return out


def utc_iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(time.time() if ts is None else ts, tz=timezone.utc).isoformat(timespec="milliseconds")


def write_private(path: Path, text: str) -> None:
    """Write a file readable only by the current user (tokens, keys)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
