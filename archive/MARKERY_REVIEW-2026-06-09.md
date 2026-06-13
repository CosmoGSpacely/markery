# MARKERY-REVIEW — Codebase analysis: deferred work, token-efficiency, model-agnosticism, agentic design

**Date:** 2026-06-09
**Scope:** Full `src/markery` tree (13,765 LOC), `markery-langgraph` companion repo (524 LOC), DESIGN.md model-agnosticism framework, DEFERRED.md open register.
**Method:** Source read of every LLM call site, the model-resolution path, the langgraph subprocess interface, and the deferred-work register. API facts (caching minimums, pricing, Batch API) verified against the `claude-api` skill reference, not from memory.
**Lens:** Three stated goals — token-efficient, model-agnostic, agentic design — plus closing deferred work.

This is a REVIEW file per the CLAUDE.md convention. When its findings are dispositioned, archive to `archive/MARKERY_REVIEW-<date>.md` and `git rm` it from root.

---

## Executive summary

Markery is architecturally sound on all three axes. The LLM layer has a single client-construction site ([llm.py](src/markery/common/llm.py)), the model-agnosticism framework in [DESIGN.md](DESIGN.md#L119) is genuinely principled (Bring-Your-Own-Knowledge + Checkable Outputs + Progressive Commitment + MVO), and the agentic layer correctly sits at the **workflow** tier (code-orchestrated graph + human gate), which is the right call for this problem — not an over-built open-ended agent.

The findings below are refinements, not redesigns. One is a concrete latent defect:

| # | Finding | Axis | Severity |
|---|---|---|---|
| **A1** | Prompt caching is silently disabled on the model actually in use. Code targets a **1024-token** cache minimum; Haiku 4.5's minimum is **4096**. Every system prompt is ~2K tokens — between the two — so `cache_read_input_tokens` is **0** on every call despite the cache being "enabled." | Token | **High** |
| A2 | Bulk independent LLM calls (librarian extract over book chunks; historian draft/infer over queues) run as serial live calls. No use of the **Batch API** (50% cost reduction, ideal for these non-latency-sensitive loops). | Token | Medium |
| A4 | `MARKERY_TOKEN_LOG` captures per-call records but there is no aggregation command — you cannot see total project cost without hand-reading JSONL. (Already filed as **D059**.) | Token | Medium |
| B1 | The default model ID `claude-haiku-4-5-20251001` is hardcoded in **3 separate files**. No single definition site, despite the single client site. | Model | Medium |
| B2 | The model-agnosticism claim is asserted in DESIGN.md but **never proven** — there is no benchmark that runs ≥2 models against the MVO validators. `mvo.md` documents contracts; no cross-model harness executes them. | Model | Medium |
| C1 | The langgraph tool surface scrapes the `[infer]` block out of stdout with **regex** ([tools.py:56](../markery-langgraph/src/langgraph_markery/tools.py#L56)). A `--json` output mode on the historian commands would make the subprocess contract robust. | Agentic | Medium |

---

## Codebase overview

Three tiers per CLAUDE.md: **Markery** (CLI, DBs, tests), **Specialist** (six agents under `src/markery/specialist/`), **Project** (`projects/<name>/`). The CLI is the product-under-test; companion repos drive it via subprocess against a versioned `MANIFEST.json` contract.

LLM surface is small and centralized — only **three** modules call Claude:
- [historian/cli.py](src/markery/specialist/historian/cli.py) — `card --infer`, `digest --infer`, `draft` (the main caller)
- [librarian/extract.py](src/markery/specialist/librarian/extract.py) — verbatim-quote extraction over book chunks
- [common/tokens.py](src/markery/common/tokens.py) — `count_tokens` for instrumentation

All inference routes through [`llm.call()`](src/markery/common/llm.py#L40) except librarian, which builds its own `messages.create` ([extract.py:179](src/markery/specialist/librarian/extract.py#L179)) — a minor centralization gap (see B1).

---

## A. Token efficiency

### A1 — Prompt cache minimum mismatch (the headline defect)

[llm.py:64](src/markery/common/llm.py#L64) wraps the system prompt in `cache_control: {ephemeral}`, and the historian sizes its persona deliberately to clear the cache threshold:

> [historian/cli.py:23](src/markery/specialist/historian/cli.py#L23) — *"task suffixes appended to push above the 1024-token minimum required for Anthropic prompt caching."*
> [librarian/extract.py:173](src/markery/specialist/librarian/extract.py#L173) — *"cache_read value will be > 0 if the prompt meets the 1024-token minimum."*

**Both comments encode the wrong threshold for the model in use.** Per the `claude-api` skill's caching table, the minimum cacheable prefix is model-dependent:

| Model | Min cacheable prefix |
|---|---|
| **Haiku 4.5** (the Markery default) | **4096 tokens** |
| Opus 4.x | 4096 tokens |
| Sonnet 4.5 / 4 / 3.7 | 1024 tokens |
| Sonnet 4.6 | 2048 tokens |

The 1024 figure is correct only for older Sonnet. The historian system prompts are `identity.md` (989 words ≈ ~1.3K tokens) + a task block (~600 tokens) ≈ **~2K tokens** — comfortably over 1024 but **under 4096**. On Haiku 4.5 the cache silently never populates: `cache_creation_input_tokens` and `cache_read_input_tokens` come back **0** on every call, and the full ~2K-token prefix is billed at full input price on every candidate, every chunk, every draft.

**Economics.** For a `card --infer` sweep of a 30-candidate queue, the shared ~2K-token prefix should cost full price once (write) and ~0.1× on 29 reads. Instead it is billed full price 30×. At Haiku input pricing ($1/1M), the prefix waste is small per project but scales with queue size and is pure overhead the code believes it has already eliminated.

**Recommendation.** Do **not** pad the persona to 4096 tokens just to cross the line — that inflates every call to save a fraction of it. Instead:
1. Correct the three docstrings to state the real, model-dependent minimum.
2. Add a one-line verification step to the token instrumentation: after any multi-call run, assert `cache_read_input_tokens > 0` and warn if 0 across a run that shares a prefix. This converts "we think caching works" into a checked invariant — exactly the Checkable-Outputs principle from DESIGN.md applied to the tool's own cost model.
3. Where caching genuinely matters (librarian over a 100+-chunk book), the prefix is the same `_SYSTEM` block every chunk — if that block is < 4096 tokens, caching will not help on Haiku, so the real lever there is **A2 (Batch API)**, not caching.

### A2 — No Batch API for bulk independent calls

[librarian/extract.py:382](src/markery/specialist/librarian/extract.py#L382) loops chunks with a live `messages.create` per chunk. Historian `draft` and `card --infer` are likewise invoked per-pair across a queue. These calls are **independent and not latency-sensitive** — the textbook Batch API case (50% price cut, up to 100K requests/batch, results within ~1h).

Today nothing uses `client.messages.batches`. For a book extract (hundreds of chunks) or a full-queue infer pass, routing through the Batch API halves token cost with no quality change.

**Recommendation.** Add a `--batch` path to `librarian extract` and to a new `historian infer-queue` (batch all unreviewed candidates at once). Keep the live path as default for single-item interactive use. File as a new DEFERRED entry (proposed **D060** below).

### A3 — Serial chunking is fine; batching is the win

The serial loop itself is not the problem (it preserves cache-read ordering, which A2 doesn't need). No change beyond A2.

### A4 — Cost is captured but not aggregated (D059)

The instrumentation is good — [tokens.py](src/markery/common/tokens.py) appends structured JSONL with prompt/completion/cache_read/model/wall_ms. But there is no `markery tokens report` to sum it. This is the measurement half of token-efficiency: you cannot manage what you cannot see. **D059 already tracks this and should be promoted to active** — it is the prerequisite for verifying A1 and A2 actually saved money. Build it first; it makes every other token finding measurable.

---

## B. Model-agnosticism

### B1 — Default model ID hardcoded in three places

`claude-haiku-4-5-20251001` appears verbatim in:
- [tokens.py:43](src/markery/common/tokens.py#L43)
- [librarian/extract.py:21](src/markery/specialist/librarian/extract.py#L21)
- [historian/cli.py:18](src/markery/specialist/historian/cli.py#L18)

The resolution chain itself is good — `--model` arg → `MARKERY_MODEL` env → project.json `model` ([cli.py:44](src/markery/cli.py#L44)) → hardcoded default. But the *default* has three sources of truth. Changing the house model means three edits and risks drift (e.g. tokens.py counting against a different model than historian infers with).

**Recommendation.** Define `DEFAULT_MODEL` once in [config.py](src/markery/common/config.py) (or llm.py, alongside the single client site) and import it in all three. The pinned dated ID is fine to keep for reproducibility — just keep it in one place.

### B2 — The model-agnosticism claim is unproven

[DESIGN.md:147](DESIGN.md#L147) states the architectural boundary honestly: "any task whose inputs are pre-generated by these tools and whose outputs pass `validate`" is model-agnostic. The MVO tier table ([DESIGN.md:135](DESIGN.md#L135)) is a genuine contribution. `tests/benchmarks/mvo.md` documents the contracts, and D049 added validator tests.

But nothing **executes** the claim across models. There is no harness that runs `card --infer` and `draft` under, say, Haiku 4.5 vs Sonnet 4.6 and asserts both pass the same `validate` gate. The model-agnostic tier is argued, not demonstrated. For a project whose thesis is model-agnosticism, that is the missing keystone — and it is cheap, because the validators already exist (the whole point of Checkable Outputs).

**Recommendation.** Add a benchmark (`tests/benchmarks/` or a `markery bench` command) that runs the model-agnostic-tier tasks under ≥2 models on a fixed fixture set and asserts each output passes its MVO validator. This turns DESIGN.md's boundary from a claim into a regression-tested property and produces the per-model cost/quality table the token work (A) needs. Propose as **D061**.

### B3 — Affirm: the resolution chain and BYOK discipline are right

Per-project `model` in project.json (animal-marks-1930 pins Haiku) flowing through `_try_inject_project_model` is clean and scope-neutral. The Bring-Your-Own-Knowledge discipline (every serial/date/assignee supplied in the scaffold, never recalled) is what *makes* Haiku viable here. No change — this is the load-bearing good decision.

---

## C. Agentic design

### C1 — Subprocess contract scrapes stdout with regex

[tools.py](../markery-langgraph/src/langgraph_markery/tools.py) drives Markery by parsing human-readable stdout: the `[infer]` block is recovered with `re.search(r'recommendation=(\w+)', ...)` ([tools.py:56](../markery-langgraph/src/langgraph_markery/tools.py#L56)), reasoning by splitting on `"\n[infer]"`. This is brittle — any formatting tweak to the historian's print output silently breaks the graph's parse, and the fallback (`defer`, score 3) masks the breakage as a defer.

The `MANIFEST.json` contract version guards *signatures* but not *output shape*, and is coarse (one `"1.0"` for all four commands).

**Recommendation.** Add `--json` to `historian card --infer` (and `digest --infer`) emitting `{"recommendation", "score", "reasoning", "card_text"}`. The graph parses JSON instead of scraping prose; the contract becomes a schema, not a regex. This is the single highest-leverage agentic-robustness change. Propose as **D062**.

### C2 — Contract versioning is coarse but adequate

One `contract_version` for four commands means any change bumps all consumers. Fine at current scale (one consumer repo). Note for later, not now.

### C3 — Affirm: workflow tier + human gate is the correct altitude

Per the claude-api decision tree, this is a **workflow** (multi-step, code-controlled logic with your own tools), not an open-ended agent — and the graph is built that way: deterministic edges, `interrupt_before=["human_gate"]`, human-in-the-loop on the irreversible `confirm`. `run_card_infer` failing safe to `defer`/3 (never auto-confirm) is correct defensive design. **Do not escalate this to an autonomous agent.** The value is the human gate on borderline figurative-mark cases (cf. Phase 22 P4), and that is exactly what the current design delivers.

---

## Deferred-work disposition

Open items in DEFERRED.md, judged against the three goals:

| ID | Item | Disposition | Rationale |
|---|---|---|---|
| **D059** | `markery tokens report` aggregation | **Promote to active — do first** | Prerequisite for measuring A1/A2. Infra already exists; it's the report layer only. |
| D058 | `markery trademark inspect` (design codes, imagery) | Keep; promote when next figurative-mark selection arises (Phase 22 P4) | Serves CLI-first inspection; low effort. |
| D053 | `markery match inspect` per-entity scores | Keep | Same family as D058; structured inspection surface. |
| D054 | Migrate 5 legacy information-systems essays | Promote — triggered by Phase 22 P1 site rebuild | Will surface as a validate regression during the publisher pass. |
| D055 | gitignore `projects/*/site/` | Keep deferred | Genuine open decision; no forcing function yet. |
| D056 | `MARKERY_ROOT` not persistent | Keep | Environment papercut; D057 cluster. |
| D057 | No isolated venv for langgraph | Keep — blocked on `python3.12-venv` | External blocker named. |
| D025 / D026 | Photographic-equipment / precision-tools projects | Active (Phase 22 P2/P3) | Already in ROADMAP. |
| D028 | `trademark search-tsdr <mark-text>` | Keep | Useful but not goal-aligned. |
| D007 | `patent bulk-import` (PatentsView) | Keep | Acquisition-path alternative; not goal-aligned. |

**New entries this review proposes** (token/model/agentic goals):

| Proposed | Item | Goal |
|---|---|---|
| D060 | `--batch` path for librarian extract + a batched `historian infer-queue` (Batch API, 50% off) | Token |
| D061 | Cross-model MVO benchmark — run model-agnostic-tier tasks under ≥2 models, assert each passes its validator | Model |
| D062 | `--json` output on `historian card --infer` / `digest --infer`; langgraph parses JSON not regex | Agentic |

Plus two **non-deferred fixes** (small enough to just do, not defer):
- Correct the three cache-minimum docstrings (A1) and add the `cache_read>0` verification warning.
- Consolidate `DEFAULT_MODEL` to one definition site (B1).

---

## Prioritized recommendations

1. **D059 — build `markery tokens report` first.** Everything token-related is unmeasurable until this exists. (Active.)
2. **Fix A1 (cache docstrings + verification warning).** Small edit; stops the codebase from lying to itself about a live cost path. Then re-run a historian queue and confirm whether crossing 4096 is worth it for the librarian's book-length prefix.
3. **B1 — single `DEFAULT_MODEL`.** One-line-per-file change; removes drift risk.
4. **D062 — `--json` on infer commands.** Hardens the one agentic seam that currently depends on prose formatting.
5. **D060 — Batch API path.** The concrete 50%-cost lever for bulk extract/infer, measurable once D059 lands.
6. **D061 — cross-model MVO benchmark.** Converts the model-agnosticism thesis into a tested property and yields the per-model cost/quality table.

Items 1–4 are days of work and close real gaps; 5–6 are the larger investments that make the three design goals *demonstrable* rather than asserted.

D060, D061, and D062 were filed to `DEFERRED.md` on 2026-06-09. The two non-deferred fixes (A1 docstrings, B1 consolidation) remain recorded here only — not yet actioned.

---

## Portfolio assessment

*This section evaluates Markery as a portfolio artifact — what it demonstrates to a technical reviewer or hiring manager, and how to strengthen and position it. It is a candid assessment, not a recommendation letter; the gaps are named as plainly as the strengths.*

### What this repo demonstrates

Markery is **not** a tutorial reskin or a CRUD clone, and that is the first thing a reviewer notices. It is an original system: cross-reference USPTO trademark filings against patent grants to reconstruct how early-20th-century companies coordinated IP strategy, then publish the findings as a static research site and — in several cases — as cited additions to live Wikipedia articles. The idea is genuinely novel, the domain is non-trivial, and the output is verifiable. That combination is rare in a portfolio and is the project's strongest single signal.

Concretely, it evidences ability across five areas a reviewer cares about:

1. **Systems architecture (senior-level).** Clean three-tier separation (infrastructure / specialist / project) with enforced boundaries; scope-neutral databases ([DESIGN.md:151](DESIGN.md#L151)) where no project-specific constants leak into the data layer; a single LLM client-construction site ([llm.py](src/markery/common/llm.py)); and a **contract-versioned subprocess interface** between two repos ([MANIFEST.json](MANIFEST.json) + langgraph `check_contract`). The decision to make the CLI the product-under-test — "the tool validates its own correctness" — is a coherent architectural thesis, not an afterthought.

2. **Process discipline (uncommon in solo work).** Phase-gated ROADMAP with explicit PASSED criteria, a DEFERRED register where **every** entry carries a reopen trigger, a REVIEW-file convention, and a CLAUDE.md project contract that governs how work is classified and routed. These are the artifacts of someone who has either worked on, or thought seriously about, production systems with multiple contributors. Most personal projects have none of this.

3. **AI engineering judgment (differentiated).** The model-agnosticism framework ([DESIGN.md:119](DESIGN.md#L119)) — Bring-Your-Own-Knowledge, Checkable Outputs, Progressive Commitment, and the MVO tier table — is a real, articulated point of view that most practitioners do not have. Token instrumentation is built in. The agentic layer sits at the **correct altitude**: a code-orchestrated workflow with a human gate on the irreversible action, not an over-built autonomous agent. Knowing *not* to reach for the maximal tool is itself a senior signal.

4. **Data & integration breadth.** EPO OPS and USPTO TSDR API clients, DuckDB-backed ingestion of patents/trademarks/entities, a Real-ESRGAN image-enhancement and vectorization pipeline, static site generation, and MediaWiki write automation. The project spans API integration, data pipelines, LLM orchestration, image processing, and publishing — and they cohere into one system rather than reading as a grab-bag.

5. **Shipped, verifiable output.** The killer artifact is the live Wikipedia contributions with recorded revision IDs (D050: revisions 1357391696, 1357918452, 1358151236, 1358151441, etc., confirmed unreverted). "My tool's research is rigorous enough to survive on Wikipedia, and here are the diffs" is a concrete, externally-validated result most portfolios cannot offer.

### Ability level this supports

On the evidence in this repo, the work reads **well above junior — solidly mid-to-senior for an applied-AI / AI-engineer / ML-platform profile.** The fingerprint that matters is *judgment*: choosing the right altitude for the agent, designing outputs to be code-checkable, instrumenting cost, enforcing module boundaries, and versioning an inter-repo contract. Those are decisions, not syntax, and they are the things that distinguish someone who can own a system from someone who can complete a ticket.

The honest caveat a reviewer **will** raise — and you should pre-empt — is provenance. This repo is developed through Claude Code (CLAUDE.md governs agent sessions), so a reviewer will ask "what did you do versus the agent?" The strong answer is already true here: the *architecture, the boundaries, the model-agnosticism framework, the phase-gate discipline, and the cost model* are the human-judgment layer that survives regardless of who typed the implementation. Orchestrating an AI to build a real, bounded, instrumented system **is** the relevant modern skill — but only if you can articulate the design decisions as yours. Be ready to whiteboard the three-tier model and the MVO framework without notes; that conversation is where this project wins or loses.

### What a critical reviewer would flag (and how to fix)

These are ordered by how much they affect the portfolio impression, not by effort:

1. **No visitor-facing front door.** The repo is dense with *inward-facing* process docs (ROADMAP, DEFERRED, CLAUDE.md) but a recruiter or hiring manager needs a 30-second README: one-sentence pitch, an annotated screenshot of a generated essay page, a direct link to a live Wikipedia edit, and a "here's the output without cloning." Right now the discipline is real but reads as internal. **This is the highest-leverage single change** — it costs an afternoon and changes first impressions completely.

2. **The central claim is unproven (B2 / D061).** Model-agnosticism is the intellectual centerpiece and it is asserted, not demonstrated. A benchmark table — *Haiku 4.5 and Sonnet 4.6 both pass the same `validate` gate at these token costs* — would convert the design doc into evidence. For a portfolio, this is the difference between "nice essay" and "this person proves their claims." Build D061 specifically because it is portfolio gold, not just engineering hygiene.

3. **A latent defect undercuts the rigor story (A1).** A reviewer who reads the LLM layer closely will find that prompt caching is silently dead on the default model (1024 vs 4096 token minimum). In a project whose brand is rigor and cost-awareness, shipping a cost optimization that doesn't fire is the kind of thing that gets noticed. Fixing it *and* adding the `cache_read > 0` verification warning is a small change that demonstrates exactly the discipline the project claims.

4. **No visible quality signals.** Tests exist, but a reviewer skimming the repo can't see a green CI badge, a coverage number, or a one-command `make test`. Portfolios benefit disproportionately from *visible* quality proof. Add CI + a badge; surface the historian `validate 8/8` gate prominently as evidence the research claims are checked, not vibes.

5. **Setup friction (D056/D057).** The two-repo split with a manual `MARKERY_ROOT` export and a non-isolated venv means a reviewer who tries to run it may stumble. Either make it trivially runnable or lean into "here is the output, no run required" (which #1 solves anyway).

6. **A brittle seam (C1 / D062).** The langgraph integration scrapes prose from stdout. A reviewer reading that file will note it; the `--json` fix demonstrates interface-design maturity and closes the gap.

### Positioning recommendations

- **Lead with the verifiable output, not the architecture.** Open with the live Wikipedia edits and a generated essay screenshot; let the architecture be the second thing they discover. Concrete results earn the right to a design-doc read.
- **Publish the model-agnosticism framework as a short write-up.** It is a differentiated opinion on AI engineering and would stand on its own as a blog post or a linked DESIGN.md excerpt. It signals that you *think* about AI systems, not just wire them.
- **Name the process discipline explicitly.** The phase gates, the contract versioning, and the reopen-triggered deferred register are senior signals that are currently buried. Call them out in the README as deliberate engineering choices.
- **Have the provenance answer ready.** One paragraph, in the README: "This is AI-orchestrated development; here are the decisions that are mine — the tier model, the MVO/model-agnosticism framework, the CLI-as-test-harness thesis, the human-gate altitude." Owning that framing turns the obvious reviewer question into a strength.

### Bottom line

As a portfolio piece, Markery is in the **top tier of what a solo applied-AI project can demonstrate**: original problem, coherent architecture, articulated AI-engineering principles, real process discipline, and externally-verified output. Its weaknesses are uniformly **"polish and prove," not "fundamental gaps"** — a missing front door, an unproven central claim, a latent cost bug, and absent quality-signal surfacing. Closing items #1–#3 above would move it from "impressive internal project" to "a portfolio that argues, and substantiates, a clear thesis about how to build AI systems." That thesis — that careful task design makes capable systems model-portable and cost-checkable — is worth making loudly, because it is both correct and uncommon.
