from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from .store import ensure_state, read_json, utc_now, write_json


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _page(root: Path, supplied: Path) -> Path:
    wiki = root / "wiki"
    page = (supplied if supplied.is_absolute() else wiki / supplied).resolve()
    if wiki not in page.parents or not page.is_file():
        raise ValueError(f"Not an existing local wiki page: {supplied}")
    return page


def status(project: Path) -> dict:
    root = ensure_state(project)
    wiki = root / "wiki"
    recorded = read_json(root / "page-state.json", {"pages": {}})["pages"]
    modified = []
    new = []
    missing = []
    for path in wiki.rglob("*.md"):
        relative = path.relative_to(wiki).as_posix()
        old = recorded.get(relative)
        if old is None:
            new.append(relative)
        elif old["sha256"] != _digest(path):
            modified.append(relative)
    for relative in recorded:
        if not (wiki / relative).is_file():
            missing.append(relative)
    return {"modified_since_agent_completion": sorted(modified),
            "unrecorded": sorted(new), "missing": sorted(missing)}


def backup(project: Path, pages: list[Path]) -> list[str]:
    root = ensure_state(project)
    saved = []
    for supplied in pages:
        page = _page(root, supplied)
        relative = page.relative_to(root / "wiki")
        digest = _digest(page)
        target = root / "wiki-history" / digest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copyfile(page, target)
        saved.append(str(target))
    return saved


def record(project: Path, pages: list[Path]) -> None:
    root = ensure_state(project)
    path = root / "page-state.json"
    state = read_json(path, {"pages": {}})
    for supplied in pages:
        page = _page(root, supplied)
        relative = page.relative_to(root / "wiki").as_posix()
        state["pages"][relative] = {"sha256": _digest(page), "recorded_at": utc_now()}
    write_json(path, state)
