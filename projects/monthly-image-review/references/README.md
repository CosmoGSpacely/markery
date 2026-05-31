# References — monthly-image-review

Secondary literature relevant to this gallery project lives in the shared library
at `library/works/`. Each file here is a one-line pointer:

```
see: library/works/<slug>
```

To load a work's passages in a historian session, read
`library/works/<slug>/excerpts.md` directly.

## Works in scope for this project

| File | Library slug |
|---|---|
| `leffingwell-scientific-office-management.md` | `library/works/leffingwell-scientific-office-management` |

## Cross-project retrieval need

The historian reviewing 1920s industrial trademarks — particularly marks filed by
manufacturers like Chicago Pneumatic and Wilson Jones — should also load:

- `library/works/galloway-office-management/excerpts.md` (in information-systems
  scope) — specifically the "Card Index Filing and its neglect" passage (pp. 153–154),
  which describes how manufacturers of this era organized trademark filing
  correspondence. This passage provides the administrative context for why
  companies like CP filed and managed their marks as they did.

This is the cross-project retrieval need that justified building the shared
`library/` (Phase 15 P3): the same work serving both projects now lives in one
place rather than as duplicate files.

## Adding a work to this project

1. Acquire or enter the work: `markery librarian acquire <identifier>` or
   `markery librarian enter <slug> --title ... --author ... --year ...`
2. Create `references/<slug>.md` containing only `see: library/works/<slug>`
3. The historian reads `library/works/<slug>/excerpts.md` in sessions

## Format reference

See `library/README.md` for the full metadata.json schema, excerpts.md format,
and sourcing guidelines.
