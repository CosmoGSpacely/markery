# References Format

Each file in this directory is a curated excerpt document for one secondary source. The historian reads these alongside the DuckDB data and uses them to ground essays in secondary literature.

## File naming

`<author-surname>-<short-title>.md`

Examples: `yates-control-through-communication.md`, `cortada-before-the-computer.md`

## File format

```markdown
---
author: Last, First
title: Full Title
year: 1989
publisher: MIT Press
isbn: 978-0-262-24029-1
ia_identifier: controlthroughcom00yate   # Internet Archive item ID (if available)
ia_access: borrow                         # open, borrow, or restricted
---

## Overview

One paragraph: what the book argues, why it is relevant to this project.

## Relevant passages

### [Topic heading]

> "Direct quotation from the text." (p. 42)

Context note: how this passage bears on the project's argument.

### [Another topic]

> "Another quotation." (p. 117)

Context note.
```

## Sourcing guidelines

- Prefer Internet Archive for open-access or borrowable works. The `ia_identifier` field is the IA item slug (from the URL `archive.org/details/<slug>`).
- For in-copyright works without IA access, paste relevant passages by hand from the physical or digital copy. Note the edition and page numbers precisely.
- Passages should be quoted verbatim with page numbers. Paraphrase is acceptable only when quotation is impractical; label paraphrases as such.
- Organize passages by topic, not by page order. The historian searches by topic.
