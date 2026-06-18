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
- Graflex — 1 mark; **32 camera/film-holder patents** (FOLMER GRAFLEX CORP) after the fetch
  (Blair: no usable local records — omitted)

**EPO G03B corpus — complete.** The full 1890–1940 sweep is fetched (+9,031
patents in the final run; ~11k G03B total). The fetch first appeared
"quota-blocked" (repeated HTTP 403) but the 403 was a **rate throttle**, not a
quota: the client sent ~120 search/min against EPO's `search=green:30` (30/min)
budget. Diagnosed via the live `X-Throttling-Control` / `X-RegisteredQuotaPerWeek-used`
headers; fixed in `epo_client.py` (2.5 s rate ≈ 24/min; 403/429/503 retried with
backoff). With the camera-apparatus patents loaded, refined variants to the new
assignees (Graflex `FOLMER GRAFLEX CORP`, Ansco `AGFA ANSCO CORP`, etc.;
validate-variants 14/14) and regenerated: **`markery match` → 11,450 candidates**
across all three entities.

## Free-model review (gpt-oss-120b:free)

The free model showed sound, goods-aware judgment in `historian card --infer`:

| Pair | Patent | Model call | Why |
|---|---|---|---|
| WRATTEN ↔ US940030A | plate-holder (G03B) | **confirm/5** | same owner, 3.5y gap, dry-plate subject |
| CENTURY ↔ US1107358A | camera-stand jack | **confirm/5** | mark's "camera-stand jacks" goods match the patent |
| AZO ↔ US1107358A | (camera patent) | **reject/2** | AZO is photographic *paper*, not a camera — goods don't correspond |
| VELOX ↔ US1107358A | (camera patent) | **reject/2** | same: paper mark vs camera patent |
| ELON ↔ US1066848A | view-finder | **reject/2** | ELON is a *developer*; unrelated to a view-finder |
| RITEWAY ↔ US1900730A | camera back (Graflex) | **confirm/5** | RITEWAY film/plate holders ↔ a camera-back patent; <1y gap |
| MEMO ↔ US2168190A | enlarging apparatus (Ansco) | **confirm/5** | same owner, ~0-day gap (looser goods match — see below) |
| FLEXOGLOSS ↔ US1906931A | motion-picture film gate | **reject/2** | print-treating solution vs a film gate — goods unrelated |

Notably the model **confirms a camera mark and rejects two paper marks on the
same camera patent** — it reasons about goods-correspondence, not just owner +
date alignment. This is the curation quality the model-agnosticism thesis needs.

## Essays

**Four pairs confirmed across all three entities** — Kodak (WRATTEN, CENTURY),
Graflex (RITEWAY), Ansco (MEMO). The free model drafted every essay
(`historian draft`); all **validate 8/8** on the deterministic DB checks (title,
trademark, serial, patent, grant date, filing date, entity, no cross-contamination).
Site builds clean (`site check`: 13 pages, 136 links, 0 broken). Total free-model
cost across both review passes: **$0.00**.

## Key finding — the validator gates facts, not interpretation

The free model's WRATTEN draft **passed all 8 factual checks but overclaimed the
connection** — it asserted the plate-holder patent "underlies the functional
performance" of the WRATTEN consumables, a causal claim stronger than the
evidence (a plate-holder is a general accessory; same owner and era is not a
documented product-patent link). This was caught in human review and revised to
an honest owner/era/subject-level framing, with a transparent editorial note in
the essay. CENTURY's connection (camera-stand patent ↔ camera-stand goods) was
defensible and kept as drafted.

The second review pass reinforced this twice over:

- **MEMO** drew the same overclaim — the draft said the enlarging patent "provides
  the technical foundation" for a MEMO "processing component" and invented
  "patented illumination and focus controls." Revised to an owner/era framing with
  an editorial note. (RITEWAY's connection — film/plate holders ↔ a camera-back
  patent — was tight and kept as drafted.)
- **The validator caught a factual error the free model made:** the RITEWAY draft
  misspelled the entity as "Grafix", failing `entity_recognised`. A human corrected
  it to "Graflex" and it then validated 8/8. This is the deterministic gate doing
  exactly its job — catching a model slip on a checkable fact.

This is the central result of the free-model build: **a free model clears
Markery's factual bar end-to-end at $0 — and when it slips on a fact the validator
catches it — but its interpretive claims still require the human gate.** Facts are
model-agnostic and machine-checkable; judgment is not.

## Status

- ✅ Project built entirely on the free model: **4 confirmed pairs across 3
  entities** (Kodak, Graflex, Ansco), all essays 8/8, site clean (13 pages, 136
  links, 0 broken), **$0.00** LLM cost.
- ✅ Full EPO G03B 1890–1940 corpus fetched (~11k patents) after fixing the
  throttle-403 misdiagnosis; 11,450 candidates.
- ⏳ `search-tsdr` (D028) pending an ODP/ID.me key — not needed here (marks were
  local) but would streamline future projects.
