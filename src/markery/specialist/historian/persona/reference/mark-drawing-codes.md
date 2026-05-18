# Mark Drawing Codes

## Dataset Format

In the `trademarks.duckdb` database (built from the 2011 USPTO CSV dataset), drawing codes appear in `case_file.mark_draw_cd` as 4-character alphanumeric strings. These differ from the single-digit codes used in the TSDR API and modern USPTO systems — the first character is the same, so `3000` in the database corresponds to `3` in the API.

## Code Categories

| Prefix | Category | Historical Notes |
|---|---|---|
| `1xxx` | Typeset word mark | Historical form used before standard character marks; name in plain typed text |
| `2xxx` | Design/illustration with color | Visual mark where color is claimed as a feature |
| `3xxx` | Design/illustration, black & white | Visual mark without color claim; most scanned historical design marks |
| `4xxx` | Standard character (word mark, modern) | Name in any font or style; broadest protection |
| `5xxx` | Stylized or design-plus-word | Name rendered in specific lettering, or words combined with design elements |

## Common Specific Codes

| Code | Description |
|---|---|
| `3000` | Design mark, black and white, no words |
| `4000` | Standard character mark (word only) |
| `5000` | Stylized/design mark, general |
| `5W23` | Stylized words/letters/numbers with design elements |
| `2xxx` | Color drawing — uncommon in pre-1940 filings |

## Filtering in SQL

```sql
-- Non-word marks (design, stylized, illustrated)
WHERE mark_draw_cd LIKE '2%'
   OR mark_draw_cd LIKE '3%'
   OR mark_draw_cd LIKE '5%'

-- Word marks only
WHERE mark_draw_cd LIKE '1%'
   OR mark_draw_cd LIKE '4%'
   OR mark_draw_cd = '5000'
```

## Historical Interpretation

The distribution of mark types in a filing cohort is itself evidence. Industries that filed predominantly word marks were competing on name recognition. Industries that filed design marks were competing on visual identity — packaging, labels, branded goods. The shift from typeset (1xxx) to standard character (4xxx) codes across the dataset also reflects modernization in USPTO practice, not necessarily any change in the marks themselves.

For pre-1940 filings, 3xxx codes dominate among design marks because color printing and color mark claims were rare and expensive. A black-and-white design mark in this period often represents a product label or packaging element that was printed in color in practice but filed monochromatically.
