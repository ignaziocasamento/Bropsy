# Search choices beyond a small Markdown wiki

Research date: November 25, 2026. This note records primary-source capabilities and a provisional implementation decision; it does not claim performance on a 4,000-source corpus.

## Why a single index is insufficient as a design assumption

[Karpathy's LLM Wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) reports that a hand-maintained `index.md` works well at roughly 100 sources and hundreds of pages, then suggests adding search as the wiki grows. That is an experience report, not a hard source limit. Bropsy keeps a short map of topical indexes for human navigation and a separate local search index for retrieval.

## Candidate retrieval methods

| Method | Source-backed capability | Tradeoff for Bropsy |
| --- | --- | --- |
| [ripgrep](https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md) | Fast exact/regex search with line context and no persistent index | Weak relevance ranking and no semantic recall; raw PDF requires extraction |
| [SQLite FTS5](https://www.sqlite.org/fts5.html) | Local indexed full-text search, BM25 ranking, snippets, and integrity checks | Lexical matching; index and content must be kept in sync |
| [qmd](https://github.com/tobi/qmd) | Local BM25, vector and hybrid retrieval, reranking, incremental updates, line-number retrieval | Additional models and runtime setup; non-Markdown originals need a normalization path |

**Design inference:** source ID, version hash, and locator must remain independent of the chosen search engine. This keeps citations stable if retrieval changes. The search engine offers candidates; the agent opens the full cited section before making a factual claim.

## First-release decision

Use SQLite FTS5 as a provisional, rebuildable lexical index. It is available through Python's SQLite library on the development environment and fits the local-only retrieval requirement. This decision is about a working first release, not measured superiority at scale. The source and wiki formats are not tied to FTS5.

A later public benchmark can compare retrieval quality, query latency, index update time, and rebuild time on prepared questions with expected sources. No example corpus or benchmark data is included in the first release.
