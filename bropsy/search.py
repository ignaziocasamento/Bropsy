from __future__ import annotations

import re
import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            version TEXT NOT NULL,
            locator TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    connection.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
        USING fts5(content, content='chunks', content_rowid='id')
    """)
    connection.executescript("""
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
          INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
          INSERT INTO chunks_fts(chunks_fts, rowid, content)
          VALUES ('delete', old.id, old.content);
        END;
    """)
    return connection


def replace_chunks(connection: sqlite3.Connection, kind: str, source_id: str,
                   version: str, sections: list[dict]) -> None:
    with connection:
        connection.execute("DELETE FROM chunks WHERE kind = ? AND source_id = ?", (kind, source_id))
        connection.executemany(
            "INSERT INTO chunks(kind, source_id, version, locator, content) VALUES (?, ?, ?, ?, ?)",
            [(kind, source_id, version, item["locator"], item["text"]) for item in sections],
        )


def remove_chunks(connection: sqlite3.Connection, kind: str, source_id: str) -> None:
    with connection:
        connection.execute("DELETE FROM chunks WHERE kind = ? AND source_id = ?", (kind, source_id))


def index_wiki(connection: sqlite3.Connection, wiki_root: Path) -> int:
    seen = set()
    count = 0
    for path in sorted(wiki_root.rglob("*.md")):
        relative = path.relative_to(wiki_root).as_posix()
        seen.add(relative)
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        sections = [{"locator": f"L{n + 1}-L{min(n + 25, len(lines))}",
                     "text": "\n".join(lines[n:n + 25])}
                    for n in range(0, len(lines), 25)]
        replace_chunks(connection, "wiki", relative, "", sections)
        count += 1
    obsolete = connection.execute("SELECT DISTINCT source_id FROM chunks WHERE kind = 'wiki'").fetchall()
    for row in obsolete:
        if row["source_id"] not in seen:
            remove_chunks(connection, "wiki", row["source_id"])
    return count


def search(connection: sqlite3.Connection, query: str, scope: str = "all",
           limit: int = 10) -> list[dict]:
    terms = re.findall(r"\w+", query, flags=re.UNICODE)
    if not terms:
        return []
    expression = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)
    rows = connection.execute("""
        SELECT c.kind, c.source_id, c.version, c.locator,
               snippet(chunks_fts, 0, '[', ']', ' … ', 24) AS snippet,
               bm25(chunks_fts) AS rank
        FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.rowid
        WHERE chunks_fts MATCH ? AND (? = 'all' OR c.kind = ?)
        ORDER BY rank LIMIT ?
    """, (expression, scope, scope, limit)).fetchall()
    results = [dict(row) for row in rows]
    for result in results:
        if result["kind"] == "source":
            result["citation"] = f'[@{result["source_id"]}@{result["version"]}#{result["locator"]}]'
    return results


def integrity(connection: sqlite3.Connection) -> bool:
    try:
        connection.execute("INSERT INTO chunks_fts(chunks_fts, rank) VALUES ('integrity-check', 1)")
        return True
    except sqlite3.DatabaseError:
        return False



def rebuild(project: Path) -> dict:
    import os
    import json
    from .store import ensure_state, read_json

    root = ensure_state(project)
    target = root / "index.sqlite"
    temporary = root / "index.rebuild.sqlite"
    if temporary.exists():
        temporary.unlink()
    connection = connect(temporary)
    sources = 0
    try:
        manifest = read_json(root / "manifest.json", {"sources": {}})
        for source_id, source in manifest["sources"].items():
            if not source["active"]:
                continue
            version = source["active_version"]
            extracted = root / "extracted" / source_id / (version + ".json")
            if not extracted.is_file():
                raise FileNotFoundError(f"Missing extraction for {source_id}@{version}")
            sections = json.loads(extracted.read_text(encoding="utf-8"))["sections"]
            replace_chunks(connection, "source", source_id, version, sections)
            sources += 1
        pages = index_wiki(connection, root / "wiki")
        if not integrity(connection):
            raise sqlite3.DatabaseError("Rebuilt FTS index failed integrity check")
    except Exception:
        connection.close()
        temporary.unlink(missing_ok=True)
        raise
    connection.close()
    os.replace(temporary, target)
    return {"indexed_sources": sources, "indexed_wiki_pages": pages}
