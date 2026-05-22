# Public Readiness Review

**Opened:** 2026-05-22  
**Purpose:** Structured pre-release audit per Phase 13 P1. All findings resolved inline, promoted to DEFERRED, or explicitly accepted.

---

## Module Walk — Hardcoded Assumptions

### 1. `src/markery/cli.py` — docstring examples
**Finding:** Module docstring contains `information-systems` project name (5 occurrences), serial `71235764`, path `output/vi-dex`, and the removed `migrate-figures` command.  
**Impact:** No runtime effect; visible only to developers reading source. Misleading to a contributor unfamiliar with the project.  
**Resolution:** **Fixed inline** — replaced project-specific examples with generic `<project>` placeholders; removed `migrate-figures` line.

### 2. `src/markery/specialist/patent/cli.py` — argparse defaults
**Finding:** `markery patent fetch` and `markery patent signals` default to `project="information-systems"` when no project argument is supplied (`nargs="?"`).  
**Impact:** Running without an argument silently operates on `information-systems` instead of erroring. Any user without that project directory gets a misleading "project not found" error referencing a project they never created.  
**Resolution:** **Fixed inline** — changed both defaults to `None`; `require_project(None)` exits with "project name required".

### 3. `src/markery/specialist/trademark/cli.py` — argparse default
**Finding:** `markery trademark enrich-project` defaults to `project="information-systems"`.  
**Resolution:** **Fixed inline** — changed default to `None`.

### 4. `src/markery/specialist/historian/review.py` — argparse default
**Finding:** `markery review` defaults to `project="information-systems"`.  
**Resolution:** **Fixed inline** — changed default to `None`.

### 5. `src/markery/common/project.py` — error message example
**Finding:** `validate_patent_no` error message includes `US1261167A` as an example.  
**Impact:** Acceptable — this is a canonical example patent number, not a project-specific reference. It aids format understanding.  
**Resolution:** **Accepted as-is.**

---

## Document Walk — Root Files

### 6. `README.md` — stale install command
**Finding:** Setup section shows `pip install -r requirements.txt`. No `requirements.txt` exists; install is via `pip install -e "."`.  
**Resolution:** **Fixed inline** — corrected to `pip install -e "."`.

### 7. `README.md` — overhaul (P5)
**Finding:** README leads with architecture rather than purpose. No quickstart. Links section is functional but not inviting.  
**Resolution:** **Deferred to P5** (README overhaul is P5 scope).

### 8. `SETUP.md` — missing `markery --version` in first-run verification
**Finding:** Section 3 "Verify the committed databases" jumps straight to `markery status` without a simpler first check. A user whose install is misconfigured won't get a helpful error from `markery status`.  
**Resolution:** **Fixed inline** — added `markery --version` as step 1 of the verification sequence.

### 9. `SETUP.md` — wikipedia `verify-credentials` listed but not documented
**Finding:** Phase 13 P4 calls for a credential section per API. Wikipedia credentials are not yet documented in SETUP.md.  
**Resolution:** **Fixed inline as part of P4** — added Wikipedia section.

### 10. `CONTEXT.md` — `information-systems` example
**Finding:** CONTEXT.md uses `information-systems` as the example project name in the project layout section.  
**Impact:** Accurate — it is the live project. Acceptable for a public-facing document that acknowledges this is a real research tool.  
**Resolution:** **Accepted as-is.**

---

## CLI Help Accuracy

### 11. `markery --help` — missing `match` subcommands (status, rescore, preflight, auto-disposition)
**Finding:** `markery --help` lists `match` as "Generate patent-trademark candidate pairs" but `match` has 7 subcommands. Users reading only the top-level help won't know about `match status`, `match rescore`, etc.  
**Impact:** Discoverability gap, not a bug. Top-level help is intentionally brief.  
**Resolution:** **Accepted as-is.** `markery match --help` lists all subcommands.

### 12. `markery wikipedia --help` — 5 subcommands accurate
**Finding:** Verified correct.  
**Resolution:** No action needed.

---

## Blocking Gaps (must resolve before P6)

| # | Item | Blocking? | Resolution |
|---|------|-----------|------------|
| 1 | `cli.py` docstring — project-specific examples + migrate-figures | No (runtime) | Fixed inline |
| 2 | Patent CLI defaults `information-systems` | Yes — misleads first-time users | Fixed inline |
| 3 | Trademark CLI default `information-systems` | Yes | Fixed inline |
| 4 | Review CLI default `information-systems` | Yes | Fixed inline |
| 6 | README `requirements.txt` | Yes — install step fails | Fixed inline |
| 8 | SETUP.md missing `--version` check | Minor | Fixed inline |

---

## Deferred Items

None promoted to DEFERRED from this audit. All gaps were resolved inline or accepted.

---

## Audit Result

All blocking gaps resolved. Proceed to P2.
