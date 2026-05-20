# Instruction Card: Match Status

## Command

```bash
markery match status <project>
```

Prints the current pipeline state and review progress for a project.

---

## Output fields

```
Project: information-systems
  Generated:   2026-05-18T14:22:09  (1,847 candidates, P50=0.2302, P90=0.4812)
  Enriched:    2026-05-18T15:03:44  (312 signals)
  Rescored:    2026-05-18T15:04:01
  Confirmed:   18 pair(s)
  Rejected:    42 pair(s)
  Unreviewed:  1787 candidate(s)
```

### Pipeline timestamps

| Field | What it means |
|---|---|
| `Generated:` | When `markery match <project>` last ran. Score reflects structural components only (unless `--full` was used). |
| `Enriched:` | When `markery patent signals <project>` last ran. Signal fields added to candidates. `(N signals)` = count of signal records written. |
| `Rescored:` | When `markery match rescore <project>` last ran. Scores updated to include semantic bonus. |

If any timestamp shows `never`:
- `Generated: never` — no candidates exist; run `markery match <project>` first
- `Enriched: never` — scores are structural only; signals not yet run
- `Rescored: never` after enrichment — semantic bonus not yet in scores; run `markery match rescore <project>`

### Score percentiles

`P50` and `P90` are computed at generation time (structural scores only). They give a quick read on the score distribution:

- Low P90 (< 0.50) — most pairs are in the weak zone; check entity variant coverage
- P50 near 0.30 — expected for a well-populated project with mixed CPC coverage
- P50 > 0.40 — entity variants are well-matched and the patent/trademark date ranges align closely

### Review counts

| Field | Source |
|---|---|
| `Confirmed:` | Count of rows in `projects/<project>/matches/confirmed.jsonl` |
| `Rejected:` | Count of rows in `projects/<project>/matches/rejected.jsonl` |
| `Unreviewed:` | `candidate_count - confirmed - rejected` (lower bound; some confirmed pairs may not be in the current candidate set) |

---

## Matchmaker registry status

For entity registry row counts (not per-project pipeline state):

```bash
markery matchmaker status
```

Output:
```
entities.duckdb:
  company_entity         12
  entity_name_variant    47
```

---

## Human-readable request forms

```
"What is the current pipeline state for the information-systems project?"

"How many candidates have been reviewed?"

"Has signal enrichment been run? Do scores need to be updated?"
```
