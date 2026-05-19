# Instruction Card: Patent Signals

## When to use

When a confirmed patent lacks abstract text and that text would strengthen the correspondence analysis — for example, when `abstract_name_hit` or `goods_abstract_overlap` would change the scoring or the essay argument.

Check BRIEF.md `signals_available` first. If the patent is already listed there, the abstract is in the database and no fetch is needed.

## What this produces

Running `markery patent signals <project>` enriches `candidates.jsonl` with four signal fields for each candidate:

| Field | Meaning |
|---|---|
| `title_name_hit` | Mark words appear in the patent title |
| `abstract_name_hit` | Mark words appear in the patent abstract |
| `goods_title_overlap` | Jaccard overlap between G&S text and patent title tokens |
| `goods_abstract_overlap` | Jaccard overlap between G&S text and patent abstract tokens |

After running signals, the abstract text itself can be queried from `patents.duckdb` via `patents.abstract`.

## Where the output lands

Signal fields are added to `candidates.jsonl`. Abstract text is already in `patents.duckdb.patents.abstract` (fetched during the original build). Running signals does not fetch new data — it computes overlap scores from already-present text.

If an abstract is missing entirely (NULL in the database), signals will not fix it. In that case the patent needs individual re-fetch via EPO OPS — a separate operation not covered by this card.

## Request to researcher

**Human-readable:**
> "I need the signal fields computed for the information-systems candidates. Please run: `markery patent signals information-systems`"

**Structured (for agentic use):**
```json
{
  "action": "patent_signals",
  "target": {"project": "information-systems"},
  "project": "information-systems",
  "reason": "<state why the signals are needed>"
}
```

## Expected output

The command prints a count of candidates enriched. After it runs, re-read `candidates.jsonl` or query `patents.duckdb` directly for abstract text. BRIEF.md should be regenerated (`markery historian prepare <project>`) to reflect updated `signals_available`.
