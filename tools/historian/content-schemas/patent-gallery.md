# Content Schema: Patent Gallery

## Purpose

A browsable gallery of all patents for a project's entities, with a timeline and historian-written narrative interpreting the patent strategy.

## Data Provided by Backend

The site builder supplies:
- All patent records for the project (via `patents.for_project`)
- Patent figures embedded in cards where available (from `patent_figures` table)
- A generated SVG timeline: grant dates plotted on a 1900–1939 axis, colored by entity and annotated with CPC class
- CPC class distribution summary (count per class)
- For each patent: link to the relevant match page if a confirmed pair exists

## What the Historian Writes

**Output file:** `projects/<project>/content/patents-narrative.md`

### Required sections (in order)

#### 1. Patent portfolio overview (150–250 words)

What does this entity's patent record reveal about its technical priorities and competitive positioning? Cover:
- Volume and temporal distribution — when did the company file most heavily?
- CPC class distribution — what technical domains did it focus on?
- Named inventors — are there identifiable lead inventors, or broad distributed R&D?
- The relationship between the patent record and any known corporate events (mergers, product launches)

Every claim grounded in specific patent numbers, dates, and assignee names from the record.

#### 2. Technically significant patents (one paragraph per patent, 50–100 words each)

Identify 3–5 patents that are technically or historically notable — strongest candidates for patent-trademark correspondence, patents held by key inventors, or patents marking a technology inflection. For each:
- What the invention is, in plain language
- Its date relative to relevant trademark filings
- Why it is significant to the patent-trademark correspondence question

Link by patent number. The site builder converts patent numbers to card anchors.

#### 3. Gaps and coverage limits (50–100 words)

What is not in the record? Patents filed outside the covered CPC classes, patents in predecessor companies' names not yet captured in the entity registry, international filings. Note any periods where the patent record seems thin relative to known company activity.

## Output Format

Plain Markdown. No YAML front matter. `##` headings. Code blocks for any SQL cited. Rendered above the patent gallery grid.

## Example opening

> Wilson Jones's patent record in B42F and B42D between 1920 and 1935 concentrates almost entirely in filing-system hardware: loose-leaf binder mechanisms, tab systems, and guide card assemblies. Seventeen patents in this window, nearly all assigned to Wilson Jones Company of Chicago. The concentration in B42F — filing systems — rather than B42D — office folders and envelopes — reflects a company that understood its market position precisely. Wilson Jones was not trying to be an office supply generalist; it was a filing-systems specialist, and the patent record reflects that discipline.

## Site builder integration

The site builder generates `projects/<project>/site/patents.html` by combining:
1. This narrative (above the gallery)
2. A generated SVG timeline of grant dates
3. A CPC class distribution bar
4. A card grid of all patents (figure if available, patent number, title, grant date, inventors, CPC classes, entity badge)
5. Links to match pages for confirmed pairs
