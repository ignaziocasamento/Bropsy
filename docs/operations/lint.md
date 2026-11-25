# Lint the wiki

Read [AGENTS.md](../../AGENTS.md) and [the data schema](../schema.md). Lint audits derived wiki material and its references; it does not rewrite original source snapshots.

1. Run `python -m bropsy lint`. Read every reported error and warning. Mechanical checks cover citation ID/version/locator, withdrawn sources, local links, duplicate pages, orphan pages, index integrity and alignment, and failed or interrupted queue items. If the index is stale or damaged, run `python -m bropsy rebuild-index` and repeat lint.
2. Search related wiki pages and original source sections to inspect semantic contradictions, near-duplicate concepts, stale summaries, missing cross-links, important concepts without pages, and unsupported claims. Report these as review findings, distinct from verified mechanical failures.
3. For an incremental pass, inspect pages touched by the most recent ingest. For a full pass, inspect all topical indexes and expand to linked pages and cited sources. Record date, scope, findings, and unresolved questions in `.bropsy/log.md`.
4. Invoke repair for a specific broken page. Pause for human judgment if the repair requires choosing between contradictory sources or reconstructing missing evidence.

Completion: every mechanical finding is accounted for; each semantic concern names the affected pages and source evidence; unresolved issues remain explicit. A clean mechanical lint is not proof that every statement is true.
