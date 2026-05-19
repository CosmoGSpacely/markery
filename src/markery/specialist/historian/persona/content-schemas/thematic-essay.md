# Content Schema: Thematic Essay

## Purpose

A cross-entity narrative essay that synthesizes multiple confirmed pairs, entities, or patent-trademark clusters into a single historical argument. Where match essays treat one pair in isolation, thematic essays explain what the full pattern means: how a technology spread, how an industry organized itself, how a generation of companies translated invention into product.

Thematic essays are the intellectual core of the published site. They are what makes the project interesting to a general reader who has no interest in patent law or trademark registration. They should be written for the widest audience the project serves.

## Output file

`projects/<project>/content/theme-<slug>.md`

The slug describes the theme: `card-index`, `phonetic-coding`, `visible-record`, `office-systems-industry`.

## Layered audience

Thematic essays are written in two registers simultaneously:

**Narrative lead (accessible):** The opening section and transitions are written for any informed reader. No assumed knowledge. Define terms on first use. Explain what a card index is before analyzing it. Write as if the reader has read a newspaper but not an academic journal.

**Technical depth (specialist):** Later sections can go deep — citing specific serial numbers, CPC classes, grant dates — for the researcher or specialist reader who wants to follow the evidence. These sections should be clearly marked (with subheadings) so a general reader can skip them and a specialist can find them.

The two registers coexist in one document; the schema below specifies which sections use which register.

## Required sections

### 1. Opening argument (150–250 words) — *accessible*

State the theme and its historical significance in plain language. What pattern are you documenting? Why does it matter beyond the USPTO record? Do not open with a specific patent or trademark — open with the historical situation that made the patents and trademarks happen.

> Card indexing was not invented by any one company. But in the 1910s and 1920s, a handful of American manufacturers turned a European library tool into the backbone of the modern office — and they branded what they built.

### 2. The historical context (200–350 words) — *accessible*

What was happening in American commerce or technology that created the conditions for this theme? Draw on secondary literature where available (`references/` directory). Place the patent-trademark record within the larger historical story.

### 3. The evidence: confirmed pairs and the pattern (300–500 words) — *technical depth*

Present the confirmed pairs that support the theme. Use tables for multiple records. Cite serial numbers and publication numbers. Show the pattern that emerges across pairs: date clustering, entity succession, common goods descriptions, shared CPC classes. This is where the primary-source argument lives.

### 4. What the pattern shows (150–250 words) — *accessible*

Interpret the evidence for the general reader. What does the filing record reveal about how these companies operated, how this technology spread, or how this period worked? Reach from the specific pairs to the broader historical claim.

### 5. Significance and limits (100–150 words) — *accessible*

What does this theme contribute to the project's argument? What are the limits of the evidence — what would additional research need to establish?

## Output format

Plain Markdown. `##` headings for sections 1–4, `###` for subsections. Prose paragraphs. Tables for multi-record comparisons. No YAML frontmatter. No bullet lists in the narrative sections (tables for evidence, paragraphs for argument).

## Length target

800–1,500 words. A thematic essay should be substantive enough to support a full reading session but not so long that it requires a table of contents.

## Exemplars

None yet. The first thematic essay for the information-systems project should be on phonetic coding / card indexing — covering SOUNDEX, SOUNDEX QUICK AS A FLASH, and the Library Bureau citation chain. OBJECTIVES.md identifies this as the canonical demonstration of the project's method.
