# Scoring Formula Reference

Candidates are scored on two additive components. Maximum total score: **0.80**.

The ceiling is intentional — a score of 1.0 would imply a certainty the model cannot deliver. Scoring ranks candidates for review; it does not confirm them.

---

## Component 1: Temporal Score (max 0.50)

Measures how closely the trademark filing date follows the patent grant date.

| Condition | Score |
|---|---|
| TM filed 0–20 years after patent grant | 0.50 tapering to 0.0 over 20 years |
| TM filed more than 20 years after grant | 0.0 |
| TM filed before patent grant | Slight negative, max −0.40 |

The 20-year taper is intentional: a 2-year gap is more compelling than a 15-year gap, but the latter is not disqualifying. Products had long commercial lives; a mark filed a decade after the patent may still correspond to the same product.

A negative temporal score (trademark predating the patent) is not disqualifying. Brand names often preceded their specific patents — a company could have used a product name commercially before the engineering team filed the covering patent. These pairs require closer historian scrutiny.

---

## Component 2: Classification Score (0.30, binary)

Fires when any of the patent's CPC classes falls in the project's product signal set.

Binary rather than graded: CPC classifications for pre-1940 patents were applied retroactively by algorithmic mapping, so fine-grained subclass precision is not reliable enough to justify a graded signal. Either the class is in scope or it is not.

Which classes constitute the signal set is defined by the project, not by the tool.

---

## Hard Exclusion: Company-Name Marks

Marks where the trademark text is the company name itself (e.g., a trademark filing for "REMINGTON RAND" by Remington Rand) are excluded before scoring. These represent brand identity, not product identity, and cannot correspond to a specific patent.

---

## Uncertainty Band

| Score range | Interpretation |
|---|---|
| ≥ 0.60 | Strong candidate — review recommended |
| 0.40–0.60 | Uncertainty band — signal enrichment helps |
| < 0.40 | Weak candidate — low priority for review |

Signal enrichment adds text-match fields (`title_name_hit`, `abstract_name_hit`, `goods_title_overlap`, `goods_abstract_overlap`) that can shift a pair's effective evidence weight without changing its numeric score. A 0.50 pair with a title hit and high goods overlap is materially different from a 0.50 pair with no text match.

---

## Implementation

`src/markery/specialist/matchmaker/score.py` — `total_score()`, `date_score()`, `class_score()`, `semantic_score()`
