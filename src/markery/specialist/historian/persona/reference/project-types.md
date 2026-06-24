# Project Types

Markery projects follow one of two types. The HISTORIAN specialist owns the definition and session workflow for each type. When starting a new project, choose a type based on the research goal; the type determines the workflow, file structure, and which specialists are involved.

---

## Match-Review-Essay

**Purpose:** Systematic cross-reference research producing confirmed patent-trademark pairs and published scholarly content.

**Workflow:** The full Markery pipeline — entity registry, candidate generation, human review, essay writing, site publication.

**Session workflow:** `research-session.md` in this directory. That file is the runnable checklist for a session on a match-review-essay project.

**Specialists involved:** All five — PATENT and TRADEMARK build the corpora, MATCHMAKER generates candidates, HISTORIAN reviews and writes, PUBLISHER renders and publishes.

**Project structure:**
```
projects/<name>/
├── entities.csv            Entity definitions for this project
├── variants.csv            Name variant definitions
├── seed_patents.json       Manually-identified seed patent records
├── entities.txt            Entity IDs in scope (one per line)
├── RESEARCH-AGENDA.md      Candidate subjects, methodology, key references
├── RESEARCH.md             Scholarly framework
├── matches/
│   ├── candidates.jsonl    Generated — never edited
│   ├── confirmed.jsonl     Hand-curated — authoritative
│   └── rejected.jsonl      Explicitly rejected pairs
└── content/                Research essays and narrative pages
```

**Durable artifacts:** `entities.csv`, `variants.csv`, `seed_patents.json`, `entities.txt`, `matches/confirmed.jsonl`, `content/`. Everything else is generated and gitignored.

**Example project:** `information-systems`

---

## Gallery/Exploration

**Purpose:** Visual survey of trademark marks in a particular date window, category, or theme. Surfaces leads that may feed into a match-review-essay project or stand alone as visual records.

**Workflow:** Query `trademarks.duckdb` for marks matching a condition, render images into an HTML gallery, optionally enhance selected marks. No pair confirmation, no essay writing.

**Session workflow:** Documented in the project's own `README.md`. No generic session workflow exists because gallery projects vary significantly in scope and query.

**Specialists involved:** TRADEMARK (image data), PUBLISHER (gallery rendering, image enhancement).

**Project structure:**
```
projects/<name>/
├── README.md               Project overview and workflow
├── STATUS.md               Project metrics and next action
└── output/                 Gallery HTML and enhanced images (gitignored)
```

**Durable artifacts:** `README.md`, `STATUS.md`. Output is gitignored and regenerable.

---

## Annual Review

**Purpose:** An *annual* design-mark review (`type: annual-review`). Per year in
`project.json`'s `review_years`, the publisher builds a year landing page linking twelve
monthly design-mark galleries into `site/<project>/<year>/`, surfaced as a card on the
Markery root portal. Built by `markery site build-all`, driven by the project's config.

**Specialists involved:** TRADEMARK (design-mark data/images), PUBLISHER (review rendering).

**Example project:** `annual-design-review` (`review_years: [1929, 1930]`).

---

## Choosing a Type

| Question | Match-review-essay | Gallery/exploration |
|---|---|---|
| Goal | Confirmed historical correspondences + published site | Visual survey, image collection, lead generation |
| Output | `confirmed.jsonl` + research essays + HTML site | Gallery HTML files |
| Human role | Review candidates, confirm pairs, approve essays | Choose which marks to enhance; select leads |
| Duration | Multi-session research project | Can complete in one session |
| Prerequisite | Both patent and trademark databases cover the scope | Trademark database only |
