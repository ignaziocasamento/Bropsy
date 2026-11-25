# Local data schema

The repository is a reusable template. Root `bropsy/` is tracked Python code, while ignored root `sources/` holds local input files and ignored root `.bropsy/` holds acquired and generated state. `python -m bropsy init` creates `sources/` and `.bropsy/` plus a pre-commit guard when no existing hook occupies that slot. Every path in the layout below is relative to `.bropsy/`.

## Local layout

- `manifest.json`: source ID to original path, active version, versions, author and date when known, and rights note. Unknown author/date is explicit. The rights note starts as `unrecorded`; the user or agent should document the actual permission before relying on the source for publication.
- `queue.json`: sequential ingest states `queued`, `indexed`, `processing`, `complete`, `error`, or `withdrawn`.
- `sources/<id>/<sha256>/original.<extension>`: immutable acquired bytes.
- `extracted/<id>/<sha256>.json`: text sections with stable locators.
- `wiki/`: agent-maintained Markdown pages and topical indexes.
- `reports/<id>-<sha256>.json`: per-source ingest receipt and completion status.
- `index.sqlite`: rebuildable local lexical search index for sources and wiki pages. Run `python -m bropsy rebuild-index` after loss or corruption.
- `log.md`: chronological operations log.
- `page-state.json` and `wiki-history/`: agent completion hashes and local backups used to detect and preserve human wiki edits.

A source ID identifies the path at which an input was first supplied. Its version is the SHA-256 of acquired bytes. Replacing a file at the same path produces a new version. Moving it to a new path currently creates a new ID. The manifest is the authority for active/withdrawn status.

## Citation syntax

`[@<source-id>@<version-sha256>#<locator>]`

The ID is 20 lowercase hex characters; the version is 64 lowercase hex characters. Text and Markdown locators are `L<start>-L<end>` for a 25-line extraction block. PDF locators are `p<number>`. Use `python -m bropsy evidence '<citation>'` to read the exact extracted text. For PDFs, cite the page plus a short claim-specific quotation or paraphrase in prose; the locator alone identifies a page, not a sentence.

A wiki claim must cite its original source. Wiki-to-wiki links aid navigation, but do not substitute for source citations. A citation to an older source version remains traceable and is flagged for review. A withdrawn source is not valid support for a current claim.

## Wiki page structure

Create `.bropsy/wiki/sources/<source-id>.md` for each ingested source. Its summary cites the active source version and links to the concept/entity pages it informed. Use a concise title, a one-paragraph scope statement, claim sections with direct citations, and links to related wiki pages. Distinguish source statements from agent inference. Record disagreements with both citations, dates when known, and unresolved status. Keep `.bropsy/wiki/index.md` as a short map to topical indexes. Keep topical index pages small and navigable; do not append every source or page to a single global index.

The CLI checks locator existence and local links. Semantic support, contradiction assessment, and preservation of human edits remain agent responsibilities.
