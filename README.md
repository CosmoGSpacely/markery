# Markery

Markery is a research platform for historical patent and trademark scholarship, built on an **agentic design pattern**. Five specialist agents — each owning a bounded data domain, a Python CLI, and a Claude persona — coordinate to acquire source data, generate candidate correspondences, support human review, and publish research findings.

The platform is designed for **responsive live retrieval**, not static database loading. Patent records are fetched from the EPO Open Patent Services API as projects define new scope. Trademark records are enriched from the USPTO TSDR API on demand. The shared databases grow with each research question; no data is pre-loaded for any specific project. A second project with different scope runs the appropriate build commands and gets exactly the data it needs.

The current research project — `information-systems` — documents the pre-computer information systems industry: filing appliances, card-index equipment, visible record systems, tabulating machines, and the phonetic coding schemes that American businesses used to organize knowledge before the digital era. These technologies were patented and trademarked at scale by major manufacturers and are almost entirely absent from the standard history of information technology.

---

## Architecture

Five specialist agents live under `src/markery/specialist/`. Each specialist owns one data domain and exposes three surfaces: a **Python CLI** for human operators, a **queries module** as a typed programmatic API for other agents, and a **Claude persona** (`persona/`) for use in Claude projects.

| Specialist | Owns | Role |
|---|---|---|
| PATENT | `data/patents.duckdb` | Fetches patent records from EPO OPS by CPC class and year range; manages resume state |
| TRADEMARK | `data/trademarks.duckdb` | Loads USPTO bulk trademark data; enriches individual marks via TSDR API |
| MATCHMAKER | `data/entities.duckdb` | Manages the canonical entity registry; generates and scores patent-trademark candidates |
| HISTORIAN | `confirmed.jsonl` per project | Human-facing review; drafts research essays from a defined scholar persona |
| PUBLISHER | `site/` per project | Renders confirmed pairs and historian essays into a static research site |

Cross-specialist calls route through `src/markery/specialist/orchestrator.py`. No specialist imports directly from another. The unified CLI entry point is `markery`.

---

## Why agentic, why live retrieval

A conventional approach would be: download all relevant data, load it into a database, query the database. Markery takes a different position on two dimensions.

**Scope neutrality.** The databases hold no project-specific defaults — no hardcoded date windows, CPC class sets, entity rosters, or seed records. A project defines its own scope through data files and CLI arguments; the tool provides the mechanism. Two projects can share the same databases and add to them independently without interfering with each other.

**Live retrieval.** The patent corpus grows by `markery patent build` command as projects expand their CPC class coverage. The trademark corpus gains per-mark enrichment — images, goods descriptions, first-use dates — as candidates are reviewed. Figures are fetched and stored when the historian needs them. This is not a snapshot; it is a growing, queryable record that responds to research questions.

The practical consequence: the `information-systems` project expanded from two CPC classes (filing appliances, forms) to seven classes covering typewriters, duplicating machines, calculators, punched-card systems, and display devices — each expansion was a single `markery patent build` command, not a code change.

---

## The confirmation model

The MATCHMAKER scores every patent-trademark pair for each project entity on two dimensions: how closely the trademark filing follows the patent grant date (max 0.5), and whether the patent's CPC class falls in the project's product signal set (0.3 binary). Maximum score: 0.80. The ceiling is intentional — a score of 1.0 would claim a certainty the model cannot deliver.

A high score identifies a candidate worth examining. It does not confirm a historical correspondence.

Confirmation is a human act. The HISTORIAN presents each candidate interactively — mark details, patent details, date gap, text-signal overlap — and records the human's Y/N decision. A confirmed pair carries a defensible historical argument, not just a score. `confirmed.jsonl` is curated by hand and is what research essays and the published site are built from. `candidates.jsonl` is generated automatically and never edited.

The error asymmetry drives this design: a false positive in `confirmed.jsonl` corrupts the scholarly record; a false negative is simply an unrecognized pair. Human review before confirmation is the appropriate epistemic standard for a tool making historical claims.

---

## Current corpus

| Database | Contents |
|---|---|
| `trademarks.duckdb` | 25,473 case files, 1900–1939 (USPTO bulk) · 96 mark images · 18 enriched records (TSDR) |
| `patents.duckdb` | ~30,500 US patents across B42F, B42D, B41J, B41L, G06C, G06K; G09F 1910–1939 in progress |
| `entities.duckdb` | 5 entities, 32 name variants (information-systems project) |

All three database files are committed to the repository. No rebuild is needed to start working.

---

## CLI

```bash
# Patent corpus
markery patent build --classes B42F B42D --year-start 1900 --year-end 1939
markery patent build --resume                    # continue after quota interruption
markery patent pull US1261167A                   # on-demand single patent
markery patent verify-credentials

# Trademark corpus
markery trademark build --csv-dir csv/ --date-start 1900-01-01 --date-end 1939-12-31
markery trademark fetch <serial_no>              # TSDR fetch into extended_marks
markery trademark enrich-project <project> --source confirmed

# Entity registry
markery matchmaker build --data-dir projects/<project>
markery matchmaker list

# Match pipeline
markery match <project>                          # generate candidates
markery match <project> --full                   # generate + signals + rescore
markery match rescore <project>                  # rescore after signal enrichment
markery review <project>                         # interactive review (Y / N / Q)

# Historian
markery historian prepare <project>              # generate BRIEF.md project state
markery patent signals <project>                 # enrich candidates with text signals
markery patent fetch <project> --confirmed       # fetch figures for confirmed pairs

# Publish
markery site build <project>
markery publisher build <project>                # alias for site build
markery enhance enhance <serial_no> --out-dir projects/<project>/output/<slug>
markery wikipedia draft <project> <slug>         # generate Wikipedia wikitext draft

# Diagnostics
markery status
```

Full options: `markery <subcommand> --help`

---

## Setup

Full guide: [`SETUP.md`](SETUP.md)

```bash
git clone <repository-url>
cd markery
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Add EPO_CONSUMER_KEY, EPO_CONSUMER_SECRET, USPTO_API_KEY to .env
markery status    # verify committed databases are intact
```

---

## Reference

| | |
|---|---|
| [`SETUP.md`](SETUP.md) | Setup guide — credentials, database verification, rebuild routes |
| [`CONTEXT.md`](CONTEXT.md) | What Markery is, specialist agents, project structure |
| [`DESIGN.md`](DESIGN.md) | Engineering rationale — DuckDB, agentic architecture, scoring, scope neutrality |
| [`ROADMAP.md`](ROADMAP.md) | Active development |
| [`DEFERRED.md`](DEFERRED.md) | Known deferred work with reopen triggers |
| [`src/markery/specialist/patent/EPO.md`](src/markery/specialist/patent/EPO.md) | EPO OPS API reference |
| [`src/markery/specialist/trademark/TSDR.md`](src/markery/specialist/trademark/TSDR.md) | USPTO TSDR API reference |
| [`src/markery/specialist/historian/persona/`](src/markery/specialist/historian/persona/) | HISTORIAN persona — scholar identity, content schemas, session workflow |
