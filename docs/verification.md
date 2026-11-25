# Verification record

Date: November 25, 2026. Scope: first-release implementation candidate. No personal source was used.

## Checks performed

- Python integration suite: five passing tests using temporary files. It covers source versioning, queue resumption, wiki citation completion, local source and wiki search, index rebuild after deletion, withdrawal and dependent pages, human-edit detection and backup, scanned-PDF failure, broken-link and stale-index lint, and a real Git commit attempt blocked by the installed private-data hook.
- Positive PDF extraction: a generated one-page text PDF produced a `p1` locator and its expected text. A blank-page PDF produced a specific non-extractable error.
- Independent skill forward tests: fact checking identified a claim contradicted by a structurally valid citation; repair corrected an invalid locator in a temporary wiki and ended with zero lint findings. No repository or personal data was used in those tests.
- Both project skills passed the skill-creator frontmatter and scaffold validator.
- Python 3.13 syntax compilation passed. Runtime integration tests ran with Python 3.14 on Windows.
- Markdown relative links and staged-file paths were checked. `.bropsy/` is ignored by Git; the hook also blocks a forced add.

## Not yet verified

- GitHub Copilot behavior: neither Copilot CLI nor the VS Code Copilot extension is installed in the current environment. The shared instructions and skill paths follow the documented repository locations, but a Copilot session test remains open.
- Claude Code behavior: documented as expected compatibility and intentionally not tested in this release.
- A 4,000-source corpus, retrieval quality at scale, performance, OCR, and synthetic-brain generation are later work.

The implementation must not be described as scale-validated or cross-agent behaviorally verified until those checks are performed.
