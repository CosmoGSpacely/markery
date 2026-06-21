# Site Review

Phase 24 P1 site-builder audit. Working document — UX/render issues collected here for triage; archived on phase completion per the REVIEW-file convention.

## Issues

### 1. Stat pills look like buttons but are not interactive
The summary stats in the gallery header (e.g. "11 marks", "0 with images", "1 confirmed pairs") are rendered as pill/badge shapes with borders that read as clickable buttons. They are static labels, so the affordance is misleading — users may try to click them expecting filtering or drill-down. Either restyle them so they don't look interactive, or make them actually do something (e.g. filter the gallery).

### 2. Trademark card image blocks are empty
The image area on trademark cards is rendering blank. Expected behavior: show the mark image when one exists, and fall back to the word mark (the mark text) when there is no image. Currently neither appears, so cards with no image are just empty boxes.

### 3. Patent cards should show an illustrative figure
Patent cards have no figure. They should display the illustrative drawing — historically Figure 1 — so each patent card has a visual anchor like the trademark cards do.

### 4. Vertical scrolling filing timeline alongside cards
Idea: replace/augment the current standalone horizontal timeline with a vertical timeline running down the left side of the gallery, given a little more prominence. It sits alongside the cards so that scrolling down moves forward through time — the cards and the timeline advance together. (Today the timeline is a horizontal SVG on its own `timeline.html` page, rendered by `_timeline_svg` in `components.py`; this would bring it onto the gallery layout as a left rail.)

### 5. Entity pills on cards should link to the entity page
On patent and trademark cards, the entity pill/badge is currently a static label. It should be a link to that entity's page, so users can jump from a card to the full entity view.

### 6. Entity pages need a short company-formation essay
Each entity page should include a short essay on the formation of the company — its founding story / origins — to give the entity page narrative context beyond the stats and linked records.

### 7. Redundant breadcrumbs on Entities and Matches pages
The breadcrumb (e.g. "Home › Entities") on the entities page and the matches page is redundant — the same links sit in the nav bar directly above it. Consider dropping the breadcrumb on these top-level pages.

### 8. Rename "Entities" to "Companies"; add "People" to nav
The "Entities" nav item should be renamed "Companies". Additionally, add a "People" item to the nav bar — we plan to gather historical information on some of the people behind the companies (e.g. Mack, Remington) and give them their own section.

## Additional recommendations (from code review)

### 9. New link color likely fails WCAG AA contrast on the cream background
The Ink Wash slate `#6D8196` used for inline links measures ~3.96:1 against the cream page background `#FFFFE3` — below the 4.5:1 WCAG AA minimum for body-size text. Recommend using a darker slate for *text* links (e.g. the hover tone `#56697d`, ~5.4:1, or darker). The lighter slate is fine where text is bold or sits on a dark fill (buttons, badges, the `.match-link`). Worth a pass over all `#6D8196`-on-light usages.

### 10. No active/current indicator in the nav bar
The header nav (`_nav_links` in `components.py`) gives no signal of which section the user is currently viewing. Add an "active" state so Trademarks/Patents/Companies/etc. highlight the current page.

### 11. Cards aren't clickable as a unit
On the gallery cards (`_make_card` in `galleries.py`), only the "Confirmed pair →" link is actionable (and the entity pill once #5 lands). The large card surface, image, and title aren't clickable. Consider making the whole card — or at least the image and name — link to a detail view, which is the affordance users expect from a card grid.

### 12. Truncated "goods" text has no way to see the full value
Goods descriptions are cut at 120 chars with an ellipsis (`galleries.py:48`) and there's no tooltip or expand. At minimum add a `title` attribute carrying the full text; better, an expand-on-click or a detail view.

### 13. Zero/empty states read as errors or blank space
Stats like "0 with images" and galleries with no records render as bare zeros and empty grids. Add friendly empty-state copy (e.g. "No confirmed pairs yet") so an empty section looks intentional rather than broken.

### 14. Image placeholder shows the serial number, not the mark
Related to #2: when a trademark has no image, the placeholder renders the raw serial number (`galleries.py:40`), which is meaningless to a reader. The word-mark fallback requested in #2 should replace it; the patent gallery likely has the analogous issue with patent numbers.

### 15. Label the classification/drawing codes on cards
The code values on cards are shown without a clear label of what they are:
- **Patent cards** — the classification should be labeled, e.g. "Class G01B".
- **Trademark cards** — the drawing code should be labeled "Drawing Code 5T07" (currently rendered as "Draw 5T07" in the card footer, `galleries.py:62`).

### 16. Link notable people (inventors/registrants) to their People essay
When an important person — e.g. a founder — appears as an inventor on a patent, the patent card should link that person's name to their People essay (see #6/#8 for the People section). In this period it's rare for an individual to register a trademark, but if it does occur, the trademark card should likewise link the individual registrant to their People essay.

## Implemented changes

- **Ink Wash color scheme** — remapped the site palette in `src/markery/specialist/publisher/render/css.py` from the warm brown/cream scheme to Ink Wash: charcoal `#4A4A4A` (headers, text), light gray `#CBCBCB` (borders), cream `#FFFFE3` (page background), slate blue `#6D8196` (links, buttons, badges). Two derived tints added for contrast: `#56697d` (slate hover) and `#ECECDF` (panel fill).
- **Footer affiliation** — updated the footer in `src/markery/specialist/publisher/render/components.py` to read: "History of commerce and technology is built by Markery. Copyright [current year] Guild Products." Year is dynamic (`date.today().year`); "Markery" links to the repo, "Guild Products" links to guildproducts.com.
