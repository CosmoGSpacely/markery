# Public-Domain Media Sources — Survey (Phase 24 P2, Step 1)

Survey of public-domain (and unambiguously free-licensed) media sources for enriching
Markery project pages with photos, maps, drawings, and video. Working reference for the
P2 librarian/historian/publisher extension; archived to `archive/` on P2 completion.

**Admission rule (hard):** only **public domain** or **unambiguously free** media is
admitted. Default-admit: `PD` / `PD-US-expired` / `PD-USGov` / `CC0` / rightsstatements.org
"No Copyright". Admit-with-attribution: `CC-BY`, `CC-BY-SA` (capture credit + license).
**Never admit:** `*-NC`, `*-ND`, "rights reserved", "no known restrictions" *without a
positive PD basis*, or anything whose license can't be resolved to one of the above.
Every admitted item stores its license **and** provenance (see schema below). When in
doubt, skip — same discipline as essays: state what it is and where it came from, invent
nothing.

---

## Provenance schema (per media item)

Stored alongside the file so the publisher can render an honest caption and the licensing
is auditable:

| field | meaning |
|---|---|
| `slug` | stable id (kebab) |
| `kind` | `photo` \| `map` \| `drawing` \| `video` |
| `source` | `wikimedia_commons` \| `loc` \| `nara` \| `dpla` \| `internet_archive` \| `uspto` |
| `source_url` | canonical human page (the item's landing page, not the binary) |
| `file_url` | direct media URL fetched |
| `title` | item title as given by the source |
| `creator` | author/photographer/agency (may be "Unknown") |
| `date` | creation/publication date (as given) |
| `license` | normalized code: `PD` \| `PD-US-expired` \| `PD-USGov` \| `CC0` \| `CC-BY` \| `CC-BY-SA` \| `NoKnownCopyright` |
| `license_url` | machine URI (creativecommons.org/… or rightsstatements.org/…) when present |
| `rights_statement` | **verbatim** rights text from the source (the audit trail) |
| `attribution_text` | rendered credit line for the caption |
| `acquired_at`, `sha256`, `format`, `width`, `height` | acquisition + integrity metadata |

---

## Sources (in recommended adoption order)

### 1. USPTO patent drawings — already in-corpus ✅
- **Media:** patent figures (line drawings). Already fetched via EPO OPS into
  `patent_figures` (`src/markery/specialist/patent/figures.py`) and rendered on patent
  cards/detail and embedded via `[[figure:<patent_no>]]`.
- **Rights:** US patent drawings are **not subject to copyright** (US government works /
  patent documents). `license = PD-USGov`.
- **Attribution:** patent number + "USPTO". Already captured.
- **Action:** no new work — documents the precedent the media flow should mirror.

### 2. Wikimedia Commons — primary source for entities & people
- **Media:** photos, logos, maps, drawings, some video. Huge coverage of companies,
  founders, products of the 1900–1939 era.
- **API:** MediaWiki API at `https://commons.wikimedia.org/w/api.php`
  - search: `action=query&list=search&srsearch=…&srnamespace=6` (File namespace)
  - rights: `action=query&prop=imageinfo&iiprop=url|extmetadata&titles=File:…` →
    `extmetadata.LicenseShortName`, `.License`, `.Artist`, `.Credit`, `.UsageTerms`,
    `.AttributionRequired`, `.Restrictions`.
- **License determination:** parse `extmetadata`. Admit when `License` ∈
  {`pd`, `cc0`} or `LicenseShortName` matches a PD template (`PD-US-expired`, `PD-old`,
  `PD-Art`, `PD-USGov`). `CC-BY`/`CC-BY-SA` admit-with-attribution (use `Artist`+`Credit`).
  Reject if `Restrictions` is non-empty (trademark/personality/etc.) or license is NC/ND.
- **Attribution:** even for PD, store `Artist` + Commons file URL.
- **Caveat:** a file can be PD in the US but restricted elsewhere; we publish US-scoped, so
  `PD-US-expired` (works **published before 1931** — i.e. 1930 or earlier, as of 2026) is
  the safe core. The cutoff advances one year every January 1.

### 3. Library of Congress (loc.gov) — Prints & Photographs
- **Media:** historical photographs, maps, posters (PPOC, Panoramic Maps, etc.).
- **API:** append `?fo=json` to any loc.gov item/search URL
  (e.g. `https://www.loc.gov/photos/?q=…&fo=json`); item JSON carries `item.rights`,
  `rights_advisory`, and reproduction numbers.
- **License determination:** LoC uses **rights statements**, not licenses. Admit only when
  the rights field gives a positive PD basis ("No known restrictions on publication" **plus**
  a PD rationale, or an explicit PD/US-gov statement). Record the rights text verbatim;
  "no known restrictions" alone is a flag, not a guarantee — keep it but mark `license =
  NoKnownCopyright` and prefer items with an explicit PD basis.
- **Attribution:** "Library of Congress, Prints & Photographs Division" + reproduction no.

### 4. National Archives Catalog (NARA)
- **Media:** federal photographs, maps, films — overwhelmingly US-gov PD.
- **API:** `https://catalog.archives.gov/api/v2/` (records search; media via
  `digitalObjects`). Check `useRestriction` / `accessRestriction` — donated/seized
  materials can carry restrictions; admit only "Unrestricted"/PD.
- **Attribution:** "U.S. National Archives" + National Archives Identifier (NAID).

### 5. DPLA — aggregator (breadth, indirect rights)
- **Media:** aggregates millions of items from US libraries/archives/museums.
- **API:** `https://api.dp.la/v2/items` (API key required). Rights via
  `sourceResource.rights` and increasingly **rightsstatements.org** URIs.
- **License determination:** admit only rightsstatements.org `NoC-US` / `NKC` with a PD
  basis, or CC0/PD. DPLA links to the **provider**; verify rights at the provider before
  admitting. Treat DPLA as a discovery layer, not the rights source of record.
- **Caveat:** key provisioning + per-provider variance make this lower priority than 2–4.

### 6. Internet Archive — already integrated (text); add media
- **Media:** images, maps, **public-domain film/video** (e.g., Prelinger), audio.
- **API:** already used (`src/markery/specialist/librarian/sources/ia.py`). Metadata via
  `https://archive.org/metadata/<identifier>` → `licenseurl`, `rights`,
  `possible-copyright-status`.
- **License determination:** admit `licenseurl` ∈ CC0/PD or
  `possible-copyright-status = "NOT_IN_COPYRIGHT"`. **Caveat:** IA uploads are
  user-contributed and frequently mislabeled — require a positive PD/CC0 signal, never
  assume.

---

## Machine-readable license backbone

Normalize everything to two URI families plus a small PD vocabulary:
- **creativecommons.org/publicdomain/zero/1.0** → `CC0`; `/licenses/by/4.0` → `CC-BY`; etc.
- **rightsstatements.org** → `/vocab/NoC-US/` (No Copyright – US) and `/vocab/NKC/`
  (No Known Copyright) map to `PD`/`NoKnownCopyright`.
- Commons PD templates (`PD-US-expired`, `PD-Art`, `PD-USGov`, `PD-old-70`) → `PD`.

For our 1900–1939 scope the dominant, safest basis is **US copyright expiration**:
**works published before 1931 (1930 or earlier) are public domain in the US as of 2026**
(95-year term; the cutoff advances one year each January 1). This covers most period
photographs/maps/drawings from 1900–1930 on Commons, LoC, and NARA. **Works from
1931–1939 are not yet PD by expiration** (they enter the public domain in 2027–2035) — for
those, admit only on another positive basis: US-government authorship (`PD-USGov`), an
explicit PD dedication / `CC0`, or a free CC-BY/CC-BY-SA license.

---

## Integration plan (informs P2 Steps 2–4)

- **Storage:** `projects/<name>/library/media/<slug>/` holding the file + `metadata.json`
  (schema above); a `library/media/index.jsonl` for listing/search — mirroring the existing
  `library/works/` + `index.jsonl` model.
- **Librarian (Step 2):** `markery librarian media search <source> <query>` (no download)
  and `markery librarian media acquire <source> <id> --project <p>` (fetch + resolve license
  via the rules above + register metadata). Refuse to register anything that doesn't resolve
  to an admitted license; print the rights text on rejection.
- **Historian (Step 3):** embed via a `[[media:<slug>]]` token (parallel to
  `[[figure:<patent_no>]]`), resolved by the publisher Markdown renderer.
- **Publisher (Step 3):** render `<figure>` with the media + a caption that states *what it
  is*, the source, and the attribution/credit line, plus the license. Reuse the existing
  `.patent-figure` / `.essay-media` styling.
- **Run (Step 4):** enrich one project (candidate: `precision-tools` — small, already has
  mark images/figures) with a handful of PD Commons/LoC items for its companies; confirm
  attribution renders, licensing is sound, and `markery site build` / `site check` stay clean.

## Recommended adoption order

1. **Wikimedia Commons (PD-US-expired / CC0)** — best coverage of period company/person
   imagery, clean machine-readable rights. Start here in Step 2.
2. **Library of Congress** — high-quality PD photos/maps with explicit rights text.
3. **NARA** — US-gov PD films/photos.
4. **Internet Archive (media)** — PD film/video, with strict positive-PD checks.
5. **DPLA** — last; discovery aggregator, verify at provider.
