# KARDEX: The Visible Index and the Filing System Empire

## The Mark

Remington Rand filed the KARDEX trademark on **December 14, 1939**, registration number **0377986**, covering *"card index filing cabinets and trays, index cards, guides, and supplies therefor."* The applicant was Remington Rand Inc. of New York, NY.

The filing came late in the company's 1930s filing burst. Between 1929 and 1939, Remington Rand registered REMRANDCO, LINEDEX, SCOTTIE, ARISTOCRAT, VARIADEX, RAND, and two REMINGTON marks before arriving at KARDEX. That the company waited until 1939 to register the name most closely associated with its visible-filing product line suggests KARDEX had long functioned as a trade name — recognized in the market without formal trademark protection — and that the 1939 filing was a consolidation of brand assets rather than the introduction of a new product.

---

## What Kardex Was

The Kardex system was a **visible record filing system**: index cards arranged in overlapping trays so that the bottom edge of each card remained exposed, allowing an operator to scan a large index at a glance without removing any card. The trays were mounted in cabinets — desktop units, floor-standing towers, or rotary carousels — that could hold hundreds or thousands of cards.

The visible record concept had several commercial applications. In its simplest form it was a name-and-address index. More elaborately, each card represented an inventory item, an account, a personnel file, or a production order; the visible edge carried summary data (stock level, balance due, status code) while the full card held the detail. A colored signal tab could be clipped to the card edge to flag exceptions — past-due accounts, low stock, deferred items — making the tray itself a dashboard for the state of a business operation.

This was, in the vocabulary of the period, not just a filing system but an **information system** — a designed arrangement for storing, retrieving, and acting on operational data at the speed of a clerk scanning a tray rather than pulling a drawer.

---

## The Patent Record: 166 Patents, 1917–1939

`patents.duckdb` contains **171 patents** assigned to Remington Typewriter Company or Remington Rand Inc. in CPC classes B42F and B42D between 1917 and 1939. The density of filing tells the corporate history as clearly as any narrative:

| Period | Assignee | Patents | Character |
|---|---|---|---|
| 1917–1926 | Remington Typewriter Company | ~10 | Foundational: accounting sheets, billing forms, index trays |
| 1927–1934 | Remington Rand Inc. | ~90 | Burst: card index trays, filing cabinets, visible index mechanisms |
| 1935–1939 | Remington Rand Inc. | ~70 | Refinement: prong binders, followers, signal tabs, protective strips |

The 1927 inflection is the merger. After Remington Typewriter joined with Rand Kardex to form Remington Rand, patent output in filing-system classes roughly tripled. The merged company was not just larger — it was filing systems as its core business, and it was patenting aggressively.

Selected patents from the cluster most directly corresponding to the KARDEX mark and visible-index product line:

| Patent | Title | Granted |
|---|---|---|
| US1640397A | Card-Index Tray | 1927-08-30 |
| US1647655A | Ledger Tray | 1927-10-18 |
| US1801804A | Visible Index | 1931-04-21 |
| US1802348A | Visible Index | 1931-04-28 |
| US1811633A | Visible File Case | 1931-06-23 |
| US1813257A | Credit System | 1931-07-07 |
| US1834204A | Overlapping Visible Index | 1931-12-01 |
| US1925343A | Index Card And Method Of Preparing Same | 1933-09-05 |
| US1963806A | Visible Index File Panel | 1934-06-19 |
| US2015460A | Index Device | 1935-09-24 |
| US2015480A | Card Index System For Keeping Records In A Visible Or Horizontal Way | 1935-09-24 |
| US2043675A | Record Member For Card Index Systems | 1936-06-09 |
| US2081841A | Visible Card File | 1937-05-25 |
| US2086047A | Card Index File | 1937-07-06 |
| US2178457A | Visible Index | 1939-10-31 |

The KARDEX trademark was filed two months after the last visible-index patent in the dataset (US2178457A, granted October 31, 1939; trademark filed December 14, 1939). The sequence — a decade of patents followed by a trademark consolidation — is characteristic of a mature product line rather than a launch.

---

## LINEDEX and VARIADEX: The Product Family

The KARDEX mark did not stand alone. The cross-reference of Remington Rand's trademark registrations against the patent record reveals a product family with distinct lines:

**LINEDEX** (Reg. 0289923, filed 1931) — registered by the subsidiary Remington Rand Business Service, Inc. The "line" in LINEDEX likely refers to the horizontal line of visible card edges in a Kardex-style tray: the product was a line-visible index rather than a tab-visible system.

**VARIADEX** (Reg. 0371824, filed April 7, 1939) — filed just weeks before the year's most active Remington Rand patent cluster. "Varia" suggests a variable or rotary index. US1849049A ("Rotary Index," 1932) and US2026503A ("Card Index Device," 1935) are candidate patents; the candidate score for VARIADEX–US2152606A ("Card Index," granted March 28, 1939; VARIADEX filed April 7) is 0.80 — the highest in the dataset.

**SCOTTIE** (Reg. 0323202, filed October 8, 1934) — the only Remington Rand trademark from this period without an obvious product category from the name alone. US1973497A ("Loose Leaf Binder," granted September 11, 1934; SCOTTIE filed October 8) scores 0.80. The product was likely a branded binder model.

---

## The Candidate Matches

From `candidates.jsonl`, the highest-scoring Remington Rand patent-trademark pairs involving specifically filing/visible-index products (excluding company-name marks REMINGTON and RAND):

| Score | Patent | Granted | Trademark | Filed |
|---|---|---|---|---|
| 0.80 | US2152606A Card Index | 1939-03-28 | VARIADEX | 1939-04-07 |
| 0.80 | US2149553A File | 1939-03-07 | VARIADEX | 1939-04-07 |
| 0.80 | US2149547A Card Index | 1939-03-07 | VARIADEX | 1939-04-07 |
| 0.80 | US1973497A Loose Leaf Binder | 1934-09-11 | SCOTTIE | 1934-10-08 |
| 0.80 | US1713945A Accounting And Filing System | 1929-05-21 | REMRANDCO | 1929-06-19 |
| 0.80 | US2178449A Card-Holding Clip | 1939-10-31 | KARDEX | 1939-12-14 |

The KARDEX–US2178449A ("Card-Holding Clip") pair captures the relationship precisely: a functional component of the visible-card system patented the same month the product-line name was trademarked.

---

## Source Note

Patent data from EPO OPS API via `patents.duckdb` (B42F and B42D classes, 1900–1939). Trademark data from USPTO Trademark Case Files Dataset and TSDR API via `trademarks.duckdb`. Candidate scores generated by `python -m match information-systems` using the date-proximity and CPC-class scoring model in `match/score.py`. Confirmed pairs recorded in `matches/confirmed.jsonl`.
