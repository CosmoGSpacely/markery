# Content Schema: Trademark Gallery

## Purpose

A browsable gallery of all trademark filings for a project's entities, with a timeline showing filing activity across the research period and a historian-written narrative interpreting the portfolio.

## Data Provided by Backend

The site builder supplies:
- All trademark records for the project (via `trademarks.for_project`)
- Mark images embedded in cards (from `mark_images`, or TSDR if not yet fetched)
- A generated SVG timeline: filing dates plotted on a 1900–1939 axis, colored by entity
- For each mark: link to the relevant match page if a confirmed pair exists

The historian does not query the database for this page. The data arrives pre-assembled.

## What the Historian Writes

**Output file:** `projects/<project>/content/trademarks-narrative.md`

### Required sections (in order)

#### 1. Portfolio overview (150–250 words)

What does this entity's trademark portfolio reveal about its commercial strategy? Cover:
- How many marks, over what period
- The balance of word marks vs. design marks — what does this signal?
- Whether filings cluster (rapid expansion) or are distributed (steady growth)
- What product categories the goods descriptions reveal

Ground every claim in the filing record. Quote specific serial numbers, dates, and goods descriptions.

#### 2. Key marks (one paragraph per mark of significance, 50–100 words each)

Identify 3–5 marks that deserve individual attention — strongest candidates for patent-trademark correspondence, marks with unusual design choices, or marks that reveal inflection points in company strategy. For each:
- What the mark is and what it covered
- Why it is significant to the research
- Any known or suspected patent correspondence

Link by serial number. The site builder converts serial numbers to card anchors automatically.

#### 3. Gaps and uncertainties (50–100 words)

What is missing? Destroyed files, marks without images, periods of inactivity that may reflect unregistered use. Be specific about what the record cannot show.

## Output Format

Plain Markdown. No YAML front matter. Headings use `##` within the file (the site builder wraps it in the page's section structure). Code blocks for any SQL queries cited. The site builder renders this narrative above the gallery grid.

## Example opening

> Remington Rand's trademark record in B42F classes tells a story of acquisition-driven portfolio construction rather than organic brand development. Between 1917 and 1935, the company filed 23 marks — but the filing pattern breaks sharply at 1927, when the Remington-Rand merger consolidated three predecessor portfolios into a single corporate identity. Before 1927, marks appear under "Remington Typewriter Company" and "Rand Kardex Bureau, Inc." as separate filers; after 1927, they consolidate under the merged entity. This is visible in the owner field of the filing record as much as in any corporate history.

## Site builder integration

The site builder generates `projects/<project>/site/trademarks.html` by combining:
1. This narrative (rendered from Markdown, placed above the gallery)
2. A generated SVG timeline
3. A card grid of all marks (mark image, serial, filing date, goods, status, entity badge)
4. Links to match pages for confirmed pairs
