# Precision Tools — Research Record

**Phase 23 P2 — second project built end-to-end with a free model.** Every LLM
step (candidate inference, essay drafting) ran on `openai/gpt-oss-120b:free` via
OpenRouter. Total LLM cost: **$0.00** (`markery tokens report` over
`projects/precision-tools/tokens.jsonl` confirms $0.0000).

## Entities and data

Target entities (CPC scope **G01B** only — measuring instruments, 1910–1940):
L.S. Starrett Company (35), Brown & Sharpe Manufacturing (36), Snap-on Tools
Company (37), Illinois Tool Works (38).

`markery patent build --classes G01B --year-start 1910 --year-end 1940` loaded
the corpus (`coverage-check` projected ~3,770; **3,766** added). The EPO throttle
fix from P1 (`epo_client.py`, 2.5 s rate, 403/429/503 retried) held — the fetch
ran clean in one pass.

`markery matchmaker suggest-variants` surfaced the exact owner/assignee strings;
`validate-variants` matched **14/14**. The local data splits the four entities
into two useful and two one-sided:

- **L.S. Starrett** — 6 marks, 29 patents (`STARRETT L S CO`). Both sides present;
  the project anchor.
- **Illinois Tool Works** — marks + 10 patents (gear/hob-testing machines). Both
  sides present, but see the anachronism finding below.
- **Brown & Sharpe** — 26 micrometer/caliper patents (`BROWN & SHARPE MFG`) but
  **no Brown & Sharpe mark in the local DB** (the "BROWN COMPANY" hits are a paper
  company — a false match). No pair possible locally.
- **Snap-on** — marks (`SNAP-ON INCORPORATED`) but **no G01B patents** (Snap-on's
  goods are wrenches → B25B, deferred per D026). No pair possible locally.

`markery match precision-tools` (entities 35, 38 in scope) → **62 candidates**.

## Free-model review (gpt-oss-120b:free)

`markery historian infer-queue` ran the whole unreviewed queue through the free
model in one batch. It discriminated on goods, as in P1:

| Pair | Patent | Model call | Note |
|---|---|---|---|
| (figurative) ↔ US1419306A | Indicating Surface Gauge (Starrett) | **confirm/5** | Starrett mark + Starrett measuring-instrument patent |
| (figurative) ↔ US1438617A | Steel Rule With Holder (Starrett) | **confirm/5** | same; tightest date gap (0.7 y) |
| (figurative) ↔ US1384105A | Fine-Adjustment Bevel-Protractor (Starrett) | **confirm/5** | same; widest gap (2.1 y) |
| MAGNAFLUX ↔ US2124119A | Gear Testing Machine (ITW) | **reject/2** | magnetic-testing apparatus vs mechanical gear tester — goods don't correspond |
| INDIAN HEAD ↔ US1858840A | Hob Tester (ITW) | **reject/2** | goods unrelated |
| DE VILBISS / DYKEM ↔ ITW patents | various | **reject/2** | goods unrelated |
| MAGNAFLUX ↔ US1858840A/US1846270A | Hob Tester (ITW) | **confirm/4** | model confirmed — but see the anachronism finding |

The free model again rejected most paper/coating/spray brands on machine-tool
patents on goods grounds — the same goods-aware judgment seen in P1.

## Key finding 1 — the period-ownership anachronism (a new human-gate class)

The ITW candidates exposed a failure mode the P1 project did not. Several marks
the free model confirmed on ITW patents — **MAGNAFLUX, DYKEM, DE VILBISS, INDIAN
HEAD** — carry the trademark-owner string `ILLINOIS TOOL WORKS INC.` in the DB
because ITW acquired those brands **decades later** (Magnaflux Corp., founded
1934, was acquired by ITW in 1987). The marks were **not** owned by ITW in the
1920s–30s when the paired patents issued.

The deterministic validator would **pass** these pairs: the mark's current owner
and the patent's assignee both map to entity 38, so `no_cross_contamination` and
`entity_recognised` hold. But the pairing is historically false — mark and patent
were never co-owned at the time. **This is a new human-gate class beyond P1's
interpretive overclaims: a factual-looking attribution the validator cannot catch
because the owner string is literally correct *today*.** These ITW pairs were
rejected in human review on period-ownership grounds. (`ILLINITE`, owner
`ILLINOIS TOOL WORKS` with no "INC.", *is* a genuine 1937 ITW mark, but its pair —
cutting-tools brand ↔ a hob-testing machine, 4.8 y gap — is a loose goods match
and was not pursued.)

The project was therefore anchored on **Starrett**, which was never acquired:
its marks and patents are genuinely co-owned and contemporaneous.

## Key finding 2 — owner-and-era, not goods-match (and the validator's limit again)

All three Starrett pairs use one **figurative** mark (serial 71185153, filed 1923)
whose registered goods are Starrett's **hand-tool line** — punches, clamps,
nippers, pliers, saws, scrapers, screwdrivers, scribers, wrenches, vises. The full
goods list (confirmed via `markery trademark inspect`) contains **no rules,
gauges, or protractors** — so the three paired patents (a surface gauge, a steel
rule, a bevel-protractor — all measuring instruments) are **not within the mark's
goods**. These are **owner-and-era** pairs, not goods matches.

The free model drafted all three essays and they **validate 8/8** — but every
draft overclaimed "The Connection," asserting the patented instrument "provides
the fundamental measuring principle that underlies" the mark's hand tools, and two
drafts invented trademark "Class 6 / Class 8" attributions absent from the record.
As in P1, the validator certified the facts (serial, patent, dates, owner, no
cross-contamination) but not the interpretation. All three Connections were
rewritten by hand to honest owner/era framing — noting explicitly that the patent
is not among the mark's goods — each with a transparent editorial note. (A nice
honest detail kept in: the mark's USPTO **design codes** 170701/170708 fall in the
"measuring and controlling instruments" category, so the device's *imagery* evokes
measurement even though its *goods* are hand tools.)

## Status

- ✅ Project built entirely on the free model: **3 confirmed pairs** (L.S.
  Starrett), all essays **8/8**, site clean (`site check`: 11 pages, 106 links,
  0 broken), **$0.00** LLM cost.
- ✅ Full EPO **G01B** 1910–1940 corpus fetched (3,766 patents) in one clean pass.
- ✅ Two new findings strengthening the model-agnosticism thesis: (1) a
  period-ownership anachronism class the validator cannot catch (later-acquired
  brands), and (2) the owner-and-era vs goods-match distinction, with the free
  model's connection-overclaim caught by the human gate — as in P1.
- 🛠 Fixed a publisher bug surfaced by this project: figurative marks
  (`trademark = NULL`) crashed `site build` (`landing.py`/`essays.py`/`queries.py`
  dereferenced the null mark text); now fall back to "(figurative)".
- ⏳ `search-tsdr` (D028) pending an ODP/ID.me key — not needed here (marks were
  local) but would streamline future projects.
