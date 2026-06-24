# Wikipedia Edit Queue (Phase 24 P3)

> **Status: PAUSED (P3 closed 2026-06-22).** One edit live (John Deere). The current
> confirmed pairs are largely exhausted of clean "augment an existing article" targets
> (Sterilamp/Victor assessed non-viable below). Resume this cadence after more projects
> add fresh confirmed pairs.


A living working list for the **one-edit-per-day** Wikipedia contribution cadence.
Each edit follows the proven Soundex pattern (live 2026-06-06, unreverted): a small,
**primary-source-cited** addition to an **existing notable article**, period-correct
entity naming, diff reviewed before submit, recorded to the project's
`wikipedia/submissions.jsonl`. We **augment existing articles — we do not create
stubs**. An edit is only queued if a suitable target article exists and the
patent/trademark fact is honestly on-topic.

**Honesty rule (carried from the essays):** cite a patent on an article only when the
patent's subject genuinely matches the article topic. Owner-and-era pairs and
off-topic patents get a **trademark-only** citation (or are skipped) — never an
implied embodiment link.

## Workflow (free-model drafting, human-gated)

As of 2026-06-19 the mechanical steps are CLI + free-model driven; the human does the
judgment:

1. `markery wikipedia candidates <project>` — deterministic list of confirmed pairs
   (slug, normal-cased mark, patent, essay present?, already on Wikipedia?). No API.
2. `markery wikipedia propose-edit <project> <slug> --article "<Article>"` — the
   **project model (now the free model)** drafts the neutral, sourced citation
   sentence from the human-gated essay, in normal case (MOS:TM), with the TSDR
   `{{cite web}}` template, and **no patent-embodiment claim** unless the essay's
   Connection supports goods-correspondence. Writes `wikipedia/<slug>-propose.wiki`.
3. **Human gate:** verify the facts (esp. filing-vs-registration dates), pick a unique
   anchor sentence in the live article.
4. `markery wikipedia replace "<Article>" --project <project> --find … --replace … --summary …`
   — diff + confirm, POST, record to `submissions.jsonl`.

**Proof (2026-06-19):** `propose-edit` on the John Deere pair (free model, $0) produced
the correct normal-cased, trademark-only sentence with the right serial and TSDR cite —
but stated the mark was "registered … on 8 April 1911" (that is the *filing* date;
registration was 1912-09-10). The free model carries the drafting; the human gate
catches the fact slip. Same thesis as the essays: facts are machine-checkable, judgment
is human.

## Cadence

One edit per day. After each submit: confirm the diff is live, wait for it to settle
unreverted before the next day's edit on a related/high-profile article.

## Prior edits

| Date | Article | Project | What | Status |
|---|---|---|---|---|
| 2026-06-06 | Soundex | information-systems | SOUNDEX trademark citation (serial 71246709, 1927, Rand Kardex Bureau) | live |
| 2026-06-19 | [John Deere](https://en.wikipedia.org/w/index.php?diff=1360151379) | animal-marks-1930 | "John Deere Moline, Ill." trademark citation (serial 71055630, filed 1911, reg 1912) — rev 1360151379 | live |

**Lesson (2026-06-19):** Wikipedia's AbuseFilter #50 ("Shouting") rejects edits whose
added text is heavily uppercase. Render trademark names in **normal case** in prose and
edit summaries (per [MOS:TM](https://en.wikipedia.org/wiki/MOS:TM)), not the all-caps
form stored in the DB. The all-caps "JOHN DEERE MOLINE, ILL." was warned and not saved;
"John Deere Moline, Ill." went through.

## Queue (prioritized)

| # | Article (target) | Project / slug | Edit | Connection | Target verified | Status |
|---|---|---|---|---|---|---|
| ~~1~~ | ~~John Deere~~ | animal-marks-1930 / john-deere-moline-ill-us979019a | ✅ **DONE 2026-06-19** — rev 1360151379, live | — | — | **live** |
| ~~2~~ | Germicidal lamp | radio-pioneers / sterilamp-us2168861a | trademark-only: STERILAMP serial 71423019 (filed 1939-08-25, reg 1940-03-05) | **Premise was wrong (verified 2026-06-21):** the live *Germicidal lamp* article **and** the detailed *Ultraviolet germicidal irradiation* article contain **no** Westinghouse/Sterilamp mention — there is no existing sentence to augment, and a bare-trademark sentence injected into a heavily-sourced medical article is weak/promotional. Paired patent US2168861A is a *Stroboscopic Lamp* (off-topic) regardless. | ❌ no anchor in either article | **Blocked** — needs a secondary source for Sterilamp's historical role + a sourced History sentence in UVGI, else skip |
| ~~3~~ | Victor Talking Machine Company | radio-pioneers / victor-us1486221a | — | **Verified 2026-06-21:** paired patent US1486221A is *"Means for Controlling the Flow of Electrons in Electric Discharge Devices"* (1924 vacuum-tube patent) — off-topic for the phonograph-era Victor article, which already documents Victor's trademarks (His Master's Voice/Nipper) in depth. Owner/era only. | ❌ off-topic patent; trademark already covered | **Dropped** |
| — | Shannon file / Yawman & Erbe | information-systems / shannon-us1738120a | — | **No dedicated Wikipedia article** (only marketplace listings) — no target | ❌ no article | Dropped |
| — | Kardex | information-systems / kardex-us2178457a | — | Essay "Connection" is empty (never finalized) — finalize the essay before any edit | n/a | Blocked (essay incomplete) |
| — | Wratten | photographic-equipment / wratten-us940030a | trademark-only at most | Paired patent is a *plate-holder* (owner/era only, flagged in essay) — weak; revisit only as a trademark-only note | ⏳ | Low priority |
| — | L.S. Starrett | precision-tools / figurative-* | — | Marks are *figurative* (no word element); little to add to a company article | ⏳ | Low priority |

## Notes

- High-profile targets (John Deere) get extra care: tightly-scoped, single sourced
  sentence in the existing logo/trademark paragraph; no patent claim forced in.
- Re-survey the remaining confirmed pairs (animal-marks `double-eagle`, the
  `figurative` marks, information-systems `rediref`/`variadex`/`vi-dex`) for target
  articles as the queue is worked down.
