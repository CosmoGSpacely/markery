# Commerce and Technology Historian

A Claude specialist for researching American commercial and industrial history through USPTO trademark records and primary sources, 1870–1950.

## Setup

Drop this folder into a Claude project. If you have access to `trademarks.duckdb` (the markery database), upload it or reference it in the project — the specialist can then run live queries against 25,473 USPTO trademark filings from 1900–1939. Without the database, the specialist works from historical knowledge and any records you paste in.

## How to Use

Ask the specialist about a company, a product category, a period, or a mark:

- *"What do the trademark filings for [Company X] tell us about their business in the 1920s?"*
- *"When did [product type] start appearing in trademark filings, and what does that suggest about the market?"*
- *"What did it mean for a company in 1922 to file a stylized mark rather than a word mark?"*
- *"What can the 1919–1929 filing record tell us about the office supply trade?"*

## What to Expect

Responses lead with historical context, ground claims in specific filing records (serial numbers, filing dates, goods descriptions, owner names), show SQL queries when drawing on the database, and distinguish what the record shows from what it implies. The specialist does not give legal advice and will not claim more certainty than the evidence supports.

## What's in This Folder

| File | Purpose |
|---|---|
| `identity.md` | Who the specialist is, areas of expertise, explicit limits |
| `rules.md` | Response format, what it always does, what it never does |
| `examples.md` | Three worked examples using real records from the database |
| `reference/mark-drawing-codes.md` | How to read drawing codes; historical interpretation |
| `reference/status-codes.md` | What status codes mean; historical significance |
| `reference/historical-context.md` | Periodization and commercial context, 1870–1950 |
| `reference/markery-database.md` | Database schema, common query patterns, gotchas |

## Source Database

`trademarks.duckdb` is built from the 2011 USPTO Trademark Case Files Dataset, filtered to applications filed 1900–1939. It includes case records, owners, goods descriptions, classification codes, design search codes, and mark images fetched from the TSDR API. See the [markery repository](https://github.com/CosmoGSpacely/markery) for the build scripts, API client, and full documentation.
