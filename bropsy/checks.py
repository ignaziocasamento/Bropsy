from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

from .search import connect, integrity
from .store import ensure_state, read_json

CITATION = re.compile(r"\[@([0-9a-f]{20})@([0-9a-f]{64})#([^\]]+)\]")
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def validate_citation(project: Path, source_id: str, version: str, locator: str) -> dict:
    root = ensure_state(project)
    manifest = read_json(root / "manifest.json", {"sources": {}})
    source = manifest.get("sources", {}).get(source_id)
    reference = f"[@{source_id}@{version}#{locator}]"
    if source is None:
        return {"citation": reference, "ok": False, "issue": "unknown_source"}
    record = next((item for item in source["versions"] if item["version"] == version), None)
    if record is None:
        return {"citation": reference, "ok": False, "issue": "unknown_version"}
    extracted_path = root / "extracted" / source_id / (version + ".json")
    if not extracted_path.exists():
        return {"citation": reference, "ok": False, "issue": "missing_extraction"}
    extracted = read_json(extracted_path, {})
    section = next((item for item in extracted.get("sections", [])
                    if item["locator"] == locator), None)
    if section is None:
        return {"citation": reference, "ok": False, "issue": "unknown_locator"}
    result = {"citation": reference, "ok": bool(source["active"]), "issue": None,
              "source_file": record["filename"], "excerpt": section["text"]}
    if not source["active"]:
        result["issue"] = "withdrawn_source"
    elif version != source["active_version"]:
        result["issue"] = "older_version"
    return result


def check_text(project: Path, text: str) -> list[dict]:
    return [validate_citation(project, *match.groups()) for match in CITATION.finditer(text)]


def lint(project: Path) -> dict:
    root = ensure_state(project)
    wiki = root / "wiki"
    issues: list[dict] = []
    pages = sorted(wiki.rglob("*.md"))
    inbound: dict[Path, int] = defaultdict(int)
    content_hashes: dict[str, Path] = {}
    citation_count = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        relative = page.relative_to(wiki).as_posix()
        for candidate in re.findall(r"\[@[^\]\n]*\]", text):
            if CITATION.fullmatch(candidate) is None:
                issues.append({"level": "error", "page": relative,
                               "kind": "malformed_citation", "citation": candidate})
        for check in check_text(project, text):
            citation_count += 1
            if not check["ok"]:
                issues.append({"level": "error", "page": relative,
                               "kind": check["issue"], "citation": check["citation"]})
            elif check["issue"] == "older_version":
                issues.append({"level": "warning", "page": relative,
                               "kind": "older_version", "citation": check["citation"]})
        for raw_link in LINK.findall(text):
            if "://" in raw_link or raw_link.startswith(("mailto:", "#")):
                continue
            path_part = unquote(raw_link.split("#", 1)[0])
            if not path_part:
                continue
            target = (page.parent / path_part).resolve()
            if not target.exists():
                issues.append({"level": "error", "page": relative,
                               "kind": "broken_link", "target": raw_link})
            elif target in pages:
                inbound[target] += 1
        normalized = re.sub(r"\s+", " ", text).strip()
        if normalized:
            import hashlib
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if digest in content_hashes:
                issues.append({"level": "warning", "page": relative,
                               "kind": "duplicate_page",
                               "other": content_hashes[digest].relative_to(wiki).as_posix()})
            else:
                content_hashes[digest] = page
    for page in pages:
        if page.name != "index.md" and inbound[page] == 0:
            issues.append({"level": "warning", "page": page.relative_to(wiki).as_posix(),
                           "kind": "orphan_page"})
    connection = connect(root / "index.sqlite")
    try:
        if not integrity(connection):
            issues.append({"level": "error", "kind": "index_integrity"})
        manifest = read_json(root / "manifest.json", {"sources": {}})
        actual_sources = {
            row["source_id"]: row["version"]
            for row in connection.execute(
                "SELECT DISTINCT source_id, version FROM chunks WHERE kind = 'source'"
            )
        }
        expected_sources = {
            source_id: source["active_version"]
            for source_id, source in manifest["sources"].items() if source["active"]
        }
        if actual_sources != expected_sources:
            issues.append({"level": "error", "kind": "stale_source_index",
                           "expected": expected_sources, "actual": actual_sources})
        indexed_pages = {
            row["source_id"] for row in connection.execute(
                "SELECT DISTINCT source_id FROM chunks WHERE kind = 'wiki'"
            )
        }
        actual_pages = {page.relative_to(wiki).as_posix() for page in pages
                        if page.read_text(encoding="utf-8").strip()}
        if indexed_pages != actual_pages:
            issues.append({"level": "warning", "kind": "stale_wiki_index",
                           "missing": sorted(actual_pages - indexed_pages),
                           "obsolete": sorted(indexed_pages - actual_pages)})
    finally:
        connection.close()
    queue = read_json(root / "queue.json", {"items": []})
    for item in queue.get("items", []):
        if item["status"] == "error":
            issues.append({"level": "error", "kind": "ingest_error",
                           "source_id": item["source_id"], "detail": item.get("error")})
        elif item["status"] == "processing":
            issues.append({"level": "warning", "kind": "interrupted_processing",
                           "source_id": item["source_id"]})
    return {"pages": len(pages), "citations": citation_count,
            "errors": sum(x["level"] == "error" for x in issues),
            "warnings": sum(x["level"] == "warning" for x in issues),
            "issues": issues}
