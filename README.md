# Markery

[![CI](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml/badge.svg)](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml)

Markery is a command-line research tool for historical patent and trademark scholarship. It finds correspondences between US patents and USPTO trademark registrations — the moment when an invention became a product — and builds a documented, human-reviewed record of those pairings. The output is a static research site with sourced essays, figures, and timelines.

Active research projects include the pre-computer information systems industry (filing appliances, card-index equipment, tabulating machines), early American radio manufacturers (1920–1940), and animal imagery in technology company trademarks (pre-1931).

---

## Quickstart

```bash
git clone https://github.com/CosmoGSpacely/markery.git
cd markery
python -m venv .venv && source .venv/bin/activate
pip install -e "."
markery --version        # confirm install
markery status           # inspect committed databases
markery project init my-project   # scaffold a new research project
```

The three databases (`patents.duckdb`, `trademarks.duckdb`, `entities.duckdb`) are committed to the repository. No rebuild is required to start working with the existing `information-systems` project.

Full setup, credential configuration, and rebuild instructions: [**SETUP.md**](SETUP.md)

---

## How it works

Markery is structured as six specialist agents, each owning one data domain:

| Specialist | Owns | Role |
|---|---|---|
| PATENT | `data/patents.duckdb` | Fetches patent records from EPO OPS by CPC class and year range |
| TRADEMARK | `data/trademarks.duckdb` | Loads USPTO bulk data; enriches marks via the TSDR API |
| MATCHMAKER | `data/entities.duckdb` | Manages the entity registry; scores patent-trademark candidate pairs |
| HISTORIAN | `confirmed.jsonl` per project | Guides human review; scaffolds and validates research essays |
| PUBLISHER | `site/` per project | Renders confirmed pairs and essays into a static research site |
| LIBRARIAN | `library/` at repo root | Acquires secondary literature; indexes passages for historian context |

**Candidate generation** — The MATCHMAKER scores every patent-trademark pair for each entity in a project: how closely the trademark filing follows the patent grant date (max 0.5), whether the CPC class falls in the product signal set (0.3 binary). Maximum score: 0.80. The ceiling is intentional — a 1.0 would claim a certainty no automated process can deliver.

**Human confirmation** — A high score identifies a pair worth examining; it does not confirm a historical correspondence. Confirmation is a human act. The HISTORIAN presents each candidate and records the human's decision. `confirmed.jsonl` is curated by hand. `candidates.jsonl` is generated automatically and never edited.

**Publishing** — Once pairs are confirmed, the HISTORIAN scaffolds research essays from a defined scholar persona; the PUBLISHER renders them as a static site with mark images, patent figures, timelines, and cross-linked entity pages.

Cross-specialist calls route through `orchestrator.py`. No specialist imports directly from another.

---

## CLI reference

```bash
# Start a project
markery project init <project>
markery status

# Patent corpus
markery patent build --classes B42F B42D --year-start 1900 --year-end 1939
markery patent build --resume              # resume after quota interruption
markery patent pull <patent_no>            # fetch a single patent on demand
markery patent coverage-check --classes B42F --year-start 1900 --year-end 1939
markery patent verify-credentials

# Trademark corpus
markery trademark build --csv-dir csv/ --date-start 1900-01-01 --date-end 1939-12-31
markery trademark fetch <serial_no>
markery trademark enrich-project <project> --source confirmed
markery trademark verify-credentials

# Entity registry
markery matchmaker build --data-dir projects/<project>
markery matchmaker list
markery matchmaker suggest-variants "<entity name>"   # rank name variants from DB
markery matchmaker validate-variants --data-dir projects/<project>

# Match pipeline
markery match <project>                    # generate candidates (focus_serials-scoped if set)
markery match <project> --all-serials      # generate from all entity trademarks
markery match <project> --full             # generate + signals + rescore
markery match auto-disposition <project> --reject-below 0.25  # batch-reject low scorers
markery match preflight <project>          # pre-session signal and image audit
markery match rescore <project>
markery review <project>                   # interactive review (Y / N / Q)

# Historian tools
markery historian prepare <project>        # generate session brief
markery historian digest <project>         # compact project state summary (~800–1200 tokens)
markery historian card <project> <slug>    # compact candidate card (~250 tokens)
markery historian scaffold <project> <slug>  # generate essay skeleton
markery historian validate <project> <slug>  # validate essay against DB

# Secondary literature (LIBRARIAN)
markery librarian discover --wikipedia "<Article Name>" --add-wants
markery librarian search-sources "<query>" --source ia
markery librarian acquire <ia-identifier>
markery librarian extract <slug> --topics "topic1" "topic2"
markery librarian index --embed
markery librarian card "<query>" --mode semantic
markery librarian search "<query>"

# Publish
markery site build <project>
markery enhance enhance <serial_no> --out-dir projects/<project>/output/<slug>
markery wikipedia draft <project> <slug>

# Diagnostics
markery status
markery <subcommand> --help
```

---

## Current corpus

| Database | Contents |
|---|---|
| `trademarks.duckdb` | 25,473 case files, 1900–1939 (USPTO bulk) · 96+ mark images · enriched records via TSDR |
| `patents.duckdb` | ~40,000+ US patents across B42F, B42D, B41J, B41L, G06C, G06K, G09F, H04B, H01J, H03F, B60C, A01B, F02B and others |
| `entities.duckdb` | 30 entities across three projects (information-systems, radio-pioneers, animal-marks-1930) |
| `library/` | Shared secondary literature corpus (Internet Archive / Gutenberg) — full text, indexed passages, embedding index |

---

## Links

| | |
|---|---|
| [SETUP.md](SETUP.md) | Installation, credentials, database rebuild |
| [CONTEXT.md](CONTEXT.md) | Project constitution — specialists, project model, workflow |
| [DESIGN.md](DESIGN.md) | Engineering rationale — DuckDB, scoring, scope neutrality |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [ROADMAP.md](ROADMAP.md) | Active development phases |
| [DEFERRED.md](DEFERRED.md) | Known deferred work with reopen triggers |
