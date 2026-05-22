# Markery

[![CI](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml/badge.svg)](https://github.com/CosmoGSpacely/markery/actions/workflows/ci.yml)

Markery is a command-line research tool for historical patent and trademark scholarship. It finds correspondences between US patents and USPTO trademark registrations — the moment when an invention became a product — and builds a documented, human-reviewed record of those pairings. The output is a static research site with sourced essays, figures, and timelines.

The current research project documents the pre-computer information systems industry: filing appliances, card-index equipment, visible record systems, tabulating machines, and the phonetic coding schemes American businesses used to organize knowledge before the digital era. These technologies were patented and trademarked at scale and are almost entirely absent from the standard history of information technology.

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

Markery is structured as five specialist agents, each owning one data domain:

| Specialist | Owns | Role |
|---|---|---|
| PATENT | `data/patents.duckdb` | Fetches patent records from EPO OPS by CPC class and year range |
| TRADEMARK | `data/trademarks.duckdb` | Loads USPTO bulk data; enriches marks via the TSDR API |
| MATCHMAKER | `data/entities.duckdb` | Manages the entity registry; scores patent-trademark candidate pairs |
| HISTORIAN | `confirmed.jsonl` per project | Guides human review; scaffolds and validates research essays |
| PUBLISHER | `site/` per project | Renders confirmed pairs and essays into a static research site |

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
markery patent verify-credentials

# Trademark corpus
markery trademark build --csv-dir csv/ --date-start 1900-01-01 --date-end 1939-12-31
markery trademark fetch <serial_no>
markery trademark enrich-project <project> --source confirmed
markery trademark verify-credentials

# Entity registry
markery matchmaker build --data-dir projects/<project>
markery matchmaker list

# Match pipeline
markery match <project>                    # generate candidates
markery match <project> --full             # generate + signals + rescore
markery review <project>                   # interactive review (Y / N / Q)

# Historian tools
markery historian prepare <project>        # generate session brief
markery historian card <project> <slug>    # compact candidate card (~250 tokens)
markery historian scaffold <project> <slug>  # generate essay skeleton
markery historian validate <project> <slug>  # validate essay against DB

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
| `trademarks.duckdb` | 25,473 case files, 1900–1939 (USPTO bulk) · 96 mark images · 18 enriched records |
| `patents.duckdb` | ~40,000 US patents across B42F, B42D, B41J, B41L, G06C, G06K, G09F (1900–1939) |
| `entities.duckdb` | 5 entities, 32 name variants (information-systems project) |

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
