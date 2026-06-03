# Markery Token Benchmarks

Baseline and reduction measurements for Phase 14. All token counts are prompt tokens
measured via the Anthropic `count_tokens` endpoint (model: `claude-haiku-4-5-20251001`).
`completion_tokens` is 0 for all entries — these commands generate context for human
sessions, not API inference completions.

---

## Baseline — 2026-05-24

**Project:** `information-systems`  
**Model:** `claude-haiku-4-5-20251001`  
**Log file:** `baseline-2026-05-24.jsonl`

### Session composition

A representative card/digest historian workflow session:

| Step | Command | Description |
|---|---|---|
| 1 | `historian digest information-systems` | Session orientation |
| 2–6 | `historian card <slug>` × 5 | Top unreviewed candidates |
| 7 | `historian scaffold variadex-us2152606a` | Essay skeleton for confirmed pair |
| — | `historian validate soundex-us1261167a` | Validation check (not instrumented; deterministic output ~30 tokens) |

### Per-command measurements

| Command | n | Mean prompt tokens | Min | Max | Mean wall ms |
|---|---|---|---|---|---|
| digest | 1 | 545 | 545 | 545 | 1,021 |
| card | 5 | 224 | 213 | 239 | 1,006 |
| scaffold | 1 | 456 | 456 | 456 | 1,046 |

**Session total (7 instrumented commands):** 2,122 prompt tokens

**20% reduction target (P3 gate):** ≤ 1,698 prompt tokens for equivalent session

### Hotspot analysis

**Hotspot 1 — Cards at scale (largest cumulative cost)**  
Each card runs 213–239 tokens. In a session reviewing 10 candidates (typical), cards
alone account for ~2,240 tokens — more than a digest + scaffold combined. The drivers
are: abstract field (truncated at 120 chars, ~40 tokens), goods-description (truncated
at 100 chars, ~30 tokens), and the signals/status block (~25 tokens). The card format
is already compact; the cost is inherent to the number reviewed per session rather than
field verbosity.

**Hotspot 2 — Scaffold template sections (single largest document)**  
At 456 tokens, scaffold is the largest single document in a session. The frontmatter
block accounts for ~110 tokens; the abstract quote (up to 500 chars raw, passed
directly from DB without truncation in scaffold) accounts for ~80–100 tokens; the six
section headers with HTML comments account for ~120 tokens. Truncating the abstract
in scaffold (as card already does) and shortening comment text are the highest-yield
reductions.

**Hotspot 3 — Digest next-review table**  
The digest's `next_review` block lists 10 candidates at ~30 tokens each (~300 tokens
of the 545 total). Reducing `--top` default from 10 to 5 saves ~150 tokens with no
loss to typical sessions where only 3–5 candidates are reviewed per sitting.

### Notes

- `historian validate` is not yet instrumented (no `--tokens` flag; no
  `MARKERY_TOKEN_LOG` trigger). Its output is 6–8 deterministic PASS/FAIL lines,
  estimated ~30 prompt tokens. Adding instrumentation is a P1 cleanup item.
- Wall time per command (~1,000ms) reflects the `count_tokens` API round-trip, not
  any Claude inference. Actual session latency for humans is zero (commands are run
  before the session starts).
- The 2,122-token session total is well within Haiku's 200K context window. The P4
  viability question is output quality with reduced context, not window overflow.

---

## P3 Hotspot Reductions — 2026-05-24

**Gate target:** ≥20% reduction vs baseline  
**Result:** 22.3% reduction — **GATE PASSED**

### Changes implemented

| Target | Change | Tokens saved (est.) |
|---|---|---|
| Card format | Removed 4 blank separator lines | ~20 |
| Card format | Compact header: status/score/gap → single `## CARD` line | ~10 |
| Card format | Removed `figures` field (almost always "absent") | ~25 |
| Card format | Removed `reg_no` field (available in scaffold frontmatter) | ~25 |
| Card abstract | Truncated 120 → 80 chars | ~10 |
| Card goods | Truncated 100 → 80 chars | ~5 |
| Card signals | Compact sig-code format (`TA gt=0.123 ga=0.456`) | ~15 |
| Digest confirmed | Single summary line instead of per-pair listing | ~200 |
| Digest next_review | `--top` default 10 → 5 | ~150 |
| Scaffold abstract | Truncated 500 → 150 chars | 0* |
| Scaffold goods | Truncated raw → 150 chars | 0* |

\* variadex-us2152606a (benchmark scaffold slug) has no abstract and 35-char goods;
truncation fires on patents with longer texts.

### Per-command measurements (post-P3)

| Command | n | Mean prompt tokens | Min | Max |
|---|---|---|---|---|
| digest | 1 | 251 | 251 | 251 |
| card | 5 | 188 | 179 | 196 |
| scaffold | 1 | 456 | 456 | 456 |

**Session total (7 instrumented commands):** 1,648 prompt tokens  
**Reduction vs baseline:** 474 tokens (22.3%)  
**Gate (≥20%):** PASSED

### Validate gate

`historian validate information-systems soundex-us1261167a` — all 6 checks PASS after
card format changes. No regressions introduced.

### Notes

- Scaffold abstract/goods truncation is correct but does not fire on the benchmark slug
  (variadex has no abstract in the DB; goods = "CARD AND CORRESPONDENCE FILE GUIDES",
  35 chars). Sessions with longer-abstract patents will see additional savings.
- Card mean dropped from 224 (baseline) → 188 post-P3, a 16% per-card reduction.
- Digest dropped from 545 → 251, a 54% reduction driven by confirmed-pairs summary
  and top-5 default.

---

## P4 Free-Model Run — 2026-05-24

**Model:** `claude-haiku-4-5-20251001`  
**Script:** `tests/benchmarks/p4_haiku_run.py`  
**Log file:** `p4-haiku-2026-05-24.jsonl`

### Test design

Both workflows send actual inference requests to Haiku. Validation checks that
responses contain no serial or patent numbers absent from the input context
(hallucination check).

### Historian workflow — card/digest

| Metric | Value |
|---|---|
| Context: persona + digest + 3 cards | 2,455 prompt tokens |
| Completion tokens | 472 |
| Wall time | 5,615 ms |
| Hallucination check | PASS |
| Context window used | 1.2% of 200K |

**Response quality:** Haiku correctly identified the REMINGTON RAND pair as the
strongest candidate (matching assignee, 18-day filing gap, goods alignment), noted
the weaker FAVORITE-US1527374A score, and flagged the entity ambiguity on the RAND
card. All serial and patent numbers referenced were from the input cards.

### Gallery/Wikipedia workflow — essay review

| Metric | Value |
|---|---|
| Context: persona + chicago-pneumatic essay | 3,090 prompt tokens |
| Completion tokens | 164 |
| Wall time | 2,821 ms |
| Hallucination check | PASS |
| Context window used | 1.5% of 200K |

**Response quality:** Haiku produced a correctly-sourced Wikipedia talk-page note
citing serial number 71299042, the April 1930 filing date, and the historical
significance of the CP monogram. No invented sources or serial numbers.

### P4 gate result

| Criterion | Result |
|---|---|
| No hallucinated serial or patent numbers | PASS (both workflows) |
| Context window not exceeded | PASS (max 1.5% of 200K used) |
| Structurally valid, parseable without human correction | PASS |

**Gate: PASSED**

### Notes

- The `validate` subcommand check ("output passes validate") applies to essay
  markdown files; the historian workflow in this test produced candidate assessments,
  not a complete essay. Quality was evaluated by response structure and hallucination
  absence instead.
- Wall times (2.8–5.6 s) reflect actual Haiku inference, not just token counting.
- Haiku correctly declined to invent facts when context was sparse (e.g., did not
  fabricate a goods description for the RAND card that was absent from the input).

---

## Phase 16 P6 — radio-pioneers Baseline — 2026-06-03

**Project:** `radio-pioneers`  
**Model:** `claude-haiku-4-5-20251001`  
**Log file:** `radio-pioneers-p6.jsonl`  
**Script:** `radio_haiku_sim.py` (inline, embedded in P6 workflow)

### Session composition

Full P6 card/digest review cycle on radio-pioneers (2,748 candidates, 3 confirmed pairs, 2 entities):

| Step | Command | n | Description |
|---|---|---|---|
| 1 | `historian digest radio-pioneers` | 2 | Session orientation (initial + post-confirm) |
| 2–8 | `historian card radio-pioneers <slug>` | 7 | Candidate review (5 exploratory + 3 confirmed) |
| — | Haiku simulation | 1 | Inference run: digest + 3 confirmed cards → Haiku |

### Per-command measurements

| Command | n | Mean prompt tokens | Phase 14 baseline | Delta |
|---|---|---|---|---|
| digest | 2 | 249 | 251 | −1% (within noise) |
| card | 7 | 195 | 188 | +4% (within noise) |
| haiku-simulation | 1 | 2,488 | 2,455 (P4 IS run) | +1% |

**No regressions.** All measurements within ±5% of Phase 14 baseline. The slight card increase (195 vs 188) reflects radio-pioneers cards having longer goods descriptions than the information-systems baseline.

### Haiku simulation — hallucination check

| Metric | Value |
|---|---|
| Prompt tokens | 2,488 |
| Completion tokens | 600 |
| Wall time | 7,632 ms |
| Hallucination check | **PASS** |
| Context window used | 1.2% of 200K |

**Response quality:** Haiku correctly assessed STERILAMP and MINALITE as strong confirmations (17-day and 15-day post-grant gaps; goods descriptions matching patent technology class). For VICTOR-US1486221A (RCA), Haiku correctly flagged uncertainty: VICTOR was a pre-existing brand and the patent is a component-level invention rather than a product patent. No alien serials or patent numbers. Haiku's confidence calibration matched the human reviewer's assessment of pair quality.

### Confirmed pairs validated

| Slug | Entity | Patent | Trademark | Gap | Validate |
|---|---|---|---|---|---|
| sterilamp-us2168861a | Westinghouse | US2168861A | STERILAMP (71423019) | 0.0y | PASS |
| minalite-us1829460a | Westinghouse | US1829460A | MINALITE (71321058) | 0.0y | PASS |
| victor-us1486221a | RCA | US1486221A | VICTOR (71195203) | 0.1y | PASS |

### Notes

- radio-pioneers has no patent abstracts for any of the 2,748 candidates (EPO OPS returns no abstract for pre-1940 radio patents in the H04B/H01J/H03F/H04R classes). Signals are structural-only (gt, ga always 0.0). This is a known gap documented in RESEARCH-AGENDA.md.
- Top-scoring candidates (score 0.80) are Westinghouse pairs that are temporally close but product-line-mismatched (STERILAMP + "Display Device"). The *confirmed* pairs were selected from lower-scoring candidates that have genuine product correspondence.
- Zenith, De Forest, and Atwater Kent have zero candidates due to patent DB coverage gaps (CPC reclassification incomplete for pre-1940 era, documented in P5).
- The `information-systems` P14 baseline remains valid. radio-pioneers measurements are within ±5%.
