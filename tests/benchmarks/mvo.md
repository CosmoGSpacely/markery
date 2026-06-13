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

## trademark inspect

**Command:** `markery trademark inspect <serial>`
**Fixture serial:** `71247861` (Mack bulldog — figurative, design code 030108, image present)

| Field | Validation rule |
|---|---|
| Exit code | 0 for an existing serial; non-zero for an unknown serial |
| Header line | First line matches `^## TRADEMARK <serial>` |
| Core fields | All present: `mark:`, `draw code:`, `filed:`, `registration:`, `status:`, `owner:`, `goods:`, `image:` |
| Figurative marks | When `mark_id_char` is null/blank, the `mark:` line reads `(figurative …)` |
| Image line | `image:` reads `available (…)` when a `mark_images` row exists, else `not available` |
| Design codes | Each six-digit code is printed with a human-readable description (authoritative category + section gloss or structural decomposition); `none` when the mark has no codes |

---

## site check

**Command:** `markery site check <project> [--strict]`
**Test file:** `tests/specialist/publisher/test_site_check.py` (synthetic site dirs, no DB)

| Field | Validation rule |
|---|---|
| Exit code | 0 when all internal links resolve; 1 on any broken link |
| Internal-link classification | Relative paths and `page.html#frag` are internal; `http(s)://`, `mailto:`, `data:`, and pure `#anchor` are not |
| Broken detection | A relative `href`/`src` whose target is absent on disk is reported as broken |
| Orphan detection | An emitted file no page links to (excluding `index.html`, `search.json`, `pagefind/`) is reported as an orphan |
| Strict mode | `--strict` raises exit code to 1 when orphans exist; default leaves orphans non-fatal |
| Missing build | Exit code 1 with a "run build first" message when the site directory is absent |

---

## patent search --assignee

**Command:** `markery patent search --assignee <substr> [--examples N]`
**Test file:** `tests/specialist/patent/test_search.py` (in-memory patents.duckdb)

| Field | Validation rule |
|---|---|
| Match set | Lists every distinct `assignee_name` matching the substring (case-insensitive), with hit counts, descending |
| Non-match exclusion | Assignees not matching the substring do not appear |
| Examples | With `--examples N`, prints up to N `patent_no  title (year)` rows per assignee |
| No-match case | Prints `No assignees matching '<substr>'` |

---

## match inspect

**Command:** `markery match inspect <project> [--entity ID] [--min-score F]`
**Test file:** `tests/specialist/matchmaker/test_groupb.py` (synthetic candidates.jsonl)

| Field | Validation rule |
|---|---|
| Grouping | Candidates grouped under `Entity <id>: <name>` headers, sorted by descending score within each group |
| Disposition | Each row marked `confirmed`, `rejected`, or `unreviewed` by cross-referencing confirmed/rejected.jsonl |
| Entity filter | `--entity ID` restricts output to that entity only |
| Figurative marks | A null trademark renders as `(figurative)` |
| Empty case | Prints a "no candidates" message when the filtered set is empty |

---

## librarian index

**Command:** `markery librarian index`

| Field | Validation rule |
|---|---|
| Exit code | 0 |
| Stdout | Contains `Indexed N work(s)` where N ≥ 0 |
| `library/index.jsonl` | Exists after run |
| Records | Each line is valid JSON with fields `work_slug`, `author`, `title`, `year`, `section`, `passage`, `page`, `context`, `indexed_at` |

---

## librarian search

**Command:** `markery librarian search <query> --mode keyword`

| Field | Validation rule |
|---|---|
| Exit code | 0 |
| Header row | Output contains `AUTHOR` and `SECTION` and `PASSAGE` |
| Result rows | Each result row contains a 4-digit year |
| No-match case | Exit code 0; output contains `No matches` |

---

## librarian list

**Command:** `markery librarian list`

| Field | Validation rule |
|---|---|
| Exit code | 0 |
| Header row | Output matches `SLUG.*AUTHOR.*YEAR` |
| Work rows | At least one row present when `library/works/` is non-empty |
| Excerpt counts | Non-negative integer in `EXC` column for each row |

---

## librarian card

**Command:** `markery librarian card <query> --mode keyword --out -`

| Field | Validation rule |
|---|---|
| Exit code | 0 |
| Header | First line matches `^# Library card:` |
| Citation brackets | At least one `[Surname (Year)]` bracket present |
| Token estimate | `len(output) // 4 ≤ 300` |

---

## publisher trademark gallery — focus_serials rendering

**Test file:** `tests/specialist/publisher/test_render_focus.py`  
**Fixture data:** synthetic trademark dicts (no DB required)

| Field | Validation rule |
|---|---|
| With `focus_serials` — section title | `trademarks.html` contains `Project Marks` |
| With `focus_serials` — entity section | `trademarks.html` contains `All Entity Trademarks` |
| With `focus_serials` — card class | `class="card card--focus"` present for each focus serial |
| With `focus_serials` — badge | `class="focus-badge"` present |
| With `focus_serials` — ordering | Focus serials appear before `All Entity Trademarks` heading; non-focus serials appear after |
| With `focus_serials` — stat chip | `project marks` chip present in page header |
| With `focus_serials` — no fallback | `>All Marks<` section title absent |
| Without `focus_serials` — section title | `trademarks.html` contains `All Marks` |
| Without `focus_serials` — no split | `Project Marks` section title absent |
| Without `focus_serials` — no focus class | `class="card card--focus"` absent from all card elements |
| Without `focus_serials` — no badge | `class="focus-badge"` absent |
| Without `focus_serials` — all serials | All trademark serial anchors present (`sn-*`) |

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
- LIBRARIAN contracts: checked against `library/index.jsonl` (committed to repo).
  The `search` and `card` contracts do not require embeddings (`index.duckdb` is
  gitignored); `--mode keyword` is used for MVO testing.
