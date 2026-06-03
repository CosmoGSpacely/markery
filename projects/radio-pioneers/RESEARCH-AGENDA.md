# Radio Pioneers — Research Agenda

Candidate confirmed pairs to investigate, ranked by expected evidence quality.
"Evidence quality" = clarity of the patent–trademark correspondence and availability
of primary sources to verify it.

---

## Tier 1 — Strong candidates (pursue first)

### De Forest AUDION — vacuum tube + trademark
- **Patent:** Lee De Forest's triode audion tube — US879532 (1908, "Space Telegraphy")
  and successors. Assigned to De Forest Radio Telephone and Telegraph Co.
- **Trademark:** AUDION — USPTO serial TBD; search `DE FOREST RADIO COMPANY` as owner.
- **Why strong:** De Forest is outside the RCA pool; the patent–trademark link is direct
  and well-documented in secondary literature. The word "Audion" was both De Forest's
  coined term for the device and his registered mark.
- **Risk:** Early De Forest patents predate the USPTO's modern TSDR coverage window for
  design marks; may need to use full-text search rather than serial lookup.

### Atwater Kent receiver — circuit patents + ATWATERKENT mark
- **Patent:** Atwater Kent breadboard receiver patents, ca. 1922–1925. Search patent
  assignee ATWATER KENT MANUFACTURING CO for H04B class, 1920–1930.
- **Trademark:** ATWATERKENT — search owner ATWATER KENT MANUFACTURING COMPANY.
- **Why strong:** Atwater Kent's breadboard receiver was a distinctive patented design;
  the brand name is a direct compound of the founder's name, making the trademark
  registration straightforward to locate and verify.

### RCA RADIOLA — receiver line + superheterodyne patents
- **Patent:** Armstrong superheterodyne circuit patents, assigned to RCA (via AT&T cross-
  license). Search RADIO CORPORATION OF AMERICA as assignee for H04B, 1920–1935.
- **Trademark:** RADIOLA — search owner RADIO CORPORATION OF AMERICA.
- **Why moderate-strong:** Patent assignee complexity (Armstrong's original patents may be
  assigned to AT&T or Columbia, with RCA as licensee, not assignee). Focus on patents
  where RCA is the direct assignee.

---

## Tier 2 — Moderate candidates

### Westinghouse AERIOLA — early receiver + broadcasting patents
- **Patent:** Westinghouse early broadcast transmitter patents, H04B class, 1919–1925.
  Assignee: WESTINGHOUSE ELECTRIC & MANUFACTURING CO.
- **Trademark:** AERIOLA — search owner WESTINGHOUSE ELECTRIC AND MANUFACTURING COMPANY.
- **Note:** AERIOLA was Westinghouse's consumer receiver brand before the RCA licensing
  agreement; after the agreement, Westinghouse's consumer products were rebranded RADIOLA
  under the RCA umbrella. The mark may have had a short registration life.

### Zenith ZENITH mark — early circuit patents + brand
- **Patent:** Zenith/Chicago Radio Laboratory circuit patents, H04B class, 1920–1930.
  Assignees: ZENITH RADIO CORPORATION, CHICAGO RADIO LABORATORY.
- **Trademark:** ZENITH — search owner ZENITH RADIO CORPORATION.
- **Note:** Zenith's patent history is complicated by the Chicago Radio Laboratory
  predecessor. The ZENITH trademark may predate the formal Zenith Radio Corporation
  entity — verify founding date against mark filing date.

---

## Tier 3 — Low-priority / speculative

### De Forest OSCILLION — oscillator tube mark
- OSCILLION was a De Forest product mark for a specific oscillator tube variant.
  Less documented than AUDION; pursue only if AUDION pair is fully confirmed.

### RCA RADIOTRON — tube mark
- RADIOTRON was RCA's consumer vacuum tube product line. Strong brand but the patent
  correspondence is diffuse (many tube patents across GE/Westinghouse assignees).

---

## Open Questions

1. **Patent sweep depth:** Do H04B, H01J, H03F, H04R sweeps return enough pre-1940 records?
   Radio CPC classes may be thin in the EPO OPS data window. Document actual counts after P5.

2. **De Forest patent dates:** US879532 (1908) predates the current EPO sweep range if the
   sweep starts at 1918. Widen lower bound to 1905 for entity_id 5 if needed.

3. **RCA pool boundary:** RCA CORP has 2,885 radio-class patents already in the DB —
   well above the gate. GEN ELECTRIC (266 H04B patents) is also present. Do not add
   GE as an RCA variant unless a specific confirmed pair requires it; document any
   GE-assignee pair separately as a pool-licensed product.

4. **Patent sweep depth (P5 finding):** H04B/H01J/H03F/H04R sweeps for 1918–1940 via
   EPO OPS returned +0 new records (CPC reclassification coverage is incomplete for
   pre-1940 US patents; API also hit 403 rate limits). The 11,213 radio-class patents
   in the DB are co-classifications from prior sweeps. ZENITH RADIO CORPORATION and
   DE FOREST entity strings are absent — their radio patents are not in the DB.
   Mitigation: use `markery patent pull <patent_no>` to add known De Forest and Zenith
   patents individually. D007 (PatentsView) does not help for 1918–1940.

5. **EPO-normalized assignee strings:** EPO OPS truncates and reformats names.
   Verified mappings now in variants.csv: "RCA CORP" (not "RADIO CORPORATION OF
   AMERICA"); "FOREST RADIO COMPANY DE" (not "DE FOREST RADIO COMPANY"). Always
   run `markery matchmaker suggest-variants` before assuming a variant string works.
