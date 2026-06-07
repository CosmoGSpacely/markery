# Instruction Card: Manual Work Registration (ILL / Physical Copy)

## When to use

When a work has arrived via interlibrary loan or is available as a physical copy, and `markery librarian acquire` is not applicable (no IA identifier, no Gutenberg ID). Use `enter` to register the bibliographic record in the library so the work appears in `list` output and can receive manually typed excerpts.

Do not use `enter` for works that are available open-access — use `acquire` instead.

## Command

```
markery librarian enter <slug> --title "<title>" --author "<Surname, Firstname>" --year <YYYY> [--isbn <ISBN>]
```

`<slug>` is a human-chosen identifier following the `make_slug` convention: lowercase, hyphen-separated, no articles at the start. Example: `jenkins-images-and-enterprise`.

## What this produces

- `library/works/<slug>/metadata.json` — bibliographic record with `source: manual`
- `library/works/<slug>/excerpts.md` — empty template with a comment prompting manual passage entry

No raw text is downloaded. Add passages directly to `excerpts.md` using the `### Section heading` + `> "Passage"` + page reference format that `index` expects.

## After entry

Run `markery librarian index` after adding passages to `excerpts.md` to make them searchable.
