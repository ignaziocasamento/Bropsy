from __future__ import annotations

import shutil
from pathlib import Path

from .extract import ExtractionError, extract
from .wiki_state import record
from .search import connect, remove_chunks, replace_chunks
from .store import ALLOWED_SUFFIXES, ensure_state, read_json, sha256_file, source_key, utc_now, write_json, record_event


class PipelineError(Exception):
    pass


def _paths(project: Path) -> tuple[Path, Path, Path]:
    root = ensure_state(project)
    return root, root / "manifest.json", root / "queue.json"


def enqueue(project: Path, paths: list[Path]) -> list[dict]:
    root, manifest_path, queue_path = _paths(project)
    manifest = read_json(manifest_path, {})
    queue = read_json(queue_path, {})
    added = []
    for supplied in paths:
        path = supplied.expanduser().resolve()
        if not path.is_file():
            raise PipelineError(f"Not a file: {path}")
        if root == path or root in path.parents:
            raise PipelineError("Cannot ingest generated local state")
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise PipelineError(f"Unsupported format: {path.suffix}")
        identity = source_key(path)
        version = sha256_file(path)
        existing = manifest["sources"].get(identity)
        if existing and existing.get("active_version") == version and existing.get("active"):
            added.append({"path": str(path), "status": "unchanged", "source_id": identity})
            continue
        if any(item["source_id"] == identity and item["version"] == version
               and item["status"] not in ("error", "complete") for item in queue["items"]):
            added.append({"path": str(path), "status": "already_queued", "source_id": identity})
            continue
        item = {"source_id": identity, "version": version, "path": str(path),
                "status": "queued", "queued_at": utc_now(), "error": None}
        queue["items"].append(item)
        added.append({"path": str(path), "status": "queued", "source_id": identity,
                      "version": version})
    write_json(queue_path, queue)
    return added


def ingest_one(project: Path) -> dict | None:
    root, manifest_path, queue_path = _paths(project)
    manifest = read_json(manifest_path, {})
    queue = read_json(queue_path, {})
    item = next((entry for entry in queue["items"] if entry["status"] == "queued"), None)
    if item is None:
        return None
    path = Path(item["path"])
    source_id, version = item["source_id"], item["version"]
    try:
        if not path.is_file() or sha256_file(path) != version:
            raise PipelineError("Source changed or disappeared after queueing; enqueue its current version")
        snapshot_dir = root / "sources" / source_id / version
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot = snapshot_dir / ("original" + path.suffix.lower())
        if not snapshot.exists():
            shutil.copyfile(path, snapshot)
        if sha256_file(snapshot) != version:
            raise PipelineError("Snapshot hash mismatch")
        sections = extract(snapshot)
        extracted = root / "extracted" / source_id / (version + ".json")
        write_json(extracted, {"source_id": source_id, "version": version,
                               "filename": path.name, "sections": sections})
        connection = connect(root / "index.sqlite")
        try:
            replace_chunks(connection, "source", source_id, version, sections)
        finally:
            connection.close()
        entry = manifest["sources"].setdefault(source_id, {
            "source_id": source_id, "original_path": str(path), "versions": [],
            "active": True, "active_version": None,
            "author": "unknown", "source_date": "unknown", "rights_note": "unrecorded"
        })
        if not any(record["version"] == version for record in entry["versions"]):
            entry["versions"].append({"version": version, "filename": path.name,
                                      "format": path.suffix.lower(), "acquired_at": utc_now(),
                                      "snapshot": str(snapshot.relative_to(root).as_posix())})
        entry["active"] = True
        entry["active_version"] = version
        write_json(manifest_path, manifest)
        item["status"] = "indexed"
        item["indexed_at"] = utc_now()
        item["error"] = None
        write_json(queue_path, queue)
        report = {"source_id": source_id, "version": version, "status": "indexed",
                  "sections": len(sections), "filename": path.name}
        write_json(root / "reports" / f"{source_id}-{version}.json", report)
        record_event(project, "ingest", path.name, f"Indexed {source_id}@{version} ({len(sections)} sections).")
        return {"source_id": source_id, "version": version, "status": "indexed",
                "sections": len(sections), "extracted": str(extracted)}
    except (OSError, ExtractionError, PipelineError) as exc:
        item["status"] = "error"
        item["error"] = str(exc)
        write_json(queue_path, queue)
        write_json(root / "reports" / f"{source_id}-{version}.json",
                   {"source_id": source_id, "version": version, "status": "error", "error": str(exc)})
        record_event(project, "ingest-error", path.name, str(exc))
        return {"source_id": source_id, "version": version, "status": "error", "error": str(exc)}


def next_for_wiki(project: Path) -> dict | None:
    root, _, queue_path = _paths(project)
    queue = read_json(queue_path, {})
    item = next((entry for entry in queue["items"] if entry["status"] == "indexed"), None)
    if item is None:
        return None
    item["status"] = "processing"
    item["started_at"] = utc_now()
    write_json(queue_path, queue)
    extracted = root / "extracted" / item["source_id"] / (item["version"] + ".json")
    return {"source_id": item["source_id"], "version": item["version"],
            "path": item["path"], "extracted": str(extracted)}


def complete(project: Path, source_id: str, version: str, pages: list[Path]) -> dict:
    root, _, queue_path = _paths(project)
    queue = read_json(queue_path, {})
    item = next((entry for entry in queue["items"] if entry["source_id"] == source_id
                 and entry["version"] == version and entry["status"] == "processing"), None)
    if item is None:
        raise PipelineError("No processing queue item matches this source and version")
    summary_name = f"sources/{source_id}.md"
    if not pages:
        raise PipelineError(f"Source summary page required: {summary_name}")
    citation = f"[@{source_id}@{version}#"
    normalized = []
    for supplied in pages:
        page = (supplied if supplied.is_absolute() else root / "wiki" / supplied).resolve()
        if root / "wiki" not in page.parents or not page.is_file():
            raise PipelineError(f"Wiki page not found inside local wiki: {page}")
        if citation not in page.read_text(encoding="utf-8"):
            raise PipelineError(f"Page lacks a citation to this version: {page}")
        normalized.append(page.relative_to(root / "wiki").as_posix())
    if summary_name not in normalized:
        raise PipelineError(f"Source summary page required: {summary_name}")
    record(project, pages)
    item["status"] = "complete"
    item["completed_at"] = utc_now()
    item["pages"] = normalized
    write_json(queue_path, queue)
    report_path = root / "reports" / f"{source_id}-{version}.json"
    report = read_json(report_path, {})
    report.update({"status": "complete", "pages": normalized, "completed_at": item["completed_at"]})
    write_json(report_path, report)
    page_list = ", ".join(normalized)
    record_event(project, "wiki", source_id, f"Completed version {version}; pages: {page_list}.")
    return {"source_id": source_id, "version": version, "status": "complete", "pages": normalized}


def resume(project: Path) -> int:
    _, _, queue_path = _paths(project)
    queue = read_json(queue_path, {})
    count = 0
    for item in queue["items"]:
        if item["status"] == "processing":
            item["status"] = "indexed"
            count += 1
    if count:
        write_json(queue_path, queue)
    return count


def withdraw(project: Path, source_id: str) -> dict:
    root, manifest_path, queue_path = _paths(project)
    manifest = read_json(manifest_path, {})
    source = manifest["sources"].get(source_id)
    if source is None:
        raise PipelineError("Unknown source ID")
    source["active"] = False
    source["withdrawn_at"] = utc_now()
    write_json(manifest_path, manifest)
    queue = read_json(queue_path, {})
    for item in queue["items"]:
        if item["source_id"] == source_id and item["status"] in ("queued", "indexed", "processing"):
            item["status"] = "withdrawn"
    write_json(queue_path, queue)
    connection = connect(root / "index.sqlite")
    try:
        remove_chunks(connection, "source", source_id)
    finally:
        connection.close()
    affected = []
    for page in (root / "wiki").rglob("*.md"):
        if f"[@{source_id}@" in page.read_text(encoding="utf-8"):
            affected.append(page.relative_to(root / "wiki").as_posix())
    page_list = ", ".join(affected) or "none"
    record_event(project, "withdraw", source_id, f"Affected pages: {page_list}.")
    return {"source_id": source_id, "status": "withdrawn", "affected_pages": affected,
            "snapshots_retained": True}
