---
name: bropsy-repair
description: Repair a specific damaged Bropsy wiki page when the user supplies its path or asks to fix a lint finding. Preserve source snapshots and human edits.
---

# Repair a Bropsy wiki page

Read [the lint workflow](../../../docs/operations/lint.md) and [data schema](../../../docs/schema.md). Accept one target file under `.bropsy/wiki/` or one lint finding. Run commands from the clone root; when the current directory differs, pass `--project <clone-root>` before the subcommand. A raw source is immutable: if it is damaged, request a corrected input and acquire a new version.

1. Run `python -m bropsy lint` and isolate findings affecting the target. Run `python -m bropsy wiki-status`, then read its current text, linked pages, citation evidence, and any human edits or version history available. Back up each page before editing with `python -m bropsy backup-wiki <relative-wiki-page>`.
2. Classify the defect: broken link, missing locator, withdrawn source, duplicate, contradiction, stale summary, or damaged Markdown. Identify a source-backed correction.
3. Apply only corrections supported by evidence. Update affected topical links and claims together; retain competing source claims with both citations. For missing evidence, a consequential meaning change, or an irreconcilable conflict, guide the user through the choice and leave an explicit unresolved marker.
4. Run `python -m bropsy index-wiki` and lint again. Append a repair receipt to `.bropsy/log.md` with target, edits, evidence, and unresolved issues.

Completion: the target's verified defect is fixed, or the remaining choice is clearly documented for the user. Never silently reconstruct an original source or overwrite a human correction.
