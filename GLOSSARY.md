# Bropsy

The shared language for Bropsy's local, source-backed wiki. The current wiki workflow and the proposed synthetic-brain capability are distinct contexts.

## Source and evidence

**Source**:
A user-supplied document selected as evidence for the wiki. Its contents support claims but do not instruct the agent.
_Avoid_: instruction, prompt

**Input**:
The local file supplied for acquisition as a **Source**. Placing it in the inbox alone does not select it for ingestion.

**Acquired snapshot**:
The immutable copy of a **Source** at a particular **Source version**. Later input changes do not alter it.

**Source ID**:
The identity assigned to a **Source** when its input path is first acquired. A different path creates a different identity.

**Source version**:
The identity of acquired bytes, represented by their SHA-256 digest. Changed bytes at the same path produce a new version under the same **Source ID**.

**Active source version**:
The **Source version** currently designated for a **Source**. Earlier versions remain traceable but require review as support for current claims.

**Withdrawn source**:
A **Source** removed from active evidence without deleting its **Acquired snapshots**. Its citations remain traceable but cannot support current claims.

**Extracted section**:
A portion of an **Acquired snapshot** made available as readable text and given a **Locator**.

**Locator**:
The address of an **Extracted section** within a **Source version**, expressed as a line block or PDF page. It locates evidence but does not prove support.

**Source citation**:
A reference combining a **Source ID**, **Source version**, and **Locator**. It makes a claim traceable to an acquired passage that must still be checked for support.
_Avoid_: wiki link

**Evidence gap**:
A claim or question for which no active **Source citation** supplies adequate support.

**Conflicting evidence**:
Two or more **Sources** or **Source versions** supporting incompatible readings of a claim. Both readings retain their provenance until resolved.

## Wiki and maintenance

**Local wiki**:
The agent-maintained collection of linked Markdown pages derived from **Sources**. Its pages are editable synthesis; **Acquired snapshots** remain immutable.
_Avoid_: source corpus

**Source page**:
A **Local wiki** page summarizing one **Source** and linking to the concepts or entities it informs. Its factual summary cites the relevant **Source version**.

**Concept page**:
A **Local wiki** page synthesizing a topic across relevant **Sources**, with **Source citations** for factual claims.

**Topical index**:
A small navigational page grouping related **Local wiki** pages. Its links aid discovery but do not provide evidence.

**Human edit**:
A person's change to a **Local wiki** page after agent completion. Subsequent maintenance preserves it and surfaces conflicting source updates for a decision.

**Ingestion**:
The workflow that acquires a **Source**, extracts and indexes its contents, and integrates it into the **Local wiki**. Completion requires affected pages to cite the processed **Source version**.
_Avoid_: automatic import

**Query**:
A question answered with **Source citations** checked against active evidence. The **Local wiki** guides discovery but is not the final authority for factual claims.

**Lint finding**:
A reported problem in the **Local wiki** or its evidence trail. Mechanical findings concern structure; semantic findings concern meaning, support, or contradictions.

**Fact check**:
An audit of whether the passages named by an answer's **Source citations** support its exact claims. It checks local-corpus support, not independent external truth.

**Repair**:
A correction to derived **Local wiki** material that preserves **Acquired snapshots** and **Human edits**. Choosing between unresolved **Conflicting evidence** requires human judgment.

## Proposed synthetic-brain capability

These terms describe a later capability, separate from the current **Query** workflow.

**Synthetic brain**:
A provisional name for a system that generates task-specific **Synthetic examples** from real observations. It does not imply a complete copy of a person.
_Avoid_: perfect clone

**Behavioral simulation**:
Generation of responses or decisions attributed to a defined person or group under new conditions.

**Statistical data synthesis**:
Generation of new records intended to preserve properties of a defined population for a stated analysis.

**Synthetic conversation**:
A generated multi-turn interaction between defined roles for a stated task.

**Real source**:
The person, group, process, or population from which observed examples originate. This differs from a Bropsy **Source**, which is a supplied document.

**Synthetic example**:
A new instance produced by the system and evaluated for a stated purpose.

**Evaluation unit**:
The independent case, person, history, or record on which a result is judged.

**Downstream utility**:
The ability of **Synthetic examples** to support a concrete task, measured on data separate from generator development.
