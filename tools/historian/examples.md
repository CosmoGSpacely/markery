# Example Interactions

These examples use real records from the `trademarks.duckdb` database.

---

## Example 1: Company History from Trademark Records

**User:** What can you tell me about Guild Products Corporation from their trademark filings?

**Specialist:**

Guild Products Corporation of Philadelphia filed three marks under the GUILD name in 1922, all within a four-month window. That clustering is significant — it suggests a company establishing brand identity across multiple product lines simultaneously, not incrementally.

| Serial No | Filing Date | Mark Type | Status |
|---|---|---|---|
| 71159752 | 1922-02-24 | Stylized (5W23) | Dead — cancelled (710) |
| 71165547 | 1922-06-15 | Design (5000) | Live — backfile cancelled (626) |
| 71165548 | 1922-06-15 | Design (5000) | Dead — expired (900) |

The goods description on the June filings — "mucilage, paste, glue and sealing wax" — places them squarely in the office and stationery supply trade, a sector that expanded rapidly with the growth of commercial office work in the 1910s and 1920s. First use is recorded as February 17, 1922 for both, suggesting those marks were filed within months of product launch.

The February filing (71159752) uses drawing code 5W23 — a stylized mark, meaning words rendered in a distinctive visual form rather than plain typeset text. The company was investing in visual identity from the start. That this mark was later cancelled while the word marks survived suggests the visual version was abandoned or consolidated into the plainer brand.

One detail in the TSDR record for 71165547 earns a second look: the address field reads "REPUBLISHED BY STATIONERS' GUILD OF AMERICA, PHILADELPHIA, PA." A republication event in 1948 means someone was still actively managing this mark 26 years after filing. The connection to the Stationers' Guild suggests trade association involvement in the brand's persistence.

```sql
SELECT cf.serial_no, cf.filing_dt, cf.mark_draw_cd, cf.cfh_status_cd,
       s.statement_text, o.own_name, o.own_addr_2
FROM case_file cf
JOIN owner o ON cf.serial_no = o.serial_no
LEFT JOIN statement s ON cf.serial_no = s.serial_no
WHERE UPPER(o.own_name) LIKE '%GUILD PRODUCTS%'
ORDER BY cf.filing_dt;
```

---

## Example 2: Product Category Emergence

**User:** When did adhesive products start showing up in trademark filings, and what does that tell us about office supply culture?

**Specialist:**

Adhesive products — mucilage, rubber cement, paste, library glue — appear in USPTO filings from the 1870s onward, but registration density increases markedly through the 1910s and into the 1920s. This tracks the broader expansion of commercial office culture: as organizations grew, correspondence volumes rose, and stationery suppliers competed for institutional buyers placing volume orders.

The classification is itself revealing. Under the pre-Nice US system, adhesives landed in Class 5 (Pharmaceuticals and Chemicals) — a category that grouped them with medicines, dyes, and cleaning compounds. That placement reflects how these products were understood at the time: as chemical formulations, not as purpose-built office tools. The emergence of dedicated stationery brands like GUILD, and eventually purpose-built product lines with distinct trade identities, is part of how "office supplies" became a recognized commercial category rather than a corner of the pharmacy.

First-use dates in the filing record can serve as approximate market entry signals — self-reported and sometimes backdated conservatively, but directionally useful. A cluster of first-use dates in 1918–1922 in the adhesive category would fit the postwar commercial expansion, as businesses re-tooled for peacetime growth and secretarial work became more systematized.

```sql
SELECT cf.serial_no, cf.filing_dt, c.first_use_any_dt, s.statement_text,
       o.own_name, o.own_addr_2
FROM case_file cf
JOIN classification c ON cf.serial_no = c.serial_no
JOIN statement s ON cf.serial_no = s.serial_no
JOIN owner o ON cf.serial_no = o.serial_no
WHERE LOWER(s.statement_text) LIKE '%mucilage%'
   OR LOWER(s.statement_text) LIKE '%paste%'
   OR LOWER(s.statement_text) LIKE '%adhesive%'
ORDER BY c.first_use_any_dt;
```

---

## Example 3: Reading a Mark Type as a Commercial Signal

**User:** What did it mean for a company in the 1920s to file a stylized mark rather than a word mark?

**Specialist:**

Filing a stylized mark in the 1920s was a deliberate investment. It required artwork — a designed rendering of the name or symbol — to be filed with the application. That meant design work, reproduction costs, and a clear intention to build visual brand recognition rather than simply staking out a name in plain text.

In the dataset, this distinction is encoded in the `mark_draw_cd` field. A code beginning with `4` or the value `5000` indicates a standard or design mark — the name or symbol with no particular visual treatment. A code like `5W23` indicates a stylized mark: words combined with design elements, filed as a specific visual artifact.

The 1920s were the decade American commercial design fully arrived. Art Deco aesthetics were moving from European luxury goods into mass-market American products. Companies that filed stylized marks in this period were participating in that shift — treating brand identity as something to be designed, not just named.

The tradeoff, which companies may or may not have understood clearly, is that stylized marks are narrower in scope. A word mark on GUILD covers the word in that class. A stylized mark on a particular rendering of GUILD covers that rendering — a competitor using the same word in different lettering might not infringe. Whether a company in 1922 made this choice strategically or simply wanted the visual protection is rarely answerable from the filing record alone. But the choice itself is evidence of how the company understood its competitive position.
