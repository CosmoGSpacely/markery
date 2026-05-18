# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

## Phase 5 — Corpus Expansion

**Goal:** Markery can support research into typewriter, calculator, and tabulating companies. The patent corpus covers all seven CPC product classes; a second project can be started without infrastructure work.

### Actions

**D001 — Fetch remaining CPC classes** *(promoted from DEFERRED)*

Fetch B41J (typewriters), B41L (duplicating), G06C (calculating machines), G06K (data recognition), G09F (display devices) into `patents.duckdb`. Infrastructure is in place; this is an operational fetch.

```bash
markery patent build --resume
```

Classes to add: `B41J B41L G06C G06K G09F`. After the fetch, run `markery status` to confirm row counts increased.

**New entities for information-systems**

Add companies with typewriter and calculator marks to the registry. Candidates from `information-systems/RESEARCH-AGENDA.md`:
- Smead Mfg. (SMEAD'S TELL VISION SYSTEM, serial 71403472)
- Library Bureau
- WHEELDEX owner (serial 71321669 — owner unknown, needs research)

Procedure: edit `specialist/matchmaker/build.py` → `markery matchmaker build` → `markery match information-systems`.

**Second project setup**

Document what it takes to start a new research project and verify the tooling is project-agnostic end-to-end:
1. Create `projects/<new-project>/` with `entities.txt`, `matches/`, `content/`
2. Run `markery match <new-project>` — confirm candidates generate
3. Run `markery site build <new-project>` — confirm site builds with no placeholder content

**Phase gate:** `patents.duckdb` includes all seven CPC classes; a second project produces a working site build.

---

## Backlog

Items not yet in a phase — candidates for Phase 6 once Phase 5 is underway.

| Item | Notes |
|---|---|
| Trademark specialist CLI (`markery trademark`) | Build out the trademark specialist with explicit subcommands alongside `matchmaker` and `patent` |
| D002 — Referenced images | Switch site output from base64-embedded to file references for HTTP cacheability |
| D003 — Patent drawings from PDF | When an essay needs inline patent figure images |
| D004 — Events table | Prosecution history from `event.csv` (~3 GB) |
| D005 — Foreign application data | Madrid Protocol records for international comparisons |
