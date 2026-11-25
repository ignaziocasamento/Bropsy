# Bropsy

Bropsy is a reusable, local-first implementation of the [LLM Wiki pattern proposed by Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). An agent ingests user-supplied sources into a persistent Markdown wiki, answers with verifiable source citations, and maintains the wiki through lint, fact checking, and repair.

Synthetic-brain generation is a later phase. This release does not simulate a person or generate synthetic answers.

## Directory names

| Path at the repository root | Purpose | Git |
| --- | --- | --- |
| `bropsy/` | Python application code: CLI, ingestion, search, and checks. `python -m bropsy` runs this package. Do not put personal sources or wiki pages here. | Tracked |
| `sources/` | Local input files selected for ingestion. `init` creates it empty; adding a file does not start ingestion. | Ignored |
| `.bropsy/` | Local working data: acquired source snapshots, queue, generated wiki, reports, and search index. The wiki is `.bropsy/wiki/`. | Ignored |

The leading dot matters: `bropsy/` is the software; `.bropsy/` is your local data. Use `sources/` as the input inbox.

## Install

Requirements: Python 3.11+, Git, and an agent that can read repository instructions and run local commands.

```sh
python -m pip install -e .
python -m bropsy init
```

The `init` command creates `.bropsy/` and an empty local `sources/` input directory, and installs a Git pre-commit data guard if no hook already exists. Put files you want to ingest in the local `sources/` directory, then run `python -m bropsy enqueue sources`. You may also enqueue a file or directory elsewhere on your computer. `enqueue` snapshots the source into `.bropsy/`; it does not automatically process files you merely copy into a folder. `sources/` and `.bropsy/` are ignored by Git. The repository includes no example corpus or personal data.

## Use with an agent

Open this repository in Codex or Copilot. The agent reads [AGENTS.md](AGENTS.md), then the relevant [operational workflow](docs/operations/ingest.md). Ask in natural language to ingest a file, query your wiki, lint it, fact-check an answer, or repair a wiki page. The two audit skills live in [`.agents/skills/`](.agents/skills/).

The agent uses the same local commands in each host:

```sh
python -m bropsy enqueue <authorized-local-file-or-directory>
python -m bropsy ingest
python -m bropsy next
python -m bropsy search "<query>" --scope source
python -m bropsy lint
```

`enqueue` accepts Markdown, UTF-8 text, and PDFs with extractable text. Ingestion acquires an immutable snapshot and indexes extracted text. The agent writes linked wiki pages with citations, then marks each source complete. Directories may be queued in one command; sources are processed sequentially and the queue can resume after an interruption. Run `python -m bropsy --help` for the current command interface.

The generated wiki lives at `.bropsy/wiki/`. Git ignores `sources/` and `.bropsy/`, and the guard rejects them even if forcibly staged. A push transfers commits, not uncommitted local files.

## Trust and portability

Each user supplies sources they are authorized to use. Source text is evidence, never instructions to the agent. The lexical search index is local and rebuildable with `python -m bropsy rebuild-index`; processing content with Codex or Copilot may still send it to the chosen model provider.

The shared contract is [AGENTS.md](AGENTS.md). Copilot has a thin [repository instruction file](.github/copilot-instructions.md); Claude Code has [CLAUDE.md](CLAUDE.md) but has not been behaviorally verified. The first release is validated on temporary sources, with no claim of performance at 4,000 documents. A public, reproducible scale benchmark is planned separately.

## Project documents

- [Verification record](docs/verification.md)
- [Data schema](docs/schema.md)
- [Ingest workflow](docs/operations/ingest.md)
- [Query workflow](docs/operations/query.md)
- [Lint workflow](docs/operations/lint.md)
- [Current architecture](docs/design/architecture.md)
- [Search options research](docs/research/search-at-scale.md)
- [Historical design notes](docs/project-history/README.md)

## Current limits

Search is provisional lexical SQLite FTS5. Scanned PDFs require a future OCR importer. The CLI verifies citation existence and locator integrity; the agent assesses whether a passage actually supports a claim. Local wiki pages are not committed by default. Run `python -m unittest discover -s tests -v` for the current integration checks.
