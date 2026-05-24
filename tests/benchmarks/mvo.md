# Markery MVO Contracts

Minimum Viable Output definitions for historian CLI commands.
Each contract specifies what fields and structure must appear in command output
for the output to be considered machine-checkable without human review.

These contracts are enforced by `tests/test_mvo.py`. All checks are structural
and deterministic — no LLM inference is required.

**Fixture project:** `information-systems`  
**Fixture slug (card/validate/scaffold):** `soundex-us1261167a`  
**Fixture slug (card only, unreviewed):** `remington-us2168802a`

---

## historian card

**Command:** `markery historian card <project> <slug> --out -`

| Field | Validation rule |
|---|---|
| Header line | Matches `^## CARD: \S+  \[` |
| Status token | One of `candidate`, `confirmed` in the header bracket |
| Score | Float in (0.0, 1.0] in the header bracket |
| Gap | Matches `gap=[\d.]+y` in the header bracket |
| `mark:` | Present; contains a USPTO serial number matching `\b7[01]\d{6}\b` |
| `filed:` | Present; date matches `\d{4}-\d{2}-\d{2}` |
| `owner:` | Present; non-empty |
| `goods:` | Present |
| `entity:` | Present; contains `(id \d+)` |
| `patent:` | Present; matches `US\d+[A-Z]` |
| `title:` | Present |
| `grant:` | Present; date matches `\d{4}-\d{2}-\d{2}` |
| `assignee:` | Present |
| `cpc:` | Present (value may be empty) |
| `abstract:` | Present (value may be empty) |
| `signals:` | Present; contains `gt=` and `ga=` |
| `essay:` | Present; one of `present`, `absent` |
| Serial DB check | Serial number in `mark:` line resolves in `trademarks.duckdb` |
| Patent DB check | Patent number in `patent:` line resolves in `patents.duckdb` |

---

## historian digest

**Command:** `markery historian digest <project>`

| Field | Validation rule |
|---|---|
| Header line | Matches `^## DIGEST: \S+  \[` |
| Timestamp | ISO-like timestamp in header bracket |
| `queue:` line | Present; contains `confirmed=`, `rejected=`, `unreviewed≥`, `total_candidates=` |
| Queue counts | All four values are non-negative integers |
| `next_review` section | Present if unreviewed count > 0 |
| `enrichment:` line | Present; contains `signals=` |
| `preflight:` line | Present |

---

## historian validate

**Command:** `markery historian validate <project> <slug>`

| Field | Validation rule |
|---|---|
| Exit code | 0 for all-PASS essay; 1 for any failing check |
| Output lines | Contains exactly 6 `PASS` or `FAIL` check lines |
| Check names | All six of: `serial_resolves`, `patent_resolves`, `grant_date_matches`, `filing_date_in_body`, `entity_recognised`, `no_cross_contamination` |
| All-PASS line | On success: `All checks passed.` appears in output |

---

## historian scaffold

**Command:** `markery historian scaffold <project> <slug> [--force]`

| Field | Validation rule |
|---|---|
| Exit code | 0 on success |
| Stdout | Contains `Scaffold written →` |
| Output file | Exists at `projects/<project>/content/<slug>.md` |
| Frontmatter | File begins with `---` block |
| `title:` | Present in frontmatter; non-empty |
| `trademark_serial:` | Present; matches `\d+` |
| `trademark:` | Present; non-empty |
| `tm_filing_dt:` | Present; matches `\d{4}-\d{2}-\d{2}` |
| `patent_no:` | Present; matches `US\d+[A-Z]` |
| `patent_grant_dt:` | Present; matches `\d{4}-\d{2}-\d{2}` |
| `entity:` | Present; non-empty |
| Section headers | All six present: `## Primary Sources`, `## The Invention`, `## The Mark`, `## The Connection`, `## Historical Context`, `## Significance` |

---

## Notes

- All contracts are checked against real DuckDB data — the tests must be run
  with the data DBs present (not mocked).
- Scaffold tests run with `--force` and clean up the output file after the check
  to avoid overwriting human-written essays. The fixture slug `soundex-us1261167a`
  has a human-written essay; tests restore it from git after running.
- Haiku compatibility: all four contracts pass with `claude-haiku-4-5-20251001`
  since none of the checks depend on LLM output — they validate Markery's own
  deterministic CLI output.
