# Instruction Card: Validate Variants

## When to use

After building the entity registry (`markery matchmaker build`) and before running candidate generation. Validates that every `patent_assignee` and `trademark_owner` variant string in `variants.csv` matches at least one record in the actual databases.

## Command

```bash
markery matchmaker validate-variants --data-dir projects/<project>
```

## Output

Per-entity output showing each variant string and its match count:

```
Entity 19: Deere and Company
  trademark   47x  DEERE & COMPANY
  patent       0x  DEERE AND COMPANY  *** NO MATCH ***
```

Exits 0 if all variants match. Exits 1 if any zero-match variants are found.

## Notes

- A zero-match variant means the string in `variants.csv` does not appear verbatim in the database. Common causes: incorrect punctuation, abbreviated vs. full form, the variant was not present in the loaded date window.
- Run `markery matchmaker suggest-variants "<entity name>"` to find the correct string.
- **Silent failure risk:** A variant that matches 0 records causes no candidates for that entity-source combination. `validate-variants` is the only way to detect this before running `markery match`.
- CSV quoting: if a variant name contains a comma, the entire field must be quoted in `variants.csv`, e.g. `"PATHE CINEMA, ANCIENS ETABLISSEMENTS PATHE FRERES"`. Unquoted commas silently corrupt the source field.
