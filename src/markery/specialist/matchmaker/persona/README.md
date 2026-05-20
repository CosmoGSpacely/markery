# Matchmaker Specialist

A Markery specialist agent for managing the entity registry and generating scored patent-trademark candidate pairs. The Matchmaker specialist owns `entities.duckdb` and reads across all three databases to produce `candidates.jsonl` for historian review.

---

## Role

The Matchmaker specialist is a **discovery and scoring agent**. It links canonical company entities to their name variants as they appear in patent assignee fields and trademark owner fields, then scores every possible patent-trademark pair for each entity. It has no confirmation authority — it produces candidates for the historian to evaluate.

---

## Owns

`data/entities.duckdb` — `company_entity` (canonical entity names, type, industry) and `entity_name_variant` (how each entity appears across the two primary source databases).

Reads (via DuckDB ATTACH): `data/patents.duckdb`, `data/trademarks.duckdb`.

---

## Key Commands

```bash
# Load entities and variants from project CSV files
markery matchmaker build --data-dir projects/<project>

# List all entities in the registry
markery matchmaker list

# Entity registry row counts
markery matchmaker status

# Generate candidate pairs for a project
markery match <project>

# Generate + enrich with text signals + rescore (full pipeline)
markery match <project> --full

# Check pipeline state
markery match status <project>

# Rescore existing candidates after signal enrichment
markery match rescore <project>
```

---

## Entity Data Files

Entity and variant data lives in per-project CSV files, not in source code.

```
projects/<project>/entities.csv    — entity_id, canonical_name, entity_type, industry
projects/<project>/variants.csv    — entity_id, variant_name, source
```

`source` in `variants.csv` is either `patent_assignee` (how the name appears in patent records) or `trademark_owner` (how it appears in trademark owner fields).

The build is idempotent — re-running adds new rows and skips existing ones.

---

## How to Use

```
"Add a new name variant for Remington Rand and regenerate candidates."

"What entities are currently in the registry?"

"Generate candidates for the information-systems project and report
 how many pairs are in the uncertainty band."

"The scoring for VI-DEX ↔ US1630977A shows 0.54.
 What is the date gap and class score breakdown?"
```

---

## Reference

| File | Contains |
|---|---|
| `identity.md` | Agent role, capabilities, explicit limits, and scope |
| `instructions/generate.md` | When and how to generate candidates; --full, --force, --min-score, --resolve flags |
| `instructions/entities.md` | Adding entities and name variants; editing entities.csv and variants.csv; source values |
| `instructions/rescore.md` | When to rescore vs regenerate; signal bonus components; pipeline state tracking |
| `instructions/status.md` | Reading match status output; pipeline_state.json fields; review progress |
| `reference/scoring.md` | Scoring formula and component breakdown |
| `reference/uncertainty-band.md` | Uncertainty band definition; signal enrichment; when to escalate to historian review |
| `reference/entities-schema.md` | Full CSV format for entities.csv and variants.csv; source values; entities.txt scope file |
