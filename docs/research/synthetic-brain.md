# A Brain for Synthetic Data Generation: Evidence and Hypotheses

Research date: November 24, 2026. This note separates published results from design choices that still need testing. “Cloning a brain” is a metaphor for simulating responses or data, not copying a mind.

## Two different goals

1. **Simulate a person or group**: interviews, decisions, and histories feed a searchable memory; an agent answers new scenarios. Park et al. built agents with memory, reflection, and planning. A later study used interviews with 1,052 people and compared simulated responses with participant responses. Its General Social Survey result is relative to participants' ability to repeat their own answers two weeks later; it does not demonstrate general fidelity or mental identity. [Generative Agents, 2023](https://arxiv.org/abs/2304.03442); [Generative Agent Simulations of 1,000 People, 2024](https://arxiv.org/abs/2411.10109).
2. **Synthesize a dataset**: learn properties of a real data distribution and sample new records. The aim is to preserve analyses useful for a specified use while measuring disclosure risk separately. Compare real and synthetic datasets on statistics, relationships, and downstream analyses. [NIST Synthetic Data Test Drive](https://pages.nist.gov/HLG-MOS_Synthetic_Data_Test_Drive/guide.html); [NIST SP 800-226](https://csrc.nist.gov/pubs/sp/800/226/final).

**Design inference:** a Karpathy-style wiki could be explicit memory for behavioral simulation and a provenance catalog for statistical synthesis. The wiki alone neither learns a distribution nor guarantees privacy.

## Initial architecture to test

| Component | Role | Evidence to retain |
| --- | --- | --- |
| Real sources | Preserve authorized interviews, events, or datasets | Origin, date, consent or license, version, access |
| Wiki | Extract facts, preferences, constraints, and contradictions | Precise citation and confidence |
| Generator | Produce scenario responses or conditioned synthetic records | Prompt, model, version, seed, parameters, sources |
| Evaluator | Compare with real data held out from development | Metrics, errors, subgroups, failure cases |

**Experimental hypothesis:** start with a wiki and retrieval agent for behavioral simulation. Use a separate tabular synthesizer if reproducible dataset statistics are the goal. Compare with a profile-only baseline and, for tabular data, a statistical baseline.

## Minimum evaluation protocol

1. Define the simulated unit: individual, composite persona, or population. Specify output and permitted use before selecting a model.
2. Split development and test data by **time or person** according to the goal. Write test scenarios before reading real answers. Testing against a source already in the prompt measures retrieval, not prediction.
3. For behavioral simulation, measure answer agreement, probability calibration, and variation across samples. Report results by subgroup and scenario. Human test-retest reliability can provide context, as in [Park et al.](https://arxiv.org/abs/2411.10109).
4. For synthetic datasets, measure marginal and joint distributions, correlations, logical constraints, and changes in relevant downstream analyses. NIST calls for joint utility and privacy evaluation for each intended use. [Source](https://pages.nist.gov/HLG-MOS_Synthetic_Data_Test_Drive/guide.html).
5. Test disclosure through exact and near-duplicate searches, sensitive-data extraction attempts, and membership inference where relevant. Synthetic output does not imply zero risk. NIST distinguishes formal differential privacy guarantees from informal claims. [NIST SP 800-188](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-188.pdf); [NIST SP 800-226](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-226.pdf).
6. Label generated data and keep the real corpus separate. Recursive training on generated data can lose coverage of distribution tails, depending on the training workflow. [Shumailov et al., Nature, 2024](https://www.nature.com/articles/s41586-024-07566-y); [Kazdan et al., 2024](https://arxiv.org/abs/2410.16713).

## First decision needed

Choose one initial demonstration: (A) simulate a consenting person's answers to new scenarios, (B) generate tabular records for a specific analysis, or (C) generate synthetic conversations. The evaluation unit, privacy risk, and metrics differ.

## Primary sources

- [Karpathy, LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): persistent wiki pattern, not a synthesis implementation.
- [Park et al., Generative Agents, 2023](https://arxiv.org/abs/2304.03442): memory, reflection, and planning.
- [Park et al., Generative Agent Simulations of 1,000 People, 2024](https://arxiv.org/abs/2411.10109): interview-based agent evaluation.
- [NIST Synthetic Data Test Drive](https://pages.nist.gov/HLG-MOS_Synthetic_Data_Test_Drive/guide.html): use-specific utility and privacy evaluation.
- [NIST SP 800-188](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-188.pdf) and [SP 800-226](https://csrc.nist.gov/pubs/sp/800/226/final): disclosure and differential privacy.
- [Shumailov et al., Nature, 2024](https://www.nature.com/articles/s41586-024-07566-y) and [Kazdan et al., 2024](https://arxiv.org/abs/2410.16713): recursive training risks and conditions.
