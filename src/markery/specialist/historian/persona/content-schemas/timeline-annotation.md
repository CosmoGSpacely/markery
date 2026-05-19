# Content Schema: Timeline Annotation

## Purpose

An annotated chronological account of the full arc documented by the project — from the earliest relevant patents through the last confirmed trademark filings, and optionally into the post-1939 commercial continuity window (Phase 6D).

The timeline annotation is the historian's contribution to a visual timeline page. The site builder generates the SVG timeline from the filing dates; the historian writes the annotations that explain what the events mean.

## Output file

`projects/<project>/content/timeline.md`

## Structure

The timeline annotation is a sequence of dated entries, each consisting of a date range or specific date and a brief explanatory note. Entries should be organized chronologically.

### Preamble (100–150 words)

State the period covered, the entities and technologies involved, and what the timeline is designed to show. This appears above the visual timeline.

### Entries

Each entry follows this format:

```markdown
### [Year or date range]

**[Event description]**

[1–3 sentences of historical context: what this event means within the project's argument, 
how it connects to surrounding entries, what it reveals about the technology or the companies.]
```

Entries should cover:
- Major patent filings and grants for confirmed pairs
- Major trademark filings and registrations for confirmed pairs
- Corporate events affecting confirmed entities (mergers, name changes, acquisitions)
- Industry context events (where documented by secondary literature)
- The date-gap between patent grant and trademark filing (the core correspondence evidence)

**Granularity:** Year-level is appropriate for most entries. Month-level for entries where timing is the argument (e.g., "51 days after the patent grant").

### Closing note (50–100 words)

One paragraph noting what happens after the timeline ends: whether commercial use continued, whether any entities persisted, what the post-1939 record shows if Phase 6D extension has been run.

## Length target

Timeline entries: as many as the confirmed pairs and significant corporate events require. Typically 15–30 entries for a project with 8 confirmed pairs. Preamble and closing note combined: 200–250 words.

## Output format

Plain Markdown. `###` headings for each entry (the date or date range). `**Bold**` for the event description line. Prose for context. No tables. No bullet lists within entries — entries should read as a continuous narrative when viewed sequentially.

## Notes

The site builder reads `timeline.md` to populate the annotated timeline page. It expects the `###` heading format for entry detection. Do not use `##` headings within this file (only the preamble and closing note, which are unmarked prose, and the `###` entries).

If a figure is available for a confirmed patent that appears in the timeline, note it: "A patent drawing is available and shown in the gallery." The site builder can link the timeline entry to the figure.
