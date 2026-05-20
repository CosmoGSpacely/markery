# Reference: Uncertainty Band

## Definition

The uncertainty band is the score range [0.40, 0.60]. Pairs in this range have enough temporal and classification evidence to warrant attention, but not enough to resolve without additional context.

| Score range | Interpretation |
|---|---|
| ≥ 0.60 | Strong candidate — review recommended; structural evidence is compelling |
| 0.40–0.60 | Uncertainty band — signal enrichment may resolve; historian judgment required |
| < 0.40 | Weak candidate — low priority; temporal or classification evidence is thin |

The band boundaries are not thresholds for accept/reject. A score of 0.38 is not automatically dismissed; a score of 0.61 is not automatically accepted. The score ranks candidates for review, not for confirmation.

---

## How the band arises

A pair lands in the uncertainty band when it scores on exactly one structural component:

- **Temporal only (score ~0.30–0.50, no class signal):** The trademark was filed within 20 years of the patent grant, but the patent's CPC classes are not in the project's product signal set. Possible causes: the patent covers ancillary technology, the CPC mapping is imprecise for pre-1940 patents, or the class set needs expansion.

- **Class only (score = 0.30, temporal near zero):** The CPC class fires, but the trademark was filed long after the patent grant (or before it). Possible causes: the company licensed a mark to a product much later, or the trademark predates the specific patent but not the product line.

---

## How signal enrichment narrows the band

`markery patent signals <project>` adds four text-match fields to each candidate. After rescoring, these can shift a pair out of the band:

| Signal field | Max bonus |
|---|---|
| `title_name_hit` — mark name appears in patent title | +0.20 |
| `abstract_name_hit` — mark name appears in abstract | +0.10 |
| `goods_title_overlap` — G&S tokens / patent title tokens Jaccard > 0.05 | +0.10 |
| `goods_abstract_overlap` — G&S tokens / abstract tokens Jaccard > 0.05 | +0.05 |

A pair at 0.50 with a title hit (score → 0.70) moves clearly above the band. A pair at 0.50 with no signals remains at 0.50 and should be escalated to historian review.

Semantic bonus is capped at 0.25. The maximum achievable total score is 0.80.

---

## When to fetch abstracts vs goods descriptions

`markery match <project> --resolve` identifies what data is missing for band pairs:

**Missing abstracts (`Missing abstracts: N patent(s)`):**
```bash
markery patent signals <project>
```
This fetches patent abstract text from `patents.duckdb` and computes signal fields. Does not make external API calls — reads from what is already in the database.

**Missing goods descriptions (`Missing G&S text: N trademark(s)`):**
```bash
markery trademark enrich-project <project> --source candidates --min-score 0.40
```
This fetches goods and services text via the USPTO TSDR API. Requires USPTO API credentials.

After fetching, run rescore:
```bash
markery match rescore <project>
```

---

## When to escalate to historian review

Escalate a band pair to the historian when:

- Signal enrichment has been run and the pair remains in the band (0.40–0.60 after rescore)
- The goods description and patent abstract are both present but semantic signals are weak
- The temporal gap is negative (trademark filed before patent) but the class signal fires — the pair may reflect a product line that preceded the specific patent

The historian can resolve these pairs through primary-source research (contemporaneous advertisements, company catalogs, trade press) that the automated score cannot capture.

---

## Reporting band size

```bash
markery match <project> --resolve
```

Reports: band pair count, missing abstracts count, missing goods count, and pairs resolvable from existing data.

```bash
markery match status <project>
```

Shows current pipeline state (generated, enriched, rescored timestamps) and review progress (confirmed, rejected, unreviewed counts). Use this to assess whether enrichment and rescore have been run.
