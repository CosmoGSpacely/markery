# Design Review — Model-Agnosticism Framework

**Date:** 2026-05-21  
**Status:** Concept — not yet promoted to ROADMAP or DEFERRED  
**Scope:** A framework for measuring and designing toward model-agnosticism in the project workflow — reducing dependence on any specific model and making it feasible to use cheap cloud models or local models for portions of the work.

---

## Problem Statement

The current workflow assumes a capable large-context model for all tasks. This creates two related problems:

1. **Cost sensitivity** — All tasks, regardless of complexity, are billed at the same per-token rate. Simple tasks (Y/N candidate review, factual section writing) consume the same token budget as complex ones (interpretive essay writing, Wikipedia analysis).

2. **Model lock-in** — If the workflow is designed around a specific model's capabilities (large context window, strong world-knowledge recall, nuanced reasoning), it becomes brittle to model changes and inaccessible to cheaper or local alternatives.

The question is whether there is a principled framework for measuring and designing toward model-agnosticism — something more structural than empirically testing many models.

---

## The Framework: Two Axes

Model-agnosticism is not primarily a testing problem — it is a task design problem. The relevant framework classifies each task along two dimensions:

**Context dependency** — How much does correct completion rely on knowledge the model must supply from training, versus knowledge provided explicitly in the prompt? High dependency means the task is model-sensitive: a model without domain knowledge of 1930s industrial history will produce worse output than one that was trained on it. Low dependency means any model that can follow instructions can do the work, because all necessary facts are in the prompt.

**Output structure** — How constrained is the expected output? A task that asks for JSON with a fixed schema is structurally model-agnostic because correctness can be checked by code. A task that asks for a scholarly paragraph is model-sensitive because assessing quality requires a human or a stronger model.

Plotting tasks on this 2D space gives a working map of the workflow:

```
                         Output
                  Structured ←——————————→ Open prose

Context   Low    auto-disposition         scaffold narrative fills
depend-          card → Y/N review        essay from scaffold
ency             validate                 
                 suggest-variants         

          High                            contextual essay
                                          Wikipedia analysis
```

Tasks in the low-dependency / structured-output quadrant are model-agnostic by construction. Tasks in the high-dependency / open-prose quadrant are irreducibly model-sensitive. All other tasks are design choices — the question is whether they can be moved toward the lower-left.

---

## Three Design Principles

### 1. Bring Your Own Knowledge

Never ask a model to recall domain facts — provide all facts as structured inputs. The model's job is transformation (arrange, judge, narrate), not retrieval. A model that knows nothing about Chicago Pneumatic Tool Company in 1930 should produce the same factual accuracy as one trained on it, because the scaffold contains every fact it needs.

This principle moves tasks left on the context-dependency axis. Its implementation in Markery is the `scaffold` and `card` tools proposed in `SPECIALIST_REVIEW.md`: the model receives pre-generated structured inputs containing everything it needs, and world-knowledge recall is never required.

### 2. Checkable Outputs

Design task outputs so correctness can be verified by code rather than by a human or a stronger model. If a validator can be written for the output, the task is structurally model-agnostic — because you can run any model and check whether its output is correct without a human in the loop.

This is why the `validate` tool (proposed in `SPECIALIST_REVIEW.md`) is not just a token-reduction device. It converts "was this essay accurate?" from a model-sensitive judgment into a deterministic check. Any model whose output passes the validator is producing correct factual content, regardless of capability level.

The principle: if you cannot write a validator for an output, the task is inherently model-sensitive. If you can, it is not.

### 3. Progressive Commitment

Break complex tasks into stages where each stage's output is validated before the next begins. A cheap model fills in a scaffold; the validator checks the facts; if it passes, the cheap model completes the narrative; the validator checks cross-references. No individual stage requires a capable model if each stage is well-defined and its output checkable.

This is a pipeline design pattern, not a prompting trick. It converts a single complex model-sensitive task into a sequence of simpler model-agnostic steps. The key property is that each stage's MVO (see below) can be checked by code before the next stage begins.

---

## Measuring Model-Agnosticism: The MVO Concept

The reason testing many models feels unsatisfying is that general model benchmarks (MMLU, HumanEval, HELM) measure capability, not suitability for specific tasks. A more principled measurement is task-specific.

For each task in the workflow, define a **minimum viable output (MVO)** — the minimum output that downstream code would accept without error or that a downstream tool would act on correctly.

- If the MVO can be fully specified and checked by code: the task is **model-agnostic in principle**. Testing reduces to: can Model X produce valid-format output? This is a low bar that most models meet.
- If the MVO requires a human or stronger model to assess: the task is **inherently model-sensitive** regardless of prompt design.

This reframes the question from "does Model X perform well?" to "for which tasks can we define an MVO that code can check?" Those tasks form the model-agnostic tier. The remainder is the model-sensitive tier and warrants the best available model.

For Markery, applying this:

| Task | MVO checkable by code? | Tier |
|---|---|---|
| Y/N candidate review | Yes — output is Y, N, or UNCERTAIN with required fields | Model-agnostic |
| Factual essay sections | Yes — serial numbers, dates, patent numbers resolve against DB | Model-agnostic |
| Entity variant suggestion | Yes — output strings are present in the source DB tables | Model-agnostic |
| Auto-disposition | Yes — entirely deterministic; no model involved | Model-agnostic |
| Narrative essay paragraphs | No — quality requires judgment | Model-sensitive |
| Wikipedia policy compliance | No — NPOV, notability require interpretation | Model-sensitive |
| Historical significance analysis | No — interpretive; no ground truth | Model-sensitive |

---

## Existing Tools That Operationalize These Principles

**Structured output enforcement** — Libraries such as Outlines, Instructor, and Guidance constrain model output to a schema (JSON, regex, context-free grammar) at the level of token sampling rather than instruction following. The constraint is imposed before decoding completes, so even a weak model produces structurally valid output. For local models, llama.cpp and Ollama support grammar-constrained generation natively. This is the most powerful practical mechanism for model-agnosticism because it makes output structure a hard constraint rather than a soft instruction.

Applying this to Markery: a Y/N candidate review that enforces a JSON schema `{"decision": "Y"|"N"|"UNCERTAIN", "reasons": [...], "flags": [...]}` is interchangeable across any model that supports grammar-constrained decoding. The output is always parseable; the validator checks the content.

**DSPy** — A Stanford framework that optimizes prompts automatically for a given task and model combination, treating the prompt as a learnable parameter rather than a fixed artifact. This makes a task definition model-agnostic at the meta-level: DSPy finds the right prompt formulation for each target model rather than requiring manual tuning. More infrastructure than Markery currently needs, but directionally correct for a multi-model deployment.

**Property-based output testing** — Rather than evaluating output quality holistically, define behavioral properties that any correct response must satisfy: "the response contains exactly one of Y, N, or UNCERTAIN," "all serial numbers cited appear in `case_file`," "all dates are ISO 8601," "the patent number resolves against `patents`." These can be expressed as code and run automatically across models. This is the practical implementation of the MVO concept, and it is directly compatible with the `validate` tool.

**Constrained decoding for local models** — Grammar-based constraints (BNF grammars, JSON Schema enforcement) are natively supported in llama.cpp via the `--grammar` flag and in Ollama via format parameters. For Markery's structured tasks (candidate review, variant suggestion output, preflight status), this means local models produce parseable structured output without relying on instruction-following ability. Local model suitability for a task becomes a question of grammar support, not reasoning capability.

---

## Convergence with the Token-Reduction Proposal

The token-reduction tools proposed in `SPECIALIST_REVIEW.md` and the model-agnosticism framework described here converge on the same design moves. This is not a coincidence — they address the same root problem from different angles.

| Tool | Token reduction mechanism | Model-agnosticism mechanism |
|---|---|---|
| `scaffold` | Pre-fills 40–60% of essay content | Removes context dependency; model writes narrative, not facts |
| `card` | Replaces per-candidate synthesis | Provides structured fixed-format input; any model can act on it |
| `validate` | Eliminates verification pass | Makes output correctness code-checkable; enforces MVO |
| `auto-disposition` | Removes 30–50% of review queue | Removes model from loop entirely for deterministic cases |
| `preflight` | Eliminates setup round-trips | Reduces session context footprint for small-context models |
| `digest` | Marginal for large-context models | Essential for small-context local models |

The practical implication: once these tools exist, there is a principled answer to "what can a local model do?" — any task whose inputs are pre-generated by these tools and whose outputs are validated by `validate`. That is the model-agnostic tier. Everything else (interpretive narrative, Wikipedia analysis, historical significance) remains in the model-sensitive tier, and that is an honest architectural boundary rather than a capability gap to be closed by testing more models.

---

## Where Testing Does Add Value

Model testing contributes most where tasks sit near the boundary between quadrants — tasks that are currently moderately context-dependent or partially structured, where prompt design changes could push them into the model-agnostic tier.

For these boundary tasks, testing tells you the gap (how much quality drops with a weaker model); design principles tell you how to close it (add more structure to the input, constrain the output format, extract context dependency into the scaffold). Testing without a design framework gives you a ranking of models. Testing within the framework gives you a diagnosis of which design changes would make the task model-agnostic.

---

## Summary

The framework has two components:

**Classification:** Plot each workflow task on the context-dependency × output-structure matrix. Tasks in the low-dependency / structured-output quadrant are already model-agnostic; tasks in the high-dependency / open-prose quadrant are irreducibly model-sensitive; everything else is a design choice.

**Design:** Apply three principles — bring your own knowledge (remove context dependency), checkable outputs (make the MVO code-verifiable), progressive commitment (pipeline complex tasks into validated stages). These principles move tasks toward the model-agnostic quadrant without requiring model-specific prompt tuning.

Measurement follows from design: define the MVO for each task, check whether code can verify it, and classify accordingly. Where the MVO is code-verifiable, the task is model-agnostic and the only remaining test is whether a target model can produce valid-format output — a low bar that grammar-constrained decoding makes even lower.
