# CPC Class Reference

The Cooperative Patent Classification (CPC) is a hierarchical patent classification system maintained jointly by the EPO and USPTO. Markery uses CPC class codes as the primary scope parameter for `markery patent build`.

---

## Reading a CPC Code

CPC codes are hierarchical, read left to right:

```
B  42  F  1  /  04
│   │  │  │     │
│   │  │  │     └─ subgroup
│   │  │  └─────── main group
│   │  └────────── subclass
│   └───────────── class (2-digit)
└───────────────── section (letter)
```

**Example:** `B42F1/04` = Section B (Performing operations), Class 42 (Office supplies), Subclass F (Filing), Main group 1 (Indexing cards), Subgroup /04 (with means for displaying or viewing).

Markery's `--classes` argument takes the **4-character subclass code** (e.g., `B42F`, `G06C`), not the full subgroup. The build fetches all patents in that subclass for the given year range.

---

## Sections Relevant to Information-Systems Research

| Section | Domain |
|---|---|
| B | Performing operations; transporting |
| G | Physics (includes computing, calculating) |

The information-systems project works entirely within B and G.

---

## Classes Used in the Information-Systems Project

| Code | Title | Covers |
|---|---|---|
| `B42F` | Indexing cards; filing appliances | Card-index equipment, Kardex-type visible-record systems, vertical file appliances |
| `B42D` | Books; book covers; loose leaves; printed matter | Loose-leaf systems, binders, tab indexes |
| `B41J` | Typewriters; selective printing mechanisms | Typewriters, early keyboard devices |
| `B41L` | Apparatus for duplicating; manifolding | Carbon copying, mimeograph, spirit duplicators |
| `G06C` | Digital computers in which all the computation is effected mechanically | Mechanical calculators, comptometers, adding machines |
| `G06K` | Recognition of data; presentation of data; record carriers | Punched-card systems, early reading machines, tabulating equipment |
| `G09F` | Displaying; advertising; signs; labels or name-plates | Display racks, visible-index devices, visible-record equipment |

---

## How to Identify Classes for a New Research Subject

1. **Start with a product description.** What did the device physically do? File papers? Calculate? Print? Display records?
2. **Find the section.** Mechanical operations → B; Physics/computing → G; Chemistry → C; etc.
3. **Browse the 2-digit class.** EPO's CPC browser at `https://www.epo.org/searching-for-patents/helpful-resources/first-time-here/classification/cpc.html` lets you search by keyword or browse hierarchically.
4. **Test at the subclass level.** Use `markery patent build --classes <CODE> --year-start 1900 --year-end 1939` with a short year range first to estimate volume before committing to a full sweep.
5. **Expect imprecision.** Pre-1940 patents were classified retroactively by algorithmic mapping. The subclass level (4 characters) is reliable; subgroup-level precision is not. A patent for a visible-record filing device may appear in B42F, G09F, or both.

---

## Pre-1940 Classification Caveats

CPC was not applied to historical patents at the time of filing — it was mapped retroactively from earlier classification systems (US Class, IPC). This has three practical consequences:

1. **Subgroup precision is unreliable.** A patent clearly about card-index filing may appear at B42F or at a neighboring subclass. Do not assume subgroup boundaries are sharp for this period.
2. **Coverage varies by class.** Some classes (B42F, G06C) have been well-mapped for the 1900–1940 period. Others have gaps or over-inclusion.
3. **The scoring model uses binary class signals.** The MATCHMAKER scores a patent as "in the product signal set" if *any* of its CPC classes falls in the project's defined set. This is intentionally coarse — fine-grained subgroup matching would overfit to the imprecision of retroactive classification.

---

## Adding a New Class to a Project

1. Identify the subclass code (e.g., `G09F`).
2. Run a test build for a short year range to confirm volume and relevance:
   ```bash
   markery patent build --classes G09F --year-start 1900 --year-end 1904
   ```
3. Check what was added: `markery status`.
4. If the class is relevant, extend the year range and resume:
   ```bash
   markery patent build --classes G09F --year-start 1900 --year-end 1939 --resume
   ```
5. Regenerate candidates after the build completes:
   ```bash
   markery match <project> --force
   ```
