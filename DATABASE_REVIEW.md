# Database Layer — Review & Plan

The three DuckDB databases are a solid, real corpus — but they're a **curated, human-seeded
slice** committed as large binaries, with partial provenance and a hand-built entity registry.
For Markery to become a platform that grows itself, the data layer needs: a coverage/expansion
model, automatic entity registration, record-freshness provenance, and a decision on how the
DBs (and the image blobs in them) are stored and reproduced.

Status: planning. No code yet. Archived to `archive/` on completion.

---

## 1. Current state (inventory)

Committed, git-tracked binaries (~70 MB) + `data/patents_fetch_log.json`:

- **`trademarks.duckdb` (46 MB)** — `case_file` **25,473** marks (filing **1900–1939**), 11
  tables: `classification`, `owner` (38,349), `statement` (35,077; goods for 25,411),
  `design_search` (18,790), `us_class`/`intl_class`, `prior_mark`, `owner_name_change`,
  `extended_marks` (543, post-1939 fetched). `mark_images` **619 (2.4%)**, with `fetched_dt`.
  Status via `cfh_status_cd` (≥700 = dead → gates merch). Built from **USPTO bulk CSV**.
- **`patents.duckdb` (20 MB)** — `patents` **80,537** (grant **1890–1940**), `patent_classes`
  **192,864** (CPC), `patent_inventors` 82,323, **23,704** assignees. `patent_figures`
  **38**, with `fetched_dt`. Built from **EPO OPS** (logged in `patents_fetch_log.json`).
- **`entities.duckdb` (4.3 MB)** — `company_entity` **38**, `entity_name_variant` **123**.
  Hand-curated (project `entities.csv`/`variants.csv` → `matchmaker build`).

---

## 2. Issues (what blocks the platform)

1. **Curated slice, no coverage model.** 25K marks / 80K patents is a *filter* around existing
   projects, not the universe (the real 1900–1939 USPTO set is orders of magnitude larger).
   An autonomous "discover a technology area" loop will hit the edge of what's loaded and must
   fetch more — but there's no record of *what's covered* vs not, and no first-class expansion
   path. (`patents_fetch_log.json` is the only coverage trace.)
2. **Entity registry is hand-curated (38).** New projects require a human to write
   `entities.csv`/`variants.csv`. The spawning pipeline can't create projects autonomously
   until entities + assignee/owner variants are **auto-registered from the corpus**.
3. **Record freshness isn't tracked.** `mark_images`/`patent_figures` carry `fetched_dt`, but
   `case_file`/`patents` have **no Markery load/refresh timestamp** — only USPTO's own dates.
   So `cfh_status_cd` (live/dead, which gates print/merch) can silently go stale, and there's
   no refresh cadence.
4. **Image blobs live in DuckDB.** `mark_images.image_data` / `patent_figures.figure_data` are
   the reason the DBs are 46 MB / 20 MB. This couples the *record* DBs to *binary assets* and
   bloats every commit. Decision needed, and it interacts with the Library phase (records keep
   their own images — but *as DB blobs or as files referenced by the DB?*).
5. **DBs are committed binaries → reproducibility + git bloat.** Each data change (e.g. fetching
   360 design-mark images) rewrites a multi-MB binary in history. The rebuild path exists
   (`trademark build` from CSV, `patent build` from EPO) but the **source inputs aren't in the
   repo**, so the committed DBs are effectively un-reproducible artifacts. Ties directly to
   `TESTS_REVIEW` (hermetic CI shouldn't need the real DBs).
6. **Schema coherence (lower priority).** Review redundancy and the `extended_marks` vs
   `case_file` duality; confirm the 11 trademark tables are all earning their keep.

---

## 3. Target model / decisions

- **Coverage manifest + expansion path.** A first-class record of what the corpus covers
  (classes, date ranges, assignees/owners, per-source counts) so the loops know the edge and
  can request expansion. Expansion routes: EPO OPS / TSDR on demand (the loops), and/or the
  deferred **PatentsView bulk** (D007) for breadth. The loops own *fetching*; the DB owns
  *knowing what it has*.
- **Auto entity registration.** Derive `company_entity` + `entity_name_variant` from corpus
  owner/assignee strings with variant ranking (`matchmaker suggest-variants` already exists);
  the spawning pipeline calls this instead of hand-written CSVs. Keep a human-confirm gate.
- **Record provenance + refresh.** Add a Markery `fetched_dt`/`source` to record loads and a
  `markery <specialist> refresh` to re-pull status for project-scope records (so the merch
  gate and live/dead reports stay honest); track a refresh cadence.
- **Asset storage decision (record images).** Keep mark/patent images as BLOBs in DuckDB
  (simple, travels with the record) **or** externalize to files referenced by the DB (smaller
  DBs, git-friendlier, aligns with the library's file-based assets). Settle this *with* the
  Library phase since they share the "where do assets live" question.
- **Reproducibility / commit policy.** Decide: keep committing the DBs (convenient, but binary
  bloat) or treat them as rebuildable artifacts (gitignore + a documented, repeatable build
  from versioned source). Either way: a documented rebuild recipe and a small **synthetic
  fixture DB** for hermetic tests/CI (per `TESTS_REVIEW`).

---

## 4. Phased plan

- **P1 — Provenance + freshness.** Add record load `fetched_dt`/`source`; `… refresh` for
  status; coverage counts surfaced (extend `patents_fetch_log` into a real coverage manifest).
- **P2 — Auto entity registration.** Corpus → `company_entity`/`entity_name_variant` with
  variant ranking + human-confirm; remove the hand-CSV requirement for new projects. (Direct
  dependency of the spawning pipeline.)
- **P3 — Asset storage + DB commit policy.** Resolve blobs-in-DB vs files (with the Library
  phase); decide commit-vs-rebuild; document the rebuild recipe; add the synthetic test fixture.
- **P4 — Coverage/expansion hooks.** A queryable coverage model the discovery/spawning loops
  consult before fetching; wire EPO/TSDR expansion (and evaluate D007 PatentsView) behind the
  loops' budget/gates.

Gate per P: deterministic, tested against a temp/synthetic DB; no regression in existing
specialist commands.

---

## 5. Placement & dependencies

Sits in the foundations, **after Tests, before Library** — it's the deepest backbone and its
asset-storage decision (P3) must be made *with* the library refactor. P2 (auto entity
registration) is a hard prerequisite for the spawning pipeline; P1/P4 (provenance, coverage)
underpin the discovery loop's acquisition.

```
Tests → Database → Library → Discovery loop → Spawning pipeline
```

---

## 6. Open questions

1. **Commit vs rebuild the DBs?** Keep ~70 MB binaries in git, or gitignore + rebuild from
   versioned source (and where does the source live)? (Lean: stop committing the large blobs;
   keep a small synthetic fixture in-repo; document/automate the rebuild.)
2. **Record images: DB blobs or files?** (Lean: externalize to files referenced by the DB —
   shrinks the DBs, aligns with the library's file assets — but confirm the publisher/print
   paths are fine reading from files.)
3. **Expansion engine:** EPO/TSDR on-demand only, or adopt PatentsView bulk (D007) for breadth?
4. **Refresh cadence:** how often to re-pull trademark status (the merch/live-dead gate) — and
   is that a `dataqa`/scheduled job rather than on every build?
