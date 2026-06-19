# Wikipedia Edit Queue (Phase 24 P3)

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
| 2 | Germicidal lamp | radio-pioneers / sterilamp-us2168861a | **Trademark-only** citation: STERILAMP serial 71423019 (1939, Westinghouse) | Article already credits Westinghouse's Sterilamp. NOTE: paired patent US2168861A is a *Stroboscopic Lamp* (off-topic) — **do not cite the patent here** | ✅ article exists, names Sterilamp | Queued |
| 3 | Victor Talking Machine Company *(assess)* | radio-pioneers / victor-us1486221a | TBD after reading essay + article | Assess notability/honesty of the VICTOR pair before queueing | ⏳ to verify | Assess |
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
