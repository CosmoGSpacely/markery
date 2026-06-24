# Library — A Real Digital Library for Markery (Plan)

Make Markery's library a single, rights-curated digital library that holds **everything
acquired from elsewhere** — secondary-literature works + excerpts **and** public-domain /
free-licensed media — each catalogued with provenance, license, and attribution. The
**record-intrinsic images** (trademark mark drawings, patent figures) stay with their
records in the databases. Projects *reference* library items; the publisher assembles a
site from library references + records.

Status: planning. No code yet. Archived to `archive/` on completion.

---

## 1. Principle (the dividing line)

Sort by **provenance**, not by media-vs-text:

- **Library** = content Markery **acquired from a third party** and had to clear rights
  for → needs a catalog record (source, license, rights basis, attribution). Holds:
  **works** (book/article text + curated excerpts) and **media** (photos, maps, drawings,
  newspaper clippings, PD books).
- **Records** = the USPTO/EPO primary source itself → travels with its DB row, rendered
  straight from the database. Holds: `mark_images` (trademarks.duckdb), `patent_figures`
  (patents.duckdb). No rights-curation to *store/show* (public records); the merch/print
  rights check stays a **use-time** gate (dead + PD), not a reason to relocate them.
- **Leads** = references to things we may *not* keep (eBay listings, market signals) →
  a project's research-leads log, **never** the library.

---

## 2. Current state (the fragmentation to fix)

- **Root `library/`** (global) holds **text works only**: `works/<slug>/`
  (metadata.json + raw_text.txt[gitignored] + excerpts.md + index.md), `index.jsonl`
  (passage-level keyword index), `index.duckdb` (embeddings), `wants.jsonl`. 13 works.
  Projects point at works via `references/` `see:<slug>` pointers — the global+reference
  pattern already works for text.
- **P2 media is per-project**: `projects/<name>/library/media/<slug>/` (metadata.json +
  file) + `library/media/index.jsonl`. Only **1 item** exists (precision-tools demo).
- **Record images live in the DBs**: `mark_images` (619), `patent_figures` (38).

Problems: two things called "library" at different scopes; media siloed per-project and
nearly empty; no single catalog spanning works + media.

---

## 3. Target model

### 3a. One global library, two collections
```
library/
├── README.md
├── catalog.jsonl        NEW — one row per library ITEM (work or media): the card catalog
├── index.jsonl          passage-level keyword index (text works) — unchanged
├── index.duckdb         passage embeddings — unchanged
├── wants.jsonl          ILL/acquisition queue — unchanged
├── works/<slug>/        text works (as today: metadata.json, raw_text, excerpts.md, index.md)
└── media/<slug>/        NEW HOME — media items moved here from projects/*/library/media/
    ├── metadata.json    provenance/license/attribution (the P2 schema, already good)
    └── <slug>.<ext>     the asset (gitignored if large/binary policy says so)
```
- `works/` stays exactly as is.
- `media/` becomes a **global** collection (move the per-project P2 media here).
- `catalog.jsonl` is the unifying **item catalog** — every library item, both kinds, with
  the common fields below — so the whole library is listable/searchable in one place.

### 3b. Catalog record (common fields, per item)
`id` (slug) · `kind` (`work` | `photo` | `map` | `drawing` | `clipping` | `book`) ·
`title` · `creator/author` · `date` · `source` (commons/loc/ia/gutenberg/…) ·
`source_url` · `license` (PD/CC0/CC-BY/CC-BY-SA/…) · `license_url` · `rights_statement`
(verbatim) · `attribution_text` · `acquired_at` · `sha256` · (media) `file`, `format`.
The existing work `metadata.json` and media `metadata.json` already carry most of this;
`catalog.jsonl` is their union, one row per item.

### 3c. Projects reference, they don't own
- A project declares the library items it uses (extend the existing `references/` `see:`
  pattern to media, or a small `references/library.jsonl` of `{id}`); an item can be
  referenced by **many** projects with no duplication.
- `[[media:<id>]]` and work cross-links resolve against the **global** library at build.
- **Build:** the publisher resolves a project's referenced media → copies the files into
  `site/<project>/media/` and builds the `media_index` from the global catalog (today it
  reads `projects/<name>/library/media/index.jsonl`; switch to global + project refs).

### 3d. Records unchanged
`mark_images` / `patent_figures` stay in the DBs and render from there (cards, detail,
`[[figure:patent_no]]`). The print/merch eligibility gate stays use-time.

---

## 4. Admission policy (what the library accepts)

- **Media:** PD / CC0 / CC-BY / CC-BY-SA only (the P2 decision), provenance + license
  captured; reject NC/ND/restricted/unresolved.
- **Works:** acquired bibliographic items; `raw_text.txt` stays **gitignored** (re-acquirable,
  avoids redistributing full copyrighted text); only curated `excerpts.md` (quote-length,
  cited) are durable.
- **Never:** eBay/lead content (no rights to store) → project leads log.

---

## 5. Migration (small today, but sets the shape)

1. Add `library/media/` and move `projects/precision-tools/library/media/illustration-of-a-combination-square/`
   into it; delete the per-project `library/media/` tree.
2. Generate `library/catalog.jsonl` from existing `works/*/metadata.json` +
   `media/*/metadata.json`.
3. Record precision-tools' reference to the moved media item (`references/`), so the build
   still embeds it.
4. Repoint code (§6) from per-project media to global library + project references.
5. Rebuild; confirm the precision-tools landing still shows the combination-square figure
   with attribution and `site check` stays clean.

---

## 6. Code changes

- `librarian/media.py`: `media_dir()` → global `ROOT/library/media`; acquisition writes to
  the global catalog (drop `--project` from *acquire*; add a `librarian use <id> --project`
  to record a reference, or fold into `media-acquire --project` = acquire-global-then-ref).
- `librarian/cli.py`: `media-list` lists the global library; add catalog write; keep
  `media-search`.
- A `catalog` reader/writer in the librarian (one place that maintains `catalog.jsonl`).
- `publisher/build.py`: build `media_index` from the global library + the project's
  references; copy referenced files into `site/<project>/media/`.
- `common/project.py`: a `references` accessor for library items (works already use
  `references/`).

---

## 7. Why this matters for the platform

The library becomes the **shared asset substrate the autonomous loops grow**: the
discovery loop (`HISTORIAN_REVIEW`) deposits rights-cleared works/media into one catalog;
the spawning pipeline (`PUBLISHER_REVIEW`) creates projects that *reference* library items;
the publisher assembles sites from references + records. A real, single, rights-curated
library is exactly what a digital-library-shaped platform needs underneath — and it removes
the per-project media silo that made the current setup look like hard-coded channels.

---

## 8. Phased plan

- **P1 — Global media collection + catalog.** Add `library/media/` + `catalog.jsonl`;
  migrate the one P2 item; `media.py`/`media-list` global. Tests for catalog read/write.
- **P2 — Project references + build.** Reference mechanism; publisher builds `media_index`
  from global library + refs; rebuild precision-tools clean.
- **P3 — Unify listing/search.** `librarian list`/`search` span works + media via the
  catalog; `card` context includes media.
- **P4 — Wire to the loops.** Discovery-loop acquisitions land in the global library;
  spawned projects get reference lists. (Depends on the loops being built.)

Gate per P: command works with mocked HTTP where relevant; `markery site check` stays
green; the migrated media still renders with attribution.

---

## 9. Open questions — RESOLVED 2026-06-24

1. **Reference mechanism: a dedicated `references/library.jsonl`** — one row per
   referenced library item id; simplest for the build to consume. (Not `see:` lines.)
2. **Binary policy: gitignore media** — treat `library/media/` files as re-acquirable
   (like `raw_text.txt` and the Phase 28 `data/assets/`). Only the catalog metadata
   (provenance/license/attribution) is committed; the binaries are rebuildable.
3. **Catalog vs index: JSONL only, no database yet** — keep `catalog.jsonl`
   (item-level) + `index.jsonl` (passage-level) as flat files. Do **not** fold media
   into a DuckDB catalog table for now (revisit if/when querying needs demand it).
4. **Acquire UX: global acquire + separate `use --project`** — `media-acquire`
   fetches once into the global library + catalog (no project); `librarian use <id>
   --project <name>` appends the id to that project's `references/library.jsonl`.
   Chosen because it scales (one acquire → many project references, no duplication)
   and fits the historian loop (acquire into the shared substrate before projects
   exist; clean acquire-vs-reference dedup and loop nodes). A one-shot
   `media-acquire --project` may be added later as thin sugar (acquire-then-`use`).
