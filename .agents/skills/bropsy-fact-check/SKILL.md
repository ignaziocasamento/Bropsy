---
name: bropsy-fact-check
description: Audit a Bropsy answer when the user asks to fact-check citations against their local source corpus. Verify support, not external truth.
---

# Fact-check a Bropsy answer

Read [the query workflow](../../../docs/operations/query.md) and [data schema](../../../docs/schema.md). The user supplies an answer file or text to audit. Use the local Bropsy corpus only. Run commands from the clone root; when the current directory differs, pass `--project <clone-root>` before the subcommand. This audit reads evidence and reports findings; it does not edit the wiki or append a query log.

1. Identify each factual claim and the citations attached to it. Run `python -m bropsy check-citations <answer-file>` when the answer is in a file. For a single citation, run `python -m bropsy evidence '<citation>'`.
2. Open the complete relevant extracted section, not just a search snippet. Compare the exact claim with the source, including quantifiers, time, subject, and negation. Inspect other cited sources when a claim combines them.
3. Classify every claim as **supported**, **partially supported**, **contradicted**, **unsupported**, or **unverifiable**. A valid locator is necessary but does not prove support.
4. Return a compact table of claim, verdict, citation, and reason. Suggest a corrected wording when the source supports a narrower claim. Flag missing or withdrawn citations. Preserve disagreement between sources.

Completion: every factual claim in the supplied answer has a verdict grounded in its cited local source. This skill does not search the open web, assert independent truth, or edit original sources.
