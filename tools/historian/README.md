# Commerce and Technology Historian

A Claude specialist for researching American commercial and industrial history through the combined USPTO trademark and patent record, 1870–1950. The specialist's primary task is identifying and documenting **confirmed patent-trademark pairs** — cases where a specific patent and a specific trademark, held by the same company, can be shown to describe the same product.

## What It Can Answer

**Trademark questions** — What did a company call its products and when? What goods did they describe? When did a product category first appear in the filing record? What does a mark's design, classification, or first-use date reveal about the company's commercial strategy?

**Patent questions** — What did a company patent in a given period and CPC class? Who were the named inventors? What is the date relationship between a patent grant and a trademark filing?

**Patent-trademark correspondence** — Does a specific patent describe the technical invention underlying a trademarked product? What does the combined record reveal about the commercial lifecycle of a technology — from bench invention to market entry to brand identity?

**Corporate history** — How did ownership transfers, name changes, and mergers show up in the filing record? What companies dominated a product category?

## Databases

The specialist reads three DuckDB files via `ATTACH` cross-database queries:

| Database | Contents | Key tables |
|---|---|---|
| `trademarks.duckdb` | 25,473 USPTO trademark filings, 1900–1939 | `case_file`, `owner`, `statement`, `mark_images`, `mark_case_status` |
| `patents.duckdb` | 11,284 US patents in filing-system CPC classes (B42F, B42D), 1900–1939 | `patents`, `patent_classes`, `patent_inventors` |
| `entities.duckdb` | Canonical company registry mapping name variants across both databases | `company_entity`, `entity_name_variant` |

Cross-database queries use DuckDB's `ATTACH`:
```python
conn = duckdb.connect("data/entities.duckdb", read_only=True)
conn.execute("ATTACH 'data/patents.duckdb'    AS pat (READ_ONLY)")
conn.execute("ATTACH 'data/trademarks.duckdb' AS tm  (READ_ONLY)")
```

## Confirmed Pairs

The specialist contributes to a structured output: `projects/<project>/matches/confirmed.jsonl`. Each entry links a specific patent to a specific trademark for the same entity, with a prose note on the correspondence. Confirmed pairs are then developed into research essays in `projects/<project>/content/`.

Confirmed pairs are curated by hand — the scoring pipeline in `match/score.py` generates candidates, but a pair is confirmed only after historical review. The specialist helps evaluate candidates and draft the prose record.

## Setup

Drop this folder into a Claude project. Add the three database files (`trademarks.duckdb`, `patents.duckdb`, `entities.duckdb` from the markery repository) to the project. The specialist can then run live queries against the full combined dataset. Without the databases, the specialist works from historical knowledge and any records pasted into the conversation.

## How to Use

```
"What patents did Wilson Jones hold in B42F between 1925 and 1930,
 and which of their trademarks filed in that window are likely product-name marks?"

"Walk me through the candidate pairs for VI-DEX (serial 71235764) —
 which patent is the strongest match and why?"

"What does the combined trademark and patent record for Remington Rand
 in 1939 tell us about the state of visible-record filing technology at
 the end of the pre-computer era?"
```

## What to Expect

Responses lead with historical context, ground claims in specific filing records (serial numbers, patent numbers, filing dates, goods descriptions), show SQL when drawing on the database, and distinguish what the record shows from what it implies. The specialist does not give legal advice.

## What's in This Folder

| File | Purpose |
|---|---|
| `identity.md` | Who the specialist is, areas of expertise, explicit limits |
| `rules.md` | Response format, what it always does, what it never does |
| `examples.md` | Worked examples using real records from the database |
| `reference/markery-database.md` | Database schema, common query patterns, gotchas |
| `reference/mark-drawing-codes.md` | How to read drawing codes; historical interpretation |
| `reference/status-codes.md` | What status codes mean; historical significance |
| `reference/historical-context.md` | Periodization and commercial context, 1870–1950 |

## Source

All three databases are built and documented in the [markery repository](https://github.com/CosmoGSpacely/markery). See `README.md` for full schema, `docs/reference/TSDR.md` for the trademark API reference, `docs/reference/EPO.md` for the patent API reference, and `docs/reference/DESIGN.md` for the architecture rationale.
