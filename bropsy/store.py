from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = ".bropsy"
ALLOWED_SUFFIXES = {".md", ".markdown", ".txt", ".pdf"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def root_for(project: Path) -> Path:
    return project.resolve() / STATE_DIR


def ensure_state(project: Path) -> Path:
    root = root_for(project)
    for name in ("sources", "extracted", "wiki"):
        (root / name).mkdir(parents=True, exist_ok=True)
    for filename, default in (("manifest.json", {"schema_version": 1, "sources": {}}),
                              ("queue.json", {"schema_version": 1, "items": []})):
        path = root / filename
        if not path.exists():
            write_json(path, default)
    return root


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_key(path: Path) -> str:
    resolved = str(path.resolve())
    normalized = resolved.casefold() if os.name == "nt" else resolved
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]




def record_event(project: Path, operation: str, subject: str, detail: str) -> None:
    root = ensure_state(project)
    path = root / "log.md"
    date = utc_now()[:10]
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"## [{date}] {operation} | {subject}\n\n{detail}\n\n")
