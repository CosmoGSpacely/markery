# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phases 9–13 closed 2026-05-24. Archived to `archive/ROADMAP-2026-05-24.md`.

---

## Phase 14 — Efficiency Baseline: Token and Model Benchmarking

**Opened:** 2026-05-24  
**Trigger:** Phase 13 complete — v0.3.0 tagged, public readiness achieved.  
**Scope:** Measure Markery's current token consumption and model sensitivity across real workflows, then reduce both enough that the gallery-exploration and card/digest historian workflows are completable end-to-end on a free cloud model. This phase closes the gap between the model-agnosticism principle documented in DESIGN.md and the reality of how sessions are run in practice.

**Goal state:** By phase close, the gallery-exploration and card/digest historian workflows complete end-to-end on a free-tier model (Claude Haiku or equivalent) without exceeding its context window or producing hallucinated structured data. Match-review-essay workflows may remain paid-model-preferred.

---

### P1 — Token instrumentation

Add per-command token measurement so every API call is observable without external tooling.

1. Add a `TokenRecord` datatype (model, prompt_tokens, completion_tokens, cache_read_tokens, cache_creation_tokens, wall_ms) to `common/tokens.py`
2. Add `MARKERY_TOKEN_LOG` env-var support: when set to a file path, each API call appends a JSON line to that file (timestamp, specialist, command, TokenRecord)
3. Add `--tokens` flag to the CLI dispatcher: when present, print a summary line to stderr after any command that calls the API (e.g., `[tokens] prompt=1,234 completion=456 cache_read=0 (haiku-4-5)`)
4. Verify: run `markery historian card soundex-us1261167a --tokens` and confirm token counts appear in output

---

### P2 — Baseline sweep

Run the standard session workflow on `information-systems` and record the token profile as the baseline.

1. Set `MARKERY_TOKEN_LOG=tests/benchmarks/baseline-2026-05-24.jsonl` and run the full session sequence:
   - `markery historian digest information-systems`
   - `markery historian card <slug>` for each unreviewed candidate
   - `markery historian scaffold <slug>` for one confirmed pair
   - `markery historian validate <slug>` against the resulting essay
2. Aggregate by command: mean prompt tokens, mean completion tokens, total tokens for the session
3. Record results in `tests/benchmarks/README.md`: baseline table, date, model, session description
4. Identify the top 3 token-cost hotspots (expected candidates: persona system prompts, full candidates.jsonl payload, goods-description fields in candidate blocks)

---

### P3 — Hotspot reductions

For each hotspot identified in P2, design and apply a targeted reduction. Measure the delta after each change.

**Expected hotspot candidates and candidate mitigations:**

| Hotspot | Candidate mitigation |
|---|---|
| Persona system prompt size | Audit each identity.md for redundancy; extract verbose reference sections to separate files loaded only when the relevant command runs |
| Full candidates.jsonl in context | Pass only the top-N candidates by score (configurable, default 20) to any command that enumerates candidates; `digest` already does this but `card` and `scaffold` may not |
| Goods-description verbosity | Truncate statement_text to 150 chars in card and digest output (truncation already applied in card but may not be in digest or scaffold context blocks) |

1. For each hotspot: describe the reduction, implement it, re-run the affected commands with `--tokens`, record the new count
2. Target: ≥ 20% reduction in prompt tokens for the session as a whole vs the baseline
3. No regression in output quality: run `markery historian validate` on essays produced pre- and post-reduction and confirm all-PASS

---

### P4 — Free-model run

Validate that the reduced workflows are completable on a free-tier model.

**Target models:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) as the primary target. Secondary: Gemini Flash or Mistral free tier if Haiku is insufficient.

1. Gallery-exploration workflow: run a full `monthly-image-review` session (select marks, run `markery enhance gallery`, draft a Wikipedia submission via `markery wikipedia from-essay`) with the model set to Haiku
2. Card/digest historian workflow: run `digest` + `card` for three candidates on `information-systems` with Haiku; verify output is structurally valid (serial numbers match DB, no invented candidates)
3. Record token counts for both runs; compare to P2 baseline
4. Define "passes" criteria explicitly:
   - No hallucinated serial numbers or patent numbers (check against DB)
   - Output passes `markery historian validate` or is parseable without human correction
   - Context window not exceeded (no truncation warnings from the model)
5. If Haiku fails on match-review-essay workflow, document the failure mode and note the minimum model tier required

---

### P5 — MVO contracts

Formalize the minimum viable output definition per command so free-model results are testable without human review.

1. Write `tests/benchmarks/mvo.md`: one table row per API-calling command with: command, expected output fields, validation rule (regex, schema check, or DB lookup)
2. Implement `tests/test_mvo.py`: for each command with a defined MVO contract, run the command against a known fixture and check output programmatically
3. Add MVO tests to the CI matrix (separate job so they don't run on every push — only on `workflow_dispatch` or tags)
4. Verify: all MVO tests pass with the primary paid model; note which pass with Haiku

---

### Phase Gate

P1 PASSED when: `--tokens` flag produces accurate token counts on any API-calling command; `MARKERY_TOKEN_LOG` appends valid JSON lines; confirmed against an actual API response.

P2 PASSED when: baseline sweep is complete, `tests/benchmarks/README.md` has a populated baseline table, and the top 3 hotspots are named.

P3 PASSED when: session-level prompt tokens are ≥ 20% below the P2 baseline; `markery historian validate` passes on essays produced post-reduction.

P4 PASSED when: gallery-exploration and card/digest historian workflows complete end-to-end on Haiku without hallucinated structured data or context-window overflow; results recorded in `tests/benchmarks/README.md`.

P5 PASSED when: all MVO tests pass with the primary paid model; `tests/benchmarks/mvo.md` is complete.

Phase PASSED when P1–P5 all pass.

---

## Post-Phase-14 Horizon

### Phase 15 — LIBRARIAN Specialist: Cross-Project Reference Retrieval

Do not begin until both D020 blocking conditions are met: (1) `references/` format proven across two projects with curated excerpts; (2) historian demonstrates a concrete cross-project retrieval need. See `DEFERRED.md` D020 for full design.

---

### Phase 16 — PatentsView Bulk Import

Do not begin until trigger fires: a project with 1976+ scope opens where EPO OPS quota is a genuine bottleneck, or where PatentsView's assignee-name and abstract coverage is needed. See `DEFERRED.md` D007 for full design.
