# Tests — Hermeticity + CI Coverage (Plan)

Two linked problems: (1) the suite is coupled to **real project/corpus data** (so it can't
be archived and CI validates data, not code), and (2) **coverage is mediocre (53%)** and
partly *inflated* by those real-data integration tests. Fix both: make tests hermetic
(code + fixtures they create), and replace the lost real-data coverage with real hermetic
coverage of the under-tested layers.

Status: planning. No code yet. Archived to `archive/` on completion.

---

## 1. Principle

- **Unit/contract tests are hermetic** — they depend only on the code under test plus
  fixtures they build (`tmp_path`, tiny synthetic DBs, mocked HTTP). They never read
  `projects/<name>/` or assume specific corpus rows.
- **Data validation is separate and optional** — "is the *real* content sound?" is data QA
  (`markery historian validate`, a `dataqa` mark that skips when data/projects are absent),
  not a gating unit test.
- Why: hermetic tests let us archive `projects/` and rebuild freely; CI then proves the
  *machinery* works for any data, not that one committed project happens to be well-formed.

---

## 2. Current state

- **800 tests, 53% coverage** (`--cov-fail-under=50` in `ci.yml`).
- **Real-data coupling:** `tests/test_mvo.py` shells `markery historian …` against the
  committed `projects/information-systems` (`PROJECT`, `SLUG_CONF`, `SLUG_CAND` hardcoded);
  `tests/test_contract.py` reads the committed `data/*.duckdb` + `library/`. The DBs and
  projects are committed, so CI runs these as integration against real data — which both
  *couples* the suite and *flatters* the coverage number. Removing `projects/` breaks 54
  tests (all `test_mvo`), proven by simulation.
- **Coverage hotspots (missed statements):**

  | Module | Cov | Missed |
  |---|---|---|
  | `publisher/build.py` (orchestrator) | 10% | 299 |
  | `matchmaker/cli.py` | 41% | 407 |
  | `librarian/cli.py` | 25% | 336 |
  | `publisher/wikipedia/cli.py` | 35% | 235 |
  | `trademark/cli.py` | 15% | 229 |
  | `patent/cli.py` | 17% | 154 |
  | `markery/cli.py` (top dispatch) | 20% | 152 |
  | `librarian/sources/wikipedia.py` | 0% | 128 |
  | `historian/review.py` | 46% | 113 |
  | `image_enhancement/cli.py` | 0% | 105 |
  | `historian/status.py` | 20% | 94 |
  | `patent/build.py` | 34% | 82 |
  | `matchmaker/link.py` | 42% | 78 |
  | `publisher/queries.py` | 46% | 79 |
  | `image_enhancement/{pipeline,gallery,upscale,binarize}` | 0–24% | ~166 |

  The gap is concentrated in **the build orchestrator, the CLI command layers, the librarian
  source adapters, and image enhancement** — i.e. the glue/integration code, exactly what
  the real-data tests were lazily covering.

---

## 3. Part A — Split the MVO test (hermetic contract + optional data-QA)

`test_mvo.py` exists for a good reason — it pins the **historian output contract** that
markery-langgraph parses (section headers, `## Primary Sources`, filing-date format, the
`## CARD:` header). Keep that guarantee; remove the live-data dependency.

1. **Hermetic MVO contract test.** Build a minimal synthetic project in `tmp_path` (a small
   `entities`/`case_file`/`patents` fixture DB + a `confirmed.jsonl` + a stub essay), point
   `config.ROOT`/`DB` at it (the pattern `test_orchestrator.py` / `test_candidates_propose.py`
   already use), run `markery historian card/scaffold/digest`, and assert the output
   structure. Always runs; no `projects/` needed.
2. **Optional data-QA path.** Move "is the real content valid" to a `@pytest.mark.dataqa`
   suite that `skipif` `projects/` or `data/` is absent (and isn't run in the hermetic CI
   lane) — backed by `markery historian validate`. This is where real-corpus assertions live.
3. **Audit the other coupled tests** (`test_contract.py`, any `requires_dbs`/`requires_library`
   users): either give them synthetic fixtures or move them under `dataqa`.

Outcome: `projects/` (and, if we choose, committed DBs) become archivable without breaking
CI; the contract is still enforced hermetically.

---

## 4. Part B — Raise CI coverage (honestly)

Replacing real-data integration with hermetic tests will *drop* coverage first, so Part B
must add real coverage of the hotspots. Highest-leverage, in order:

1. **`build.py` orchestrator (299 missed, the single biggest win).** A hermetic end-to-end
   test: synthesize a tiny project (2 entities, a few marks/patents, 1 confirmed pair) in
   temp DBs, run `build_site` **and** `build_all` into `tmp_path`, then assert: expected
   pages exist, the portal lists the project, an annual-review project renders, and
   `check_site` reports 0 broken/orphans. One test exercises build + render + queries +
   portal + reviews together — and it's the integration the real-data tests were standing in
   for.
2. **CLI layers (`*/cli.py`, ~1,400 missed combined).** (a) Dispatch tests: invoke each
   `markery <area> <subcmd> --help`/routing path and assert it maps to the right `cmd_*`
   (mock the handler) — cheap, covers the argparse glue. (b) A handful of `cmd_*` happy-paths
   with fixtures/mocks for the high-value commands.
3. **Librarian source adapters (`ia`/`gutenberg`/`wikipedia`, ~216 missed).** Mocked-HTTP
   tests following the `sources/commons.py` precedent (which is already well-tested).
4. **Image enhancement (`binarize`/`gallery`/`pipeline`/`upscale`, ~166 missed).** Test the
   pure transforms (binarize threshold, gallery query against a temp DB, upscale's Lanczos
   fallback) the way `print_asset` is tested.
5. **`queries.py` / `historian/status.py` / `matchmaker/link.py`** against small temp DBs.

**Ratchet the floor.** Raise `--cov-fail-under` in steps as hermetic coverage lands
(50 → 60 → 70), so the gain can't regress. Target ~70% with the suite fully hermetic.

---

## 5. Phased plan

- **P1 — Hermetic MVO.** Rewrite `test_mvo` against a synthetic fixture; add the `dataqa`
  mark + skip for real-corpus checks. Confirm the suite passes with `projects/` absent.
- **P2 — Orchestrator coverage.** The `build_site`/`build_all`/`check_site` end-to-end
  hermetic test (biggest single coverage jump).
- **P3 — CLI + adapters.** Dispatch tests + key `cmd_*` paths; mocked-HTTP source adapters.
- **P4 — Enhancement + queries.** Pure-transform + temp-DB tests.
- **P5 — Ratchet.** Raise `--cov-fail-under` to the new sustained floor; document the
  hermetic-vs-dataqa split in `CLAUDE.md`/test README.

Gate per P: suite green; coverage non-decreasing; after P1, `pytest` passes with `projects/`
moved aside (the archivability check).

---

## 6. Open questions

1. **Committed DBs:** keep `data/*.duckdb` committed (so optional data-QA can run in CI on
   dispatch) or drop them from the repo and rely on synthetic fixtures everywhere?
   **Resolved 2026-06-24:** the hermetic lane needs **neither** real DBs nor `projects/`
   (P1 done — it runs against `tests/fixtures/synthetic.py`). The large DBs become
   **gitignore + rebuild** artifacts; that move lands in **Phase 28 P3** (with the rebuild
   recipe). Until then they stay committed so the `dataqa` job has data.
2. **Two CI lanes?** **Resolved 2026-06-24:** yes — a hermetic `test` job (`-m "not dataqa"`,
   always, +coverage) and a `dataqa` job (`-m dataqa`). Both wired in `ci.yml`.
3. **Coverage target:** is ~70% the right sustained floor, or higher for the core
   (`render/`, `build.py`, `queries.py`) and lower for thin CLI glue? (Still open — decide
   during P5 ratchet.)
4. **markery-langgraph:** bring its suite under the same hermetic discipline + a coverage
   floor (it shells the CLI; its tests already mock tool calls)? (Still open.)
