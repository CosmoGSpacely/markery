# Instruction Card: Entity Registry Management

## What the entity registry is

`entities.duckdb` holds two tables:

- `company_entity` — one row per canonical company identity (`entity_id`, `canonical_name`, `entity_type`, `industry`)
- `entity_name_variant` — all the name forms a company appears under in patent assignee fields and trademark owner fields

The registry is **shared across all projects**. Adding a variant for one project makes it visible to every other project that includes the same entity.

---

## Adding a new entity or name variant

Entity and variant data lives in per-project CSV files. To add a new entity:

1. **Edit `projects/<project>/entities.csv`** — add one row with a new unique `entity_id`:

   ```
   entity_id,canonical_name,entity_type,industry
   12,Remington Rand,manufacturer,office machinery
   ```

2. **Edit `projects/<project>/variants.csv`** — add one row per name form, including the canonical name itself if it appears verbatim in the source databases:

   ```
   entity_id,variant_name,source
   12,Remington Rand,patent_assignee
   12,Remington Rand,trademark_owner
   12,Remington Rand Inc,patent_assignee
   12,REMINGTON RAND,trademark_owner
   ```

3. **Rebuild the registry:**

   ```bash
   markery matchmaker build --data-dir projects/<project>
   ```

4. **Confirm the entity loaded:**

   ```bash
   markery matchmaker list
   ```

---

## The `source` column

`source` tells the matchmaker which database to search for each variant:

| Value | Searches |
|---|---|
| `patent_assignee` | `patents.assignee_name` column in `patents.duckdb` |
| `trademark_owner` | `owner.own_name` column in `trademarks.duckdb` |

Most entities need at least one variant for each source. A company that filed patents under "Remington Rand Inc." and registered trademarks under "REMINGTON RAND" needs both variants with their respective sources.

---

## Idempotent build

`markery matchmaker build` skips rows that already exist (matching on `entity_id` for entities; matching on `entity_id + variant_name + source` for variants). Re-running after adding rows is safe — existing rows are never duplicated or overwritten.

---

## Removing a variant

There is no remove command. To remove a variant, delete or comment the row from `variants.csv`, then drop and rebuild `entities.duckdb` from scratch:

```bash
rm data/entities.duckdb
markery matchmaker build --data-dir projects/<project>
```

Because variants are additive, the only way to remove one is to start from a clean database.

---

## Checking what is in the registry

```bash
# All entities with IDs, names, and industry
markery matchmaker list

# Row counts for both tables
markery matchmaker status
```

---

## Variant naming tips

- Exact match only — the matchmaker joins `variant_name = assignee_name` with no normalization. Check the actual strings in the source databases before adding variants.
- Include legal suffix variants: "Remington Rand", "Remington Rand Inc", "Remington Rand Inc." are distinct strings in patent records.
- Check for ALL CAPS variants — USPTO trademark owner fields are often stored uppercased.
- Do not add the canonical name as a variant unless that exact string appears in the source database.

---

## Human-readable request forms

```
"Add Rand Kardex Bureau to the entity registry with its patent and trademark variants."

"I need to add a new name variant for Wilson Jones — they appear as
 'Wilson Jones Co' in the patent assignee field."

"How many entities and variants are currently in the registry?"
```
