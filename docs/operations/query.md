# Answer a question

Read [AGENTS.md](../../AGENTS.md) and [the data schema](../schema.md). The default mode answers from source evidence; synthetic-brain simulation is a future, separately invoked workflow.

1. Run `python -m bropsy index-wiki` after wiki edits. Search topical wiki pages first with `python -m bropsy search '<terms>' --scope wiki`.
2. Follow relevant wiki links. Search original sources with `--scope source` for each material claim, and search sources directly if the wiki has no relevant page.
3. Open full source sections through `python -m bropsy evidence '<citation>'`. Check that each cited passage supports the exact claim, including qualifiers, date, and negation. A search snippet alone is not evidence.
4. Answer with source citations. When sources conflict, present both positions and their provenance. State when evidence is missing or a conclusion is an inference. Exclude claims tied only to withdrawn sources or broken citations.
5. Record the query and the cited pages/sources in `.bropsy/log.md`. If the synthesis is reusable, update a wiki page and its topical links, preserving existing human edits.

Completion: each factual answer claim has an active source citation with a valid locator, conflicts are visible, and unsupported questions are explicitly marked unanswered. The separate fact-check skill can audit the finished answer more deeply.
