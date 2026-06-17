# Photographic Equipment — Research Record

**Phase 23 P1 — first project built with a free model.** Every LLM step
(candidate inference, essay drafting) ran on `openai/gpt-oss-120b:free` via
OpenRouter. Total LLM cost: **$0.00** (`markery tokens report` confirms $0.0000).

## Entities and data

Target entities (CPC scope **G03B** only, photographic apparatus):
Eastman Kodak Company (31), Ansco (32), Graflex (33), Blair Camera Company (34).

The marks were **already present in the local `trademarks.duckdb`** — no USPTO
text-search API or serial lookup was needed. `markery matchmaker suggest-variants`
surfaced the exact owner/assignee strings; `validate-variants` matched 10/10:

- Eastman Kodak — 26 marks, 72 patents in the DB
- Ansco — 20 marks, 1 patent
- Graflex — 1 mark, 0 patents (Blair: no usable local records — omitted)

`markery match` generated **1,078 candidates**.

**Patent corpus is partial.** The EPO G03B sweep (12,801 patents, 1890–1940)
fetched windows 1890–1909 (+2,093) before EPO returned HTTP 403 (quota); resuming
on 2026-06-17 still returned 403 (weekly quota). The current candidates pair
Kodak marks with the G03B patents already loaded; the remaining camera-apparatus
patents (1910–1940) will enrich the pool once EPO quota resets (`--resume`).

## Free-model review (gpt-oss-120b:free)

The free model showed sound, goods-aware judgment in `historian card --infer`:

| Pair | Patent | Model call | Why |
|---|---|---|---|
| WRATTEN ↔ US940030A | plate-holder (G03B) | **confirm/5** | same owner, 3.5y gap, dry-plate subject |
| CENTURY ↔ US1107358A | camera-stand jack | **confirm/5** | mark's "camera-stand jacks" goods match the patent |
| AZO ↔ US1107358A | (camera patent) | **reject/2** | AZO is photographic *paper*, not a camera — goods don't correspond |
| VELOX ↔ US1107358A | (camera patent) | **reject/2** | same: paper mark vs camera patent |
| ELON ↔ US1066848A | view-finder | **reject/2** | ELON is a *developer*; unrelated to a view-finder |

Notably the model **confirms a camera mark and rejects two paper marks on the
same camera patent** — it reasons about goods-correspondence, not just owner +
date alignment. This is the curation quality the model-agnosticism thesis needs.

## Essays

Two pairs confirmed; the free model drafted both essays (`historian draft`), and
both **validate 8/8** on the deterministic DB checks (title, trademark, serial,
patent, grant date, filing date, entity, no cross-contamination).

## Key finding — the validator gates facts, not interpretation

The free model's WRATTEN draft **passed all 8 factual checks but overclaimed the
connection** — it asserted the plate-holder patent "underlies the functional
performance" of the WRATTEN consumables, a causal claim stronger than the
evidence (a plate-holder is a general accessory; same owner and era is not a
documented product-patent link). This was caught in human review and revised to
an honest owner/era/subject-level framing, with a transparent editorial note in
the essay. CENTURY's connection (camera-stand patent ↔ camera-stand goods) was
defensible and kept as drafted.

This is the central result of the free-model build: **a free model clears
Markery's factual bar end-to-end at $0, but its interpretive claims still require
the human gate.** Facts are model-agnostic; judgment is not.

## Status

- ✅ Project built on the free model: 2 confirmed pairs, 8/8-validated essays,
  site builds clean (`site check`: 11 pages, 108 links, 0 broken).
- ⏳ EPO G03B fetch quota-blocked at 1910 — resume to add camera patents.
- ⏳ `search-tsdr` (D028) pending an ODP/ID.me key — not needed here (marks were
  local) but would streamline future projects.
