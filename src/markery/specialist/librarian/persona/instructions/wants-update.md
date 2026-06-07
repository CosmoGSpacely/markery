# Instruction Card: Update Wants-Queue Status

## When to use

When a work's status in the ILL/wants queue has changed — for example, a request has been placed (`in-progress`), the work has arrived (`acquired`), or the request was withdrawn. Use `wants-update` to keep `library/wants.jsonl` current so the `wants` command reflects actual queue state.

## Command

```
markery librarian wants-update <slug> --status <status> [--note "<note>"]
```

Valid statuses: `wanted`, `in-progress`, `acquired`.

`<slug>` is matched against the title slug or a partial title string in `wants.jsonl`. If the slug is ambiguous, the first match is used — check with `markery librarian wants` first to confirm the right entry.

## What this produces

Updates `library/wants.jsonl` in place. Prints a confirmation line: `Updated '<title>' → status=<status>`.

## Status lifecycle

```
wanted → in-progress → acquired
```

Works with status `acquired` are hidden from the default `markery librarian wants` output (they no longer need attention). To see them, use `markery librarian wants --status acquired`.
