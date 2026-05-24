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
