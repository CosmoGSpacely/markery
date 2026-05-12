# Markery Roadmap

Working plan for the markery project — where it stands, what's been built, and where it's going. Updated as of v0.1.1-alpha.

---

## What Markery Is

Markery is a research tool for studying American commercial history through USPTO trademark records. The primary dataset is 25,473 trademark applications filed 1900–1939, held in `trademarks.duckdb`. The project is organized around a specific hypothesis: that the combined trademark and patent record reveals things about the history of American technology and commerce that neither source shows alone.

The immediate research focus is **pre-computer information systems** — the filing cabinets, index cards, tabulating machines, visible record systems, and phonetic coding schemes that American businesses used to organize knowledge before the digital era. These systems were patented, trademarked, sold by major corporations, and used at massive scale. They are almost entirely absent from the standard history of information technology.

---

## Current State (v0.1.1-alpha)

### Infrastructure

**`trademarks.duckdb`** — the core database. 25,473 case records from the USPTO Trademark Case Files Dataset (2011 snapshot), filtered to 1900–1939. Tables: `case_file`, `owner`, `statement` (goods/services), `classification`, `design_search`, `intl_class`, `us_class`, `mark_images` (fetched via TSDR API). See `README.md` for full schema.

**`tsdr_client.py`** — USPTO TSDR API client. Fetches case status JSON and raw mark images (PNG) by serial number. Handles authentication, rate limits, and the quirky endpoint prefix inconsistencies in the TSDR API. See `TSDR.md`.

**`image_tools/`** — mark image enhancement pipeline. Takes raw TSDR PNG scans (~800px), upscales 4× using Real-ESRGAN (`x4plus-anime` model, optimized for pen-and-ink line art), optionally traces clean marks to SVG using vtracer. Produces print-ready PNG at ~3200px (~10" at 300 DPI). Routes on `mark_draw_cd` and design search codes to decide whether SVG vectorization is worth attempting. Exposes a CLI (`python -m image_tools {enhance,batch,gallery}`) and a Python API (`from image_tools import process_mark, build_gallery`).

**`commerce-and-technology-historian/`** — Claude specialist persona. System prompt, rules, worked examples, and reference docs for a historian of American commercial and industrial history, 1870–1950. Reads the trademark database directly and writes analysis grounded in specific filing records. Reference docs cover drawing codes, status codes, historical context, and image enhancement.

**`.claude/commands/enhance-marks.md`** — `/enhance-marks` skill. Guides the AI through fetching, enhancing, and gallery-building for a set of marks specified by date range, company, or SQL WHERE clause.

### Project structure

```
projects/
  information-systems/
    README.md
    soundex-marks/
      background.md        ← research essay
    input/                 ← gitignored
    output/                ← gitignored (generated images, PDFs, HTML)
      filing-systems/      40 design marks for filing and record organization
      stationery-marks/    55 design marks for writing paper and stationery goods
      soundex-marks/       SOUNDEX marks + Russell (1918) and Odell (1922) patent PDFs
  monthly-image-review/
    README.md
    input/                 ← gitignored
    output/                ← gitignored
      may1930-designs/     39 design marks filed May 1930, raw TSDR images
      enhanced-may1930-designs/   Real-ESRGAN enhanced (partial)
```

Research documents (`.md` essays, `README.md`) are tracked in git. Generated output (images, PDFs, gallery HTML) is gitignored — regenerable from the database and APIs.

---

## Near-Term: Patent Module

### Rationale

The trademark record establishes what a company called its product and when it entered commerce. The patent record establishes what was technically novel. For pre-computer information systems, the two records are complementary: companies like Rand Kardex Bureau (SOUNDEX, 1927) held both the trademark on the product name and the patents on the underlying algorithm — but nothing in either record points at the other. Reconnecting them by cross-referencing assignee names and date ranges is the core research operation this module will automate.

### Source

**PatentsView API** (`api.patentsview.org`) — free, structured, USPTO-backed, covers the full historical patent record. Supports queries by filing date, grant date, USPC classification, and assignee name. No authentication required.

### `patents.duckdb` schema

```sql
CREATE TABLE patents (
    patent_no       VARCHAR PRIMARY KEY,
    title           VARCHAR,
    filing_dt       DATE,
    grant_dt        DATE,
    abstract        VARCHAR,
    assignee_name   VARCHAR,
    assignee_city   VARCHAR,
    assignee_state  VARCHAR
);

CREATE TABLE patent_classes (
    patent_no       VARCHAR,
    uspc_class      VARCHAR,
    uspc_subclass   VARCHAR,
    ipc_class       VARCHAR
);

CREATE TABLE patent_inventors (
    patent_no       VARCHAR,
    inventor_name   VARCHAR,
    inventor_city   VARCHAR,
    inventor_state  VARCHAR
);
```

### USPC classifications to export (1900–1939 scope)

| Class | Description | Relevance |
|---|---|---|
| 235 | Registers | Tabulating, calculating, punched card machines |
| 40 | Card, picture, or sign exhibiting | Visible record systems, card indexes |
| 281 | Books, strips, and leaves | Loose-leaf binders, filing systems |
| 101 | Printing | Typewriters, duplicating, addressing machines |
| 283 | Printed matter | Forms, index cards, ledger sheets |

### `patent_tools/` module

```
patent_tools/
  __init__.py
  fetch.py        # PatentsView API queries → patents.duckdb
  pdf.py          # Google Patents PDF downloader (already proven for Soundex)
  drawings.py     # Extract figure images from patent PDFs (pdf2image or pypdf)
  link.py         # Cross-reference patent assignees against trademark owners
  cli.py          # python -m patent_tools {fetch,link,pdf}
```

`link.py` is the high-value piece. The matching logic:

1. Normalize company names (strip Inc./Corp./Co., uppercase, strip punctuation)
2. Join `patents.assignee_name` against `trademarks.owner.own_name` on normalized name
3. Filter to pairs where the patent grant date precedes or overlaps the trademark first-use date
4. Output a ranked candidate list for review

### Patent drawings in project output

For confirmed mark/patent pairs, patent figure images go alongside the mark image in the project output folder. The research essay references both. The gallery page for that mark links to the patent PDF and shows key figures inline.

---

## Medium-Term: Publication Pipeline

### Rationale

The current output is self-contained HTML gallery files — useful for browsing locally, not shareable or discoverable. The research has genuine public value: there is no existing resource that systematically cross-references pre-computer information system patents with trademark records and contextualizes them historically. A static public website changes this from a private research tool to a citable reference.

### Site architecture

Two-level Jinja2 site generator, replacing the current flat `gallery.py`:

```
site/
  index.html              ← filterable gallery across all projects/entries
  information-systems/
    index.html            ← project landing page
    soundex/
      index.html          ← entry detail page
      soundex-71246709.png
      soundex-71255821.png
      us1261167-fig1.png  ← extracted patent drawing
      us1261167.pdf
  monthly-image-review/
    index.html
    may-1930/
      index.html
      ...
```

Key differences from the current gallery approach:
- **Referenced images, not base64-embedded** — pages are fast and crawlable by search engines
- **Per-entry detail pages** — mark image(s), patent drawing(s), prose essay, primary source links (TSDR, Google Patents)
- **Open Graph metadata** — entries share cleanly on social/web
- **Index page** — filterable by project, date range, category, company

### Hosting

The `site/` directory output would deploy to GitHub Pages from the existing `markery` repository (`gh-pages` branch or `docs/` folder). A single `make publish` or equivalent would regenerate and push.

### Content generation

The historian specialist writes the prose essay for each entry, given:
- Structured mark metadata (serial number, filing date, goods description, owner, first-use date)
- Patent metadata (number, title, assignee, grant date, abstract)
- Both mark and patent images

The essay follows the pattern established by `projects/information-systems/soundex-marks/background.md`: historical context first, then primary-source evidence, then interpretation.

---

## Research Agenda: Information Systems Project

### Candidate subjects (marks already in the database)

The filing-systems gallery (40 marks) and stationery gallery (55 marks) are browsing outputs. The following are confirmed or high-probability mark/patent pairs worth developing into full entries:

| Mark | Serial | Filed | Company | Patent connection |
|---|---|---|---|---|
| SOUNDEX | 71246709 | 1927-03-31 | Rand Kardex Bureau | Russell 1918, Odell 1922 — phonetic indexing |
| SOUNDEX QUICK AS A FLASH | 71255821 | 1927-10-08 | Rand Kardex Bureau | Same patents |
| WHEELDEX | 71321669 | 1931-12-01 | Unknown | Rotary card file — patent TBD |
| SMEAD'S TELL VISION SYSTEM | 71403472 | 1938-02-26 | Smead Mfg. | Visible record system — patent TBD |
| FLEX-SITE | 71208081 | 1925-01-13 | Unknown | Filing system — patent TBD |
| JOHN DEERE (filing system) | 71055630 | 1911-04-08 | Deere & Co. | Farm record-keeping — patent TBD |

Beyond the database: Hollerith tabulating, Addressograph addressing systems, Kardex visible files, Powers tabulating (Sperry Rand predecessor), and Burroughs accounting machines are all high-priority subjects that likely have both trademark and patent records in this period.

### Discovery methodology

Once `patent_tools/link.py` is operational, systematic discovery replaces case-by-case research:

1. Export USPC 235 + 40 + 281 + 101 + 283 patents, 1900–1939, into `patents.duckdb`
2. Run the name-matching cross-reference against `trademarks.duckdb`
3. Review the candidate list ranked by signal strength
4. For each confirmed pair, fetch patent PDF and extract figures
5. Write background essay using the historian specialist
6. Build the entry page

### Key reference works

- JoAnne Yates, *Control Through Communication: The Rise of System in American Management* (1989) — filing systems and business communication 1880–1920
- JoAnne Yates, *Structuring the Information Age: Life Insurance and Technology in the Twentieth Century* (2005) — IBM and tabulating systems
- James W. Cortada, *Before the Computer: IBM, NCR, Burroughs, and Remington Rand and the Industry They Created, 1865–1956* (1993)
- Geoffrey Austrian, *Herman Hollerith: Forgotten Giant of Information Processing* (1982)
- Alfred D. Chandler Jr., *The Visible Hand: The Managerial Revolution in American Business* (1977) — the management systems that created demand for information products

No existing work systematically cross-references trademark records with patent records for this period and subject. That gap is the justification for this project.

---

## Monthly Image Review

A recurring research practice separate from the information systems project: browse all design marks filed in a given month, surface visually interesting or historically notable marks, and flag candidates for deeper research.

The May 1930 review produced several leads: LAND O'LAKES (71300354), BIRDS EYE (71301023), SHELL (71302052), and the Goodyear "FASHION FOLLOWS THE WINGED FOOT" mark (71300406). Each of these could become a full entry.

The enhancement pipeline makes the monthly review more useful: even a quick Real-ESRGAN pass on a promising mark resolves enough detail to make a research judgment about whether the image is worth pursuing.

---

## Output Format Standards

| Format | When used | Notes |
|---|---|---|
| PNG (4×, ~3200px) | All enhanced marks | Print-ready at 300 DPI for ~10" wide; universal |
| SVG | Clean word marks and geometric designs only | Scales perfectly; skipped when illustration content present |
| PDF | Patent documents | Downloaded from Google Patents storage |
| HTML (gallery) | Browsing output | Self-contained, base64-embedded; not for web publication |
| HTML (site) | Publication output | Referenced images, crawlable, Open Graph metadata |
| Markdown | Research essays, README | Tracked in git; human-readable source for site generation |

---

## Version History

| Tag | Notes |
|---|---|
| v0.1.1-alpha | `image_tools` pipeline, `/enhance-marks` skill, historian specialist, projects/ tree |
| v0.1.0 (implicit) | Initial TSDR client, `trademarks.duckdb` build, mark image retrieval |
