# Project Context

Markery is a patent-trademark cross-reference tool for early 20th-century American commercial history. Given a company that both patented products and trademarked product names in 1900–1939, it identifies which patents correspond to which trademarks and documents what that correspondence reveals. The analytical unit is a **confirmed patent-trademark pair**, recorded in `projects/<project>/matches/confirmed.jsonl` and developed into research essays in `projects/<project>/content/`.

## Current Focus

`projects/information-systems/` — filing appliances, card-index systems, visible records equipment, 1900–1939. Four entities in the registry (Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease), 2,412 candidate pairs, 3 confirmed pairs, 2 essays.

## Operating Posture

- `candidates.jsonl` is generated on every match run and never edited — all curation goes into `confirmed.jsonl`
- Mark images (`mark_images`) and case status (`mark_case_status`) are fetched selectively, not in bulk
- Generated output (images, PDFs, gallery HTML) is gitignored and regenerable; never commit these

## Next Action

Phases 2, 3, and 4 (P1–P3) are complete. The specialist refactor is done (`specialist/patent`, `trademark`, `matchmaker`, `historian`, `publisher`); the site is live on GitHub Pages with Open Graph metadata; 8 confirmed pairs with essays are published; D006 company-name mark filter is in place.

Next: **D001** — fetch remaining CPC classes (B41J, B41L, G06C, G06K, G09F) via `markery patent build --resume` to expand the patent corpus for typewriter and calculator entities.

## Reference Docs

| Doc | Contains |
|---|---|
| `README.md` | Full schema, match pipeline, entity procedure, project tree, setup commands |
| `STATUS.md` | Current phase, metrics, infrastructure ledger |
| `DEFERRED.md` | Deferred work register with reopen triggers |
| `RESEARCH-AGENDA.md` | Candidate subjects, discovery methodology, key references |
| `RESEARCH.md` | Scholarly framework and literature context |
| `specialist/trademark/TSDR.md` | USPTO TSDR API reference + trademarks.duckdb schema notes and quirks |
| `specialist/patent/EPO.md` | EPO OPS API reference + patents.duckdb and entities.duckdb notes |
| `DESIGN.md` | Architecture decisions — why DuckDB, why three databases, why human curation *(planned)* |
| `research-session.md` | Runnable operations checklist |
| `archive/ROADMAP.md` | Phase plan (Phases 1–4, now complete) |
| `archive/MARKERY_REVIEW.md` | Specialist refactor design record (Phases A–F) |
