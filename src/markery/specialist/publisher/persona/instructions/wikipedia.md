# Instruction Card: Wikipedia Drafting

## When to use

When a confirmed patent-trademark pair or company entity warrants a Wikipedia article — typically a confirmed pair with strong primary-source documentation (USPTO filing record, patent specification, contemporaneous trade press) that can support a neutral, well-cited article.

Wikipedia drafting is optional and downstream of the historian's work. It requires a completed match essay as the source material.

---

## Workflow

**Step 1 — Generate the wikitext draft:**
```bash
markery wikipedia draft <project> <slug>
```

Reads the match essay from `confirmed.jsonl` and the content file at the essay's path, generates a wikitext draft in Wikipedia format, and writes it to `projects/<project>/wikipedia/<slug>.wiki`.

**Step 2 — Review and edit the draft:**
Open `projects/<project>/wikipedia/<slug>.wiki` and review for:
- Factual accuracy against the match essay and primary sources
- Neutral point of view (no advocacy for the research method or the pair's significance)
- Citation format (should use `<ref>` tags with USPTO source URLs)
- No original research — all claims must be attributable to secondary sources or the public filing record

Edit the `.wiki` file directly before submitting.

**Step 3 — Submit to Wikipedia:**
```bash
markery wikipedia submit <project> <slug>
```

Shows a unified diff between the current Wikipedia article (if it exists) and the draft, then prompts for confirmation before POSTing. To target a specific Wikipedia article title:

```bash
markery wikipedia submit <project> <slug> --title "VI-DEX" --summary "Add USPTO filing record citations"
```

Default edit summary: `"Add primary source citations from USPTO filing record"`.

---

## Wikipedia's content policies

The draft generator applies these constraints, but review is still required:

- **No original research.** Do not include interpretations or conclusions that appear only in the match essay and are not attributable to a secondary source.
- **Neutral point of view.** Do not frame the Markery research method as the source of discovery — frame findings as facts from public records.
- **Verifiability.** Every factual claim should be citable to the USPTO filing record, a patent specification, a contemporary trade publication, or another reliable secondary source.
- **Notability.** Wikipedia articles require the subject to be notable — covered in independent reliable sources. A USPTO filing alone is not sufficient for notability. The confirmed pair should have documented commercial significance (trade press, industry catalogs, historical references) to justify an article.

If the content cannot meet these standards, do not draft or submit. Record the limitation in the match essay's references section instead.

---

## Output location

Draft files are written to `projects/<project>/wikipedia/<slug>.wiki`. This directory is created automatically. Draft files are not gitignored — commit them alongside the match essay if the draft is intended for eventual submission.

---

## Human-readable request forms

```
"Draft a Wikipedia article for the VI-DEX confirmed pair."

"Generate the Wikipedia wikitext for information-systems / wilson-jones-visible-index."

"The wikipedia draft for vi-dex is ready. Submit it."
```
