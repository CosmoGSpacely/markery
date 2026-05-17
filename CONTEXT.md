# Project Context

Markery is a patent-trademark cross-reference tool for early 20th-century American commercial history. Given a company that both patented products and trademarked product names in 1900–1939, it identifies which patents correspond to which trademarks and documents what that correspondence reveals. The analytical unit is a **confirmed patent-trademark pair**, recorded in `projects/<project>/matches/confirmed.jsonl` and developed into research essays in `projects/<project>/content/`.

## Current Focus

`projects/information-systems/` — filing appliances, card-index systems, visible records equipment, 1900–1939. Four entities in the registry (Remington Rand, Wilson Jones, Yawman & Erbe, Boorum & Pease), 2,412 candidate pairs, 3 confirmed pairs, 2 essays.

## Operating Posture

- `candidates.jsonl` is generated on every match run and never edited — all curation goes into `confirmed.jsonl`
- Mark images (`mark_images`) and case status (`mark_case_status`) are fetched selectively, not in bulk
- Generated output (images, PDFs, gallery HTML) is gitignored and regenerable; never commit these

## Next Action

Phase 2 steps 1–3 complete: `src/markery/` package; `tools/` tree; unified `markery` CLI (`match`, `review`, `status`, `enhance`, `fetch-patents`, `score-signals`). Next: Phase 2 step 4 — move databases to `data/`.

## Reference Docs

| Doc | Contains |
|---|---|
| `README.md` | Full schema, match pipeline, entity procedure, project tree, setup commands |
| `STATUS.md` | Current phase, metrics, infrastructure ledger, phase gate |
| `DEFERRED.md` | Deferred work register with reopen triggers |
| `ROADMAP.md` | Phase goals, research agenda, candidate subjects |
| `TSDR.md` | USPTO TSDR API reference + trademarks.duckdb schema notes and quirks |
| `EPO.md` | EPO OPS API reference + patents.duckdb and entities.duckdb notes |
| `RESEARCH.md` | Scholarly framework and literature context |
| `DESIGN.md` | Architecture decisions — why DuckDB, why three databases, why human curation *(planned)* |
