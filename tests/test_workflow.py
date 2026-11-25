from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from bropsy.checks import check_text, lint
from bropsy.pipeline import complete, enqueue, ingest_one, next_for_wiki, resume, withdraw
from bropsy.search import connect, index_wiki, rebuild, search
from bropsy.store import ensure_state, read_json
from bropsy.wiki_state import backup, status


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.root = ensure_state(self.project)

    def test_versioned_ingest_query_citation_and_withdrawal(self) -> None:
        original = self.project / "note.md"
        original.write_text("The sea is blue.\nThe hills are green.\n", encoding="utf-8")
        queued = enqueue(self.project, [original])
        self.assertEqual("queued", queued[0]["status"])
        result = ingest_one(self.project)
        self.assertEqual("indexed", result["status"])
        source_id, version = result["source_id"], result["version"]
        self.assertEqual("unchanged", enqueue(self.project, [original])[0]["status"])
        citation = f"[@{source_id}@{version}#L1-L2]"
        page = self.root / "wiki" / "seascape.md"
        page.write_text(f"# Seascape\n\nThe sea is blue. {citation}\n", encoding="utf-8")
        summary = self.root / "wiki" / "sources" / f"{source_id}.md"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(f"# Source\n\nThe sea is blue. {citation}\n\n[Seascape](../seascape.md)\n", encoding="utf-8")
        index = self.root / "wiki" / "index.md"
        index.write_text(f"[Seascape](seascape.md)\n[Source](sources/{source_id}.md)\n", encoding="utf-8")
        self.assertEqual(source_id, next_for_wiki(self.project)["source_id"])
        self.assertEqual("complete", complete(self.project, source_id, version, [page, summary])["status"])
        self.assertEqual([], status(self.project)["modified_since_agent_completion"])
        page.write_text(page.read_text(encoding="utf-8") + "Human note.\n", encoding="utf-8")
        self.assertEqual(["seascape.md"], status(self.project)["modified_since_agent_completion"])
        self.assertEqual(1, len(backup(self.project, [Path("seascape.md")])))
        connection = connect(self.root / "index.sqlite")
        try:
            self.assertEqual(3, index_wiki(connection, self.root / "wiki"))
            self.assertTrue(search(connection, "sea", "source"))
            self.assertTrue(search(connection, "seascape", "wiki"))
        finally:
            connection.close()
        (self.root / "index.sqlite").unlink()
        self.assertEqual(1, rebuild(self.project)["indexed_sources"])
        connection = connect(self.root / "index.sqlite")
        try:
            self.assertTrue(search(connection, "sea", "source"))
        finally:
            connection.close()
        self.assertTrue(check_text(self.project, citation)[0]["ok"])
        self.assertEqual(0, lint(self.project)["errors"])
        withdrawn = withdraw(self.project, source_id)
        self.assertEqual(["seascape.md", f"sources/{source_id}.md"], withdrawn["affected_pages"])
        self.assertEqual("withdrawn_source", check_text(self.project, citation)[0]["issue"])
        self.assertGreater(lint(self.project)["errors"], 0)

    def test_resume_and_source_version(self) -> None:
        original = self.project / "entry.txt"
        original.write_text("first version", encoding="utf-8")
        enqueue(self.project, [original])
        first = ingest_one(self.project)
        next_for_wiki(self.project)
        self.assertEqual(1, resume(self.project))
        self.assertEqual(first["source_id"], next_for_wiki(self.project)["source_id"])
        original.write_text("second version", encoding="utf-8")
        enqueue(self.project, [original])
        second = ingest_one(self.project)
        self.assertNotEqual(first["version"], second["version"])
        manifest = read_json(self.root / "manifest.json", {})
        self.assertEqual(2, len(manifest["sources"][first["source_id"]]["versions"]))
        first_snapshot = self.root / "sources" / first["source_id"] / first["version"] / "original.txt"
        self.assertEqual("first version", first_snapshot.read_text(encoding="utf-8"))

    def test_scanned_pdf_stays_in_error(self) -> None:
        path = self.project / "scan.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with path.open("wb") as output:
            writer.write(output)
        enqueue(self.project, [path])
        result = ingest_one(self.project)
        self.assertEqual("error", result["status"])
        self.assertIn("no extractable text", result["error"])
        self.assertIsNone(next_for_wiki(self.project))

    def test_directory_queue_ignores_private_state_and_lint_flags_broken_links(self) -> None:
        from bropsy.cli import files_from_paths
        source = self.project / "plain.txt"
        source.write_text("A plain source.", encoding="utf-8")
        private = self.root / "sources" / "secret.txt"
        private.write_text("Private state.", encoding="utf-8")
        selected = files_from_paths([str(self.project)])
        self.assertEqual([source], selected)
        page = self.root / "wiki" / "broken.md"
        page.write_text("[Missing](other.md)\n[@bad-citation]\n", encoding="utf-8")
        report = lint(self.project)
        self.assertIn("broken_link", [item["kind"] for item in report["issues"]])
        self.assertIn("malformed_citation", [item["kind"] for item in report["issues"]])
        self.assertIn("stale_wiki_index", [item["kind"] for item in report["issues"]])

    def test_git_guard_blocks_forced_private_file(self) -> None:
        from bropsy.cli import git_guard, install_hook
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        self.assertEqual("installed", install_hook(self.project))
        private = self.root / "sources" / "private.txt"
        private.write_text("private", encoding="utf-8")
        subprocess.run(["git", "add", "-f", ".bropsy/sources/private.txt"],
                       cwd=self.project, check=True)
        for folder in ("sources",):
            local_file = self.project / folder / "private.txt"
            local_file.parent.mkdir(parents=True, exist_ok=True)
            local_file.write_text("private", encoding="utf-8")
            subprocess.run(["git", "add", "-f", f"{folder}/private.txt"],
                           cwd=self.project, check=True)
        self.assertEqual(
            [".bropsy/sources/private.txt", "sources/private.txt"],
            git_guard(self.project)["blocked"],
        )
        shutil.copytree(Path(__file__).resolve().parents[1] / "bropsy", self.project / "bropsy")
        attempted = subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "commit", "-m", "should be blocked"], cwd=self.project, capture_output=True, text=True
        )
        self.assertNotEqual(0, attempted.returncode)
        self.assertIn(".bropsy/sources/private.txt", attempted.stdout + attempted.stderr)


if __name__ == "__main__":
    unittest.main()
