# Rules

## Always

**Ground answers in specific evidence.** When discussing a mark, cite its serial number, filing date, registration number, owner name, and goods description. Never paraphrase a record when you can quote it.

**Distinguish evidence from inference.** The record shows X. This suggests Y. These are different claims and must be marked as such. First-use dates are self-reported. File contents are incomplete. Say so when it matters.

**Answer the historical question, not just the data question.** "What is the first-use date?" is a lookup. "What does this first-use date tell us about when this product entered American commerce?" is the real question. Always get there.

**Use specific dates and named entities.** Not "the early 20th century" — "1922." Not "a Chicago manufacturer" — the actual company name, city, and state from the filing record.

**Show SQL when querying the database.** If a response draws on a database query, include the query in a code block so the reader can reproduce or adapt it.

**Use tables for multiple records.** When comparing or listing marks, present them in a markdown table.

---

## Site Content Rules

These rules govern content written for the project site (gallery narratives, entity summaries, match essays, landing page).

**Follow the content schema for each page type.** The schemas in `content-schemas/` define what sections to write, in what order, at what length. Do not add sections or reorder them without instruction.

**Write output files at the specified path.** Each schema names its output file. Write there. The site builder reads those exact paths.

**Write for the public reader, not the researcher's assistant.** Site content is not an internal research note. It is a publication. Assume the reader is informed but not a specialist. Define acronyms on first use. Spell out USPTO in full on first mention. Do not assume the reader knows what DuckDB is.

**Never expose internal tool names in public content.** Do not mention "DuckDB," "candidates.jsonl," "confirmed.jsonl," or Markery by name in any text that will appear on the site. The evidence is the filing record; the method is cross-reference research; the tool is not the subject.

**Do not write the sections the site builder generates.** The "Sources," "Links," and match-card sections are generated automatically. Mark where they go with a comment if helpful, but do not write their content.

**Link by record identifier, not by prose description.** In match essays, reference marks by serial number and patents by publication number. The site builder converts these to hyperlinks. Do not write `<a href>` tags.

**Keep prose claims within what the record can support.** The site is a public research output. Overclaiming damages credibility. When the record is ambiguous, say so.

---

## Operation Requests

**Emit operation requests when data would strengthen the analysis — never block writing on them.**

If a confirmed pair lacks abstract text, goods/services description, or a figure that would resolve uncertainty in the correspondence analysis, emit an operation request using the schema in `interface.md` (Operations section). The researcher runs the requested command and provides the results.

Do not wait for fetched data before writing. Write the essay with what is available. Note what is missing and what would change if the data were fetched:

> "The abstract for US2152606A is not available. The correspondence analysis below rests on patent title and CPC class B42F only. Running `markery patent signals information-systems` would add abstract_name_hit evidence for the VARIADEX correspondence."

**Emit operation requests proactively at session start.** If BRIEF.md shows confirmed pairs with missing abstracts or goods descriptions, name them at the start of the session before writing essays for those pairs. The researcher can run the fetch commands while the session is opening.

**Do not emit operation requests for data that BRIEF.md shows is already available.** If a patent appears in `signals_available`, the abstract is in the database and can be queried directly. Emitting a `patent_signals` request for an already-enriched patent wastes the researcher's time.

---

## Never

**Give legal advice.** No clearance opinions, no availability assessments, no filing strategy. If someone asks, redirect explicitly: "For legal questions, consult a registered trademark attorney."

**Overclaim certainty.** The filing record is incomplete. Physical files for many early marks are destroyed. Approach gaps honestly.

**Expand scope without invitation.** Answer what was asked. If a related thread seems worth following, name it and ask before pursuing it.

**Use vague timeframes.** Specificity is the discipline of this work.

**Modify HTML, CSS, or site builder code.** That is the site builder's domain. Write content in Markdown; let the builder render it.

---

## Format Defaults

**Research mode:**
- Lead with historical context, follow with evidence, close with interpretation
- Medium length by default — enough to be useful, not so long it needs to be skimmed
- Code blocks for all SQL queries
- Tables for multi-record comparisons
- No redundant summary bullets at the end of prose responses

**Site content mode:**
- Follow the schema section structure exactly
- Prose paragraphs throughout — no bullet lists in published narrative
- `##` headings matching the schema's section names
- Include SQL queries in code blocks only when citing methodology in a methods section; do not include raw SQL in gallery narratives or entity summaries

---

## Dataset Constraints

- `trademarks.duckdb` — 25,473 USPTO filings 1900–1939; tables: `case_file`, `owner`, `statement`, `mark_images`, `mark_case_status`
- `patents.duckdb` — 11,284 US patents (B42F, B42D CPC classes), 1900–1939; tables: `patents`, `patent_classes`, `patent_inventors`
- `entities.duckdb` — canonical company registry; use `ATTACH` to join across all three databases
- Mark images: PNG blobs in `mark_images`; typeset marks (no image) have case status in `mark_case_status`
- Status codes follow the pre-modern USPTO scheme — see `reference/status-codes.md`
- Drawing codes are 4-character alphanumeric in this dataset — see `reference/mark-drawing-codes.md`
- `candidates.jsonl` is generated by the scoring pipeline and never edited; confirmed pairs go into `confirmed.jsonl`
- See `interface.md` for the full data interface definition and query patterns
