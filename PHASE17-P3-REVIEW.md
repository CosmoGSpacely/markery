# Phase 17 P3 — Code Gap Analysis Work Plan

Scope: verify every known gap from Phases 14–17 is correctly represented in DEFERRED.md; grep-audit the implementation for unreported gaps; cross-reference CLI inventory against dispatchers; check test coverage; verify schema and historian cards.

Gate: `DEFERRED.md` updated with all newly discovered gaps; every open entry has a valid reopen trigger; no command in `--help` output is unimplemented without a DEFERRED entry.

---

## Substage A — DEFERRED.md entry verification

For each D-number named in ROADMAP P3, confirm: (1) present in DEFERRED.md, (2) description matches current code state, (3) reopen trigger is still actionable.

### A1 — Matchmaker gaps (Phase 16 P5, 16.1 P1)

| D# | Expected description | Verify |
|---|---|---|
| D035 | CSV comma-in-name mis-parse in `matchmaker build` | Check entry text matches; confirm trigger references Phase 17 P3 |
| D037 | `matchmaker clear` — no remove path for entity rows | Confirm trigger; verify `build` is still idempotent-add-only (grep for DELETE in matchmaker/) |
| D027 | `markery project onboard` — integrated new-project workflow | Confirm trigger says "third project setup" (has been met: animal-marks is third — evaluate whether to promote) |
| D039 | `suggest-variants` shows counts only, no patent titles | Check trigger is still "Phase 17 P3 or second false-positive collision" |
| D031 | `class_score` hardcodes information-systems CPC classes | Verify fix design is still accurate in DEFERRED; note Phase 16.1 P4 confirmed the scoring inversion with measurement |

### A2 — Historian gaps (Phase 16 P6, 16.1 P4)

| D# | Expected description | Verify |
|---|---|---|
| D029 | `matchmaker confirm` — non-interactive pair confirmation | Check trigger; D029 and Phase 18 P5 are the dependency |
| D030 | `historian simulate` — model simulation CLI command | Check trigger; should reference Phase 18 P5 |
| D041 | Figurative mark `None` crash — systematic audit of `c['trademark']` references | Verify audit scope in entry covers: `scaffold`, `validate`, `confirmed.jsonl` writer in historian/cli.py. Two spot-fixes applied (digest formatter, `_slug_matches_trademark`); publisher/queries.py fix also applied. Entry should name all remaining unchecked code paths. |

### A3 — LIBRARIAN gaps (Phase 16 P7, 16.1 P5)

| D# | Expected description | Verify |
|---|---|---|
| D032 | `librarian review --auto-accept` — non-interactive accept | Confirm trigger; recurred in Phase 16.1 P5 — check if entry notes both occurrences |
| D033 | `librarian index` silent zero-passage warning | Confirm trigger; check if the fix would require `_parse_excerpts()` change in `index.py` |
| D044 | `librarian acquire` rejects search-sources suggested slug | Confirm trigger references Phase 17 P2/P3 — both have now passed; update trigger to "next librarian acquisition session" |

### A4 — Trademark / patent gaps (Phase 16.1 P2, P3)

| D# | Expected description | Verify |
|---|---|---|
| D038 | `enrich` stores raw JSON, structured fields NULL | Check trigger; note pre-candidate enrichment gap (no `enrich-project` before candidates exist) — confirm whether this secondary gap is documented in entry body or needs a separate D# |
| D036 | `markery trademark mark-status` — live/dead/PD report | Check trigger; Phase 16.1 P2 is the origin — already passed, update trigger to "second project with dead-mark objective" |
| D034 | `markery trademark design-search` CLI command | Confirm trigger; Phase 16.1 P1 is the origin — already passed, update trigger to "second visual-element-first project" |
| D028 | `markery trademark search-tsdr` — text search | Confirm trigger unchanged |
| D040 | `patent signals` spec ordering — signals requires candidates | Confirm trigger references Phase 17 P2 (has passed); update to "next phase P3 template revision" |

### A5 — Publisher / scoring gaps (Phase 16.1 P4, P6)

| D# | Expected description | Verify |
|---|---|---|
| D042 | `markery match --serials` ad-hoc flag | Verify entry notes partial close: project-config `focus_serials` (Phase 17 P1) implemented; ad-hoc flag still deferred |
| D031 | (also Phase 16.1 P4) — GM Name Plate at 0.796, F02B engine at 0.43 | Check Phase 16.1 P4 measurement is noted in DEFERRED entry (it should be — this was the most concrete evidence) |

### A6 — Documentation / newly-filed gaps (Phase 17 P2)

| D# | Expected description | Verify |
|---|---|---|
| D043 | Per-project `model` key in `project.json` | Confirm trigger; D027 reopen condition ("third project") has been met — evaluate D043 similarly |
| D045 | 5 remaining librarian instruction cards | Confirm trigger is "Phase 17 P3 or workflow error from missing card" |

### A6 — Silently-closeable check

Review whether any open D# was resolved by Phase 17 P1 or P2 work and should be marked done:
- D033: was an instruction card note added to `index.md`? (Yes — `index.md` now includes `###` format requirement.) Does that satisfy the entry? The underlying code fix (zero-passage warning in `index.py`) is still unimplemented — entry stays open.
- D040: `patent signals` spec note. Was it addressed in P2 doc pass? (P2 added `signals` context to instruction cards.) Does that satisfy the trigger? Check `coverage-check.md` and `signals` instruction card. The spec-ordering fix in ROADMAP templates is a separate code-doc gap — entry stays open until the P3/P4 template in ROADMAP is updated.
- D044: P2 doc pass noted identifier requirement in `search-sources` output card. Does that satisfy the doc half? The code fix (`acquire` accepting suggested slug) is still unimplemented — entry stays open; update trigger.

---

## Substage B — Implementation grep audit

Run these greps against `src/` and classify each result.

```bash
# Explicit stubs
grep -rn "raise NotImplementedError" src/
grep -rn "TODO\|FIXME\|HACK\|XXX" src/
# Bare pass (may be legitimate — classify, don't assume all are gaps)
grep -rn "^\s*pass$" src/
```

**Classification for each hit:**
- **(a) Intentional stub** — function signature defined, body deferred by design (e.g., abstract method, placeholder for Phase 18 work)
- **(b) Known gap already in DEFERRED** — cross-reference D# in DEFERRED.md
- **(c) Newly discovered** — file a new D# entry

Pay special attention to:
- `historian/cli.py` — D041 audit targets: `scaffold`, `validate`, the `confirmed.jsonl` writer; any remaining `c['trademark']` or `m['trademark']` usage without None-guard
- `matchmaker/score.py` — `PRODUCT_CLASSES` hardcoding (D031)
- `librarian/` — `review` command terminal binding; `acquire` slug resolution (D044)
- `trademark/` — `enrich` structured-field parse (D038)

---

## Substage C — CLI inventory cross-reference

For each of the six specialists, run `markery <specialist> --help` and compare every listed subcommand against:
1. The argparse/dispatch table in `specialist/<name>/cli.py`
2. The instruction cards in `specialist/<name>/persona/instructions/`

**Specialists to check:** `patent`, `trademark`, `matchmaker`, `historian`, `publisher`, `librarian`

Also check top-level: `markery --help` for any registered but unimplemented top-level flags.

**Expected findings (from P2 audit):**
- `librarian review`, `raw-text`, `enter`, `wants-update`, `list` — no instruction cards (D045; cards deferred, commands are implemented)
- All other gaps should already be in DEFERRED

**What to look for:**
- Subcommand in `--help` but no dispatch handler (would raise `AttributeError` or fall through to default)
- Subcommand with a handler that immediately raises `NotImplementedError`
- Subcommand missing from `--help` but present in cli.py (invisible commands — may be intentional)

---

## Substage D — Test coverage audit

### D1 — pytest collection

```bash
python -m pytest --co -q 2>&1 | head -80
```

Compare collected tests against the full command inventory from Substage C. For each command with zero test coverage: file a DEFERRED entry if the gap is significant (commands that write to disk or call APIs have higher priority than read-only display commands).

### D2 — MVO contract audit

Read `tests/benchmarks/mvo.md` and `tests/test_mvo.py` side by side.

For every contract row in `mvo.md`:
- Confirm a corresponding `test_` function exists in `test_mvo.py`
- Confirm the test actually asserts the contract (not just that the command exits 0)

Phase 17 P4 requires adding a `focus_serials` publisher contract row. Confirm it is not already present — if it is, it was added during a prior session; if absent, note it for P4.

Expected gaps (pre-existing, should already be in DEFERRED or P4 scope):
- `focus_serials` gallery rendering — P4 task
- Librarian commands — Phase 15 work; check if MVO covers `librarian card` and `librarian search`

---

## Substage E — Schema audit

### E1 — Assignment table population

Check whether `trademarks.duckdb` has an `assignment` table and whether it is populated.

```bash
python3 -c "
import duckdb
con = duckdb.connect('data/trademarks.duckdb', read_only=True)
try:
    print(con.execute(\"SELECT COUNT(*) FROM assignment\").fetchone())
except Exception as e:
    print('assignment table:', e)
"
```

If the table does not exist or has 0 rows: confirm whether a DEFERRED entry for assignment data import exists. If not, file one. The SOUNDEX ownership research in Phase 16 identified this as a gap.

### E2 — Phase 14–17 schema additions

Verify every table added in Phases 14–17 is mentioned in at least one of: `CONTEXT.md`, `DESIGN.md`, or the relevant specialist's `identity.md`.

Known additions:
- `design_search` table in `trademarks.duckdb` — used in Phase 16.1 P1; check if documented in CONTEXT or trademark specialist
- `library/index.duckdb` — Phase 15 LIBRARIAN; check CONTEXT.md LIBRARIAN section (should be there from P2 pass)
- `extended_marks` enrichment columns — check CONTEXT.md schema table

---

## Substage F — Historian prepare cards

Run `markery historian prepare --help` (if the command exists) and compare its output format against `persona/instructions/`.

The ROADMAP P3 spec item: "Check `markery historian prepare` — verify instruction cards reflect the current output format."

If `prepare` is a subcommand:
- Confirm its output format matches what the instruction card describes
- If no instruction card exists for `prepare`, check whether it should be filed under D045 scope or as a new entry

If `prepare` is not a registered subcommand: note this — the ROADMAP spec references it, which may indicate a stale spec or a renamed command.

---

## Substage G — DEFERRED.md hygiene final pass

After completing A–F:

1. **Stale reopen triggers** — scan every open entry for triggers that reference phases already passed (e.g., "Reopen when: Phase 17 P2 documentation pass"). Update these to the next actionable condition.

2. **Stale path or command references** — check whether any entry references a path, command, or variable name that has since changed (e.g., old specialist paths, renamed commands).

3. **Ordering** — entries currently appear in reverse-chronological order (newest at top). Confirm no entry is orphaned (referenced in ROADMAP but not in DEFERRED, or vice versa).

4. **D027 promotion decision** — D027 trigger is "third project setup hits the same gaps." `animal-marks-1930` is the third project and it did hit the same gaps (D027 triggered during Phase 16.1 P1). Decide: promote D027 to Phase 18 P1 scope, or update the trigger to "fourth project" with a note that the gap recurred.

5. **Enrich-project pre-candidate gap** — noted in Phase 16.1 P2 conclusions: "`enrich-project` reads from `confirmed.jsonl` or `candidates.jsonl` — neither exists at P2 stage." This gap was flagged as "promote to DEFERRED if recurs in a third project." It did recur. Confirm whether a D# covers it; if not, file one.

---

## Substage H — Newly discovered gap filing

For every (c)-classified item from Substage B, and every unmatched item from C, D, E, F:

- Assign the next available D# (currently D046+)
- Write the entry following the standard format: description, why deferred, reopen trigger
- Add to DEFERRED.md

---

## Execution order

Substages are mostly independent but should run in this order to avoid double-work:

1. **A** (DEFERRED verification) — establishes ground truth before grep may surface duplicates
2. **B** (grep audit) — find new gaps; cross-reference against A results
3. **C** (CLI cross-reference) — find command/implementation mismatches
4. **D** (test coverage) — run pytest; check MVO
5. **E** (schema audit) — quick DB queries
6. **F** (historian prepare) — quick command check
7. **G** (hygiene pass) — final cleanup after all findings are in
8. **H** (file new entries) — can run alongside B/C/D/E/F as findings emerge

Total expected output: updated DEFERRED.md entries (corrected triggers, new D-numbers), one or two new D-numbers for newly discovered gaps, and a clear record in this file of what was checked and what was found.

---

## Actual findings (Phase 17 P3 audit — 2026-06-05)

### Substage A — DEFERRED verification

All 21 open D-numbers present in DEFERRED.md. Updates made:

| Entry | Change |
|---|---|
| D041 | Rewrote body with P3 code audit findings: 3 applied fixes confirmed; 2 remaining gaps found (line 219 crash fixed inline; scaffold lines 339/341/354 produce corrupt YAML, deferred to P4). matchmaker confirmed.jsonl writer noted as unaudited. |
| D027 | Noted trigger condition met (animal-marks was third project). Updated trigger to "fourth project / Phase 18". |
| D031 | Added Phase 16.1 P4 measurement (GM G09F 0.796 vs F02B 0.43). Updated trigger. |
| D032 | Added Phase 16.1 P5 recurrence note. |
| D030 | Added Phase 16.1 P4 recurrence note. |
| D043 | Noted trigger condition met (animal-marks was second non-default-model project). |
| D033 | Removed stale P2 trigger reference (P2 doc fix applied). |
| D034 | Removed stale P1 trigger reference (pattern confirmed). |
| D036 | Removed stale P2 trigger reference. |
| D040 | Removed stale P2 trigger reference. |
| D044 | Updated trigger (P2 and P3 doc fixes applied; code fix still unimplemented). |
| D035, D037, D038, D039 | Updated triggers removing "Phase 17 P3 code-gap audit" (now current). |
| **D046 (new)** | Pre-candidate `enrich-project` gap — no CLI path to batch-enrich before candidates exist. |
| **D047 (new)** | `assignment` table absent from `trademarks.duckdb` — confirmed by `SELECT COUNT(*) FROM assignment` → Catalog Error. |

### Substage B — grep audit

`grep -rn "raise NotImplementedError|TODO|FIXME|HACK|XXX" src/` — **0 hits**. Codebase is clean of incomplete-implementation markers.

### Substage C — CLI cross-reference

Full inventory of 6 specialists × all registered subcommands vs. instruction cards:

- **patent** — 8 commands, 8 cards. ✓ Complete.
- **trademark** — 9 commands; `load-supplemental.md` covers `load-events` + `load-foreign` in one card (intentional). ✓ Complete.
- **matchmaker** — 5 registered subcommands, all covered. `entities.md` and `generate.md` are context/background cards, not command cards — appropriate.
- **historian** — 5 commands, 5 cards. ✓ Complete.
- **publisher** — 1 registered subcommand; `enhance.md` and `wikipedia.md` are cross-tool awareness cards for the publisher persona — appropriate.
- **librarian** — 13 commands; 8 cards. 5 missing = D045 (already filed). ✓ Known gap.

**Finding: `markery match` invisible subcommands** — `status`, `rescore`, `auto-disposition`, `preflight` work and have instruction cards but are absent from `--help`. Filed as **D048**.

### Substage D — Test coverage

462 tests collected. Coverage is solid across all specialists. Key findings:

- `markery project init/adopt` — no test file. Low priority (D027 covers the broader onboarding gap).
- `markery enhance` — no test file. Image manipulation; hard to unit-test without fixture images.
- Publisher `focus_serials` rendering — not in MVO or test suite. **P4 task** (already in ROADMAP P4).
- **Librarian MVO contracts** — `mvo.md` documents 4 librarian contracts (index, search, list, card); `test_mvo.py` has 0 librarian test classes. Filed as **D049**.

### Substage E — Schema audit

- `assignment` table: **absent** from `trademarks.duckdb`. Filed as **D047**.
- `design_search` table: documented in `src/markery/specialist/historian/persona/reference/markery-database.md` (schema, column description, example query) and in `src/markery/specialist/trademark/persona/reference/bulk-tables.md`. ✓ No gap.
- `library/index.duckdb`: documented in CONTEXT.md LIBRARIAN section. ✓ No gap.
- `extended_marks` columns: documented in CONTEXT.md schema table. ✓ No gap.

### Substage F — Historian prepare

`markery historian prepare` generates `BRIEF.md`. Instruction card at `historian/persona/instructions/prepare.md` accurately describes the output sections. 20 unit tests in `tests/specialist/historian/test_prepare.py` cover `gather_patent_state`, `gather_trademark_state`, `count_unreviewed`, and `render_brief`. ✓ No gap.

### Substage G — Hygiene

All open D-numbers have forward-pointing triggers. No entries found to be silently closed (all gaps confirmed still open via code inspection or lack of implementation). D027 and D043 trigger conditions have been met; entries updated accordingly. No orphaned or missing entries.

### Substage H — New gap summary

| D# | Description |
|---|---|
| D046 | Pre-candidate `enrich-project` — no batch-enrich CLI path before candidates exist |
| D047 | `assignment` table absent from `trademarks.duckdb` |
| D048 | `markery match` invisible subcommands not in `--help` |
| D049 | Librarian MVO contracts in `mvo.md` have no tests in `test_mvo.py` |

### Inline fix

- `historian/cli.py` line 219: `c["trademark"].lower()` → `(c["trademark"] or "figurative").lower()` — crash guard for figurative confirmed pairs in digest confirmed-pairs summary (D041 audit item 4).

---

## Expected findings (pre-audit prediction)

Based on prior session notes, the audit is expected to find:

- **D044 trigger stale** — P2 has passed; trigger should be updated to "next acquisition session"
- **D036/D034 triggers stale** — originating phases have passed; triggers need forward-pointing conditions
- **D041 audit scope incomplete** — the entry describes the gap but may not enumerate all remaining unchecked call sites in `scaffold`/`validate`/`confirmed.jsonl` writer
- **Enrich-project pre-candidate gap** — not yet filed as a D#; needs one
- **Assignment table** — likely absent or empty; needs a D# if no entry exists
- **D027 promotion decision** — third project has already triggered the condition; entry needs updating
- **0–2 new grep findings** — minor TODOs likely; no major unreported crashes anticipated given the Phase 16.1 live-test coverage

If no findings beyond the expected list surface, P3 can close cleanly after the hygiene pass.
