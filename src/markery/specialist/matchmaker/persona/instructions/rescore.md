# Instruction Card: Rescore

## When to rescore

Rescore after signal enrichment has added text-match fields to `candidates.jsonl` and you want those signals reflected in the numeric score without regenerating from scratch.

**Do rescore when:**
- `markery patent signals <project>` has run since the last score was computed
- `markery trademark enrich-project <project>` has run and goods descriptions are now present
- The current score is structural-only and you want the full score

**Do not rescore when:**
- No signal enrichment has been run — there is nothing new to incorporate; scores will not change
- You want to add new candidate pairs — rescore only rewrites scores for existing pairs; use `markery match <project>` or `markery match <project> --full` instead

---

## Command

```bash
markery match rescore <project>
```

Reads `candidates.jsonl`, recomputes each pair's score using the structural components (date score + class score) plus any semantic bonus from signal fields, and writes the file in-place. Also updates `rescored_at` in `pipeline_state.json`.

---

## Regeneration vs rescore decision

| Situation | Action |
|---|---|
| Need new candidate pairs (added entities, extended DB scope) | `markery match <project>` — full regeneration |
| Candidates enriched, need scores updated | `markery match rescore <project>` |
| Starting fresh from scratch | `markery match <project> --full` |
| Force regeneration even though candidates are enriched | `markery match <project> --force` |

**Caution:** Regenerating (`markery match <project>`) clears all signal fields. If enrichment has been run, regeneration discards it. The CLI will warn and block unless `--force` is passed.

---

## What rescore does to the score

The structural score (date + classification) is fixed at generation time. Rescore adds a semantic bonus (capped at 0.25) based on signal fields added by `markery patent signals`:

| Signal field | Max bonus |
|---|---|
| `title_name_hit` — mark name in patent title | +0.20 |
| `abstract_name_hit` — mark name in abstract | +0.10 |
| `goods_title_overlap` — G&S/title Jaccard > 0.05 | +0.10 |
| `goods_abstract_overlap` — G&S/abstract Jaccard > 0.05 | +0.05 |

Semantic bonus is capped at 0.25, so the effective maximum total score is 0.80. Pairs without signal fields rescore identically to their structural score.

---

## Checking rescore state

```bash
markery match status <project>
```

Look for `Rescored:` in the output. If it shows `never` after enrichment has been run, rescore is needed. If `Rescored:` is newer than `Enriched:`, scores reflect current signals.

---

## Human-readable request forms

```
"Signals have been enriched. Update the scores."

"markery patent signals just finished for the information-systems project.
 Now update the candidate scores."

"Do I need to rescore or regenerate? I added a new name variant."
```
