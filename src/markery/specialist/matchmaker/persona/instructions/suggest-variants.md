# Instruction Card: Suggest Variants

## When to use

At project setup, to find the exact patent assignee strings and trademark owner strings that match a canonical entity name. The output lists candidate variant strings ranked by similarity score, which you then add to `variants.csv`.

## Command

```bash
markery matchmaker suggest-variants "<Canonical Entity Name>"
```

## Output

Two ranked lists — patent assignees and trademark owners — showing each candidate string, its occurrence count, and a Jaccard similarity score against the canonical name:

```
Variant suggestions for: 'Goodyear Tire and Rubber'

Patent assignees:
  0.82   6x  GOODYEAR TIRE & RUBBER COMPANY, THE

Trademark owners:
  0.75  47x  GOODYEAR TIRE & RUBBER COMPANY, THE
```

## Notes

- Similarity scoring normalises common suffixes (INC, CORP, LTD, MFG) before comparison. Abbreviation differences (& vs AND) are handled.
- **False positives are common** when entity names share common words with unrelated companies. Always inspect representative patent titles before adding a variant — use a direct DuckDB query (`SELECT patent_no, title FROM patents WHERE assignee_name = ?`) to verify.
- Re-run after each CPC sweep: newly ingested patents may introduce additional assignee string variants not present at project setup.
- The minimum similarity threshold is 0.30; strings below that threshold are not shown.
