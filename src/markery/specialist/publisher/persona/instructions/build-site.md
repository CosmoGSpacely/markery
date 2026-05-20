# Instruction Card: Site Build

## When to use

When the project's content files are ready to render, or after any content change (new essay, revised entity summary, updated landing page). The build is fast — re-running after a small change produces an updated site in seconds.

## Prerequisites

1. Historian has written content files to `projects/<project>/content/`
2. `confirmed.jsonl` is populated with reviewed pairs
3. Mark images are enriched (for image display): `markery trademark enrich-project <project> --source confirmed`
4. Patent figures are available (for figure references): `markery patent fetch <project> --confirmed`

## Command

```bash
markery site build <project>
```

Output: `projects/<project>/site/` (gitignored, fully regenerable).

For a custom output path:
```bash
markery site build <project> --out /path/to/output
```

For deployment with absolute URLs in Open Graph tags:
```bash
markery site build <project> --base-url https://example.com/project-name
```

## What the build produces

The site builder renders one HTML page per content file, plus index pages and asset directories. All CSS, fonts, and images are written inline or as local files — the site is self-contained and does not require a server.

## After the build

Open `projects/<project>/site/index.html` in a browser to review. Return to the historian for any content revisions, then re-run the build.
