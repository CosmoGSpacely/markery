# References — information-systems

Secondary literature relevant to this project lives in the shared library at
`library/works/`. Each file here is a one-line pointer:

```
see: library/works/<slug>
```

To load a work's passages in a historian session, read
`library/works/<slug>/excerpts.md` directly.

## Works in scope for this project

| File | Library slug |
|---|---|
| `galloway-office-management.md` | `library/works/galloway-office-management` |
| `leffingwell-scientific-office-management.md` | `library/works/leffingwell-scientific-office-management` |
| `yates-control-through-communication.md` | `library/works/yates-control-through-communication` |
| `cortada-before-the-computer.md` | `library/works/cortada-before-the-computer` |
| `austrian-herman-hollerith.md` | `library/works/austrian-herman-hollerith` |

## Adding a work to this project

1. Acquire or enter the work: `markery librarian acquire <identifier>` or
   `markery librarian enter <slug> --title ... --author ... --year ...`
2. Create `references/<slug>.md` containing only `see: library/works/<slug>`
3. The historian reads `library/works/<slug>/excerpts.md` in sessions

## Format reference

See `library/README.md` for the full metadata.json schema, excerpts.md format,
and sourcing guidelines.
