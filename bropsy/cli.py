from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .checks import CITATION, check_text, lint, validate_citation
from .pipeline import PipelineError, complete, enqueue, ingest_one, next_for_wiki, resume, withdraw
from .search import connect, index_wiki, rebuild, search
from .store import ensure_state, read_json
from .wiki_state import backup, status


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def files_from_paths(raw_paths: list[str]) -> list[Path]:
    files = []
    for name in raw_paths:
        path = Path(name).expanduser()
        if path.is_dir():
            files.extend(sorted(candidate for candidate in path.rglob("*")
                                if candidate.is_file() and not {".git", ".bropsy"}.intersection(candidate.parts)
                                and candidate.suffix.lower() in {".md", ".markdown", ".txt", ".pdf"}))
        else:
            files.append(path)
    return files


def git_guard(project: Path) -> dict:
    result = subprocess.run(["git", "diff", "--cached", "--name-only", "-z"],
                            cwd=project, capture_output=True, check=True)
    names = [part.decode("utf-8", errors="replace").replace("\\", "/")
             for part in result.stdout.split(b"\x00") if part]
    private_roots = (".bropsy", "sources")
    blocked = [name for name in names if any(name == root or name.startswith(root + "/")
                                                 for root in private_roots)]
    return {"ok": not blocked, "blocked": blocked}


def install_hook(project: Path) -> str:
    git_dir = subprocess.run(["git", "rev-parse", "--git-path", "hooks"],
                             cwd=project, capture_output=True, text=True, check=True).stdout.strip()
    path = Path(git_dir)
    if not path.is_absolute():
        path = project / path
    hook = path / "pre-commit"
    if hook.exists():
        return "existing_hook_unchanged"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\npython -m bropsy --project \"$(git rev-parse --show-toplevel)\" git-guard\n",
                    encoding="utf-8")
    return "installed"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bropsy")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project checkout")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    add = commands.add_parser("enqueue")
    add.add_argument("paths", nargs="+")
    ingest = commands.add_parser("ingest")
    ingest.add_argument("--all", action="store_true")
    commands.add_parser("next")
    done = commands.add_parser("complete")
    done.add_argument("source_id")
    done.add_argument("version")
    done.add_argument("--page", type=Path, action="append", required=True)
    commands.add_parser("resume")
    commands.add_parser("queue")
    removed = commands.add_parser("withdraw")
    removed.add_argument("source_id")
    commands.add_parser("index-wiki")
    commands.add_parser("rebuild-index")
    commands.add_parser("wiki-status")
    save = commands.add_parser("backup-wiki")
    save.add_argument("pages", type=Path, nargs="+")
    find = commands.add_parser("search")
    find.add_argument("query")
    find.add_argument("--scope", choices=("wiki", "source", "all"), default="all")
    find.add_argument("--limit", type=int, default=10)
    commands.add_parser("lint")
    audit = commands.add_parser("check-citations")
    audit.add_argument("file", type=Path)
    evidence = commands.add_parser("evidence")
    evidence.add_argument("citation")
    commands.add_parser("git-guard")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project = args.project.resolve()
    try:
        root = ensure_state(project)
        if args.command == "init":
            input_dir = project / "sources"
            input_dir.mkdir(exist_ok=True)
            emit({"state": str(root), "input_dir": str(input_dir), "git_hook": install_hook(project)})
        elif args.command == "enqueue":
            emit(enqueue(project, files_from_paths(args.paths)))
        elif args.command == "ingest":
            results = []
            while True:
                result = ingest_one(project)
                if result is None:
                    break
                results.append(result)
                if not args.all:
                    break
            emit(results)
        elif args.command == "next":
            emit(next_for_wiki(project))
        elif args.command == "complete":
            emit(complete(project, args.source_id, args.version, args.page))
        elif args.command == "resume":
            emit({"resumed": resume(project)})
        elif args.command == "queue":
            emit(read_json(root / "queue.json", {"items": []}))
        elif args.command == "withdraw":
            emit(withdraw(project, args.source_id))
        elif args.command == "wiki-status":
            emit(status(project))
        elif args.command == "backup-wiki":
            emit({"saved": backup(project, args.pages)})
        elif args.command == "rebuild-index":
            emit(rebuild(project))
        elif args.command == "index-wiki":
            connection = connect(root / "index.sqlite")
            try:
                emit({"indexed_pages": index_wiki(connection, root / "wiki")})
            finally:
                connection.close()
        elif args.command == "search":
            connection = connect(root / "index.sqlite")
            try:
                emit(search(connection, args.query, args.scope, args.limit))
            finally:
                connection.close()
        elif args.command == "lint":
            report = lint(project)
            emit(report)
            return 1 if report["errors"] else 0
        elif args.command == "check-citations":
            checks = check_text(project, args.file.read_text(encoding="utf-8"))
            emit(checks)
            return 0 if checks and all(item["ok"] for item in checks) else 1
        elif args.command == "evidence":
            match = CITATION.fullmatch(args.citation)
            if match is None:
                raise ValueError("Expected a citation like [@source_id@version#locator]")
            result = validate_citation(project, *match.groups())
            emit(result)
            return 0 if result["ok"] else 1
        elif args.command == "git-guard":
            result = git_guard(project)
            emit(result)
            return 0 if result["ok"] else 1
        return 0
    except (OSError, ValueError, PipelineError, subprocess.CalledProcessError) as exc:
        emit({"error": str(exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main())
