# Problem Framing: Synthetic Brain

Status: historical discovery note. The confirmed first-release scope is in [the current architecture](../design/architecture.md); synthetic generation remains a later phase.

## The decision to make

The phrase "clone a brain" does not identify a testable outcome. Select one target capability before choosing data, a model, or an architecture.

| Candidate capability | Unit of output | Real data needed | Primary evaluation | Distinct failure |
| --- | --- | --- | --- | --- |
| Behavioral simulation | Response or decision by a consenting person or defined group | Dated examples with inputs, responses, and relevant context | Agreement and calibration on unseen scenarios; comparison with a simple profile baseline | Plausible responses that do not predict the source |
| Synthetic conversations | Multi-turn interaction for a defined task and role | Authorized dialogues, task outcomes, and turn-level constraints | Task validity, turn consistency, diversity, and downstream performance | Fluent but impossible or repetitive conversations |
| Statistical data synthesis | New record from a defined population | Structured records, schema, sampling frame, and permitted analyses | Distributional fidelity, downstream utility, and disclosure risk | Realistic-looking records that distort rare cases or leak originals |

These candidates can coexist later. A single initial experiment must have one primary outcome so that its result is interpretable.

## Decision questions

1. **Subject:** Which person, group, process, or population is being represented? Is the aim an individual-specific model or a population model?
2. **Output:** What exact artifact must be generated, in what format, and for whom?
3. **Use:** Which real decision, analysis, or test will the synthetic artifact support? What would make it valuable?
4. **Data:** What examples exist, who owns them, what permissions apply, and how sensitive are they? What is the unit of independence for splitting them?
5. **Ground truth:** Which future or held-out observations can be used to judge output? Can a human or simple baseline be measured on the same task?
6. **Release:** Is output private to an experiment, shared with collaborators, or public? Privacy criteria depend on this exposure.

## Evidence gates before implementation

- A one-sentence, observable target capability and an explicit non-goal.
- A source inventory with usage rights and a data dictionary or example schema.
- A split plan that prevents the same person, case, or history from leaking into evaluation.
- A baseline that could falsify the value of a more complex generator.
- One primary utility metric, secondary quality metrics, and a disclosure-risk assessment appropriate to the release audience.
- A written rule for success, failure, and inconclusive results before inspecting generated samples.

## Interface design after the target is fixed

Following the Matt Pocock codebase-design skill, choose a **seam** only where an actual variation exists. A likely first **module** will accept a task instance and permitted evidence, then return a generated artifact plus provenance. Its **interface** must specify input invariants, output schema, error modes, and reproducibility. The evaluator should consume the same output artifact regardless of the generator's implementation. A second **adapter** is justified only when two real generation methods are compared. No module design is final until the chosen capability and evaluation unit are known.

## Current assumptions to challenge

- A wiki is a useful memory and provenance artifact, but it has not been shown to improve generation quality for this project.
- "More realistic" is not a metric until a downstream task and reference distribution are specified.
- A synthetic label does not establish low disclosure risk.
- A high average score may hide failures on rare cases and subgroups.

See [the primary-source research note](../research/synthetic-brain.md) and [the wiki concept page](synthetic-brain-concept.md).
