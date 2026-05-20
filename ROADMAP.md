# Markery Roadmap

Active and upcoming tool development. Items originate in `DEFERRED.md` and are promoted here when active. Completed phases are in `archive/`.

---

Phase 8 — Specialist Completeness — CLOSED 2026-05-20. Archived to `archive/SPECIALIST-REVIEW-2026-05-20.md`.

---

## Phase 9 — Tool Generalization: Image Enhancement & Wikipedia

**Opened:** 2026-05-20  
**Scope:** Two publisher-owned tools currently constrained to specific workflows. Goal: both usable from any project without restriction.

---

### Current State — Image Enhancement

The image enhancement pipeline lives in `src/markery/specialist/publisher/image_enhancement/` and exposes three CLI subcommands under `markery enhance`:

| Subcommand | Function | Status |
|---|---|---|
| `gallery` | Build self-contained HTML gallery from DB images or enhanced PNGs | **Working** — no optional deps required |
| `enhance` | Upscale one mark 4× with Real-ESRGAN, optionally vectorize to SVG | **Broken** — pipeline import fails; see below |
| `batch` | Enhance all marks matching a SQL WHERE clause | **Broken** — same root cause |

**Module dependency map:**

```
markery enhance enhance / batch
  → image_enhancement/cli.py  (fixed: lazy-imports pipeline)
    → image_enhancement/pipeline.py
        → binarize.py   imports cv2 (✅ installed), vtracer (❌ not installed)
        → upscale.py    imports cv2 (✅), numpy (✅); realesrgan inside fn body (❌ not installed)
```

`gallery` does not touch pipeline.py. The lazy-import fix in cli.py and `__init__.py` (2026-05-20) means `gallery` is completely isolated from optional deps.

**Blocking layers:**

1. **vtracer** — not installed. Single package, no transitive deps (`pip install vtracer`). Blocks `binarize.py` import, which blocks `pipeline.py`, which blocks both `enhance` and `batch`. Fix is trivial.

2. **realesrgan** — not installed. Heavy ML chain: pulls in PyTorch, torchvision, basicsr, facexlib, gfpgan, scipy, scikit-image (~1–2 GB installed). realesrgan's own imports are deferred to the `upscale()` function body, so once vtracer is installed the pipeline *imports* cleanly — but calling `upscale()` fails at runtime.

**What happens after installing only vtracer:**
- `pipeline.py` imports successfully
- `binarize.threshold()` and `binarize.vectorize()` work (cv2 + vtracer path)
- `upscale.upscale()` raises ImportError on first call (realesrgan/basicsr absent)
- Result: `enhance` and `batch` fail with a runtime error rather than an import error — better, but still broken

**Current workaround:** manual Pillow LANCZOS 4× upscale (used for the Chicago Pneumatic test, 2026-05-20). Produces acceptable output for historical scans; no SVG vectorization.

---

### Options — Image Enhancement

**Option A — Graceful Pillow fallback (recommended)**  
In `upscale.py`, wrap the realesrgan import in a try/except. If realesrgan is absent, fall back to Pillow LANCZOS 4×. Log or print a one-line notice. The pipeline then runs end-to-end with no ML stack required. SVG vectorization still works (binarize path is independent of upscaling). The `model_used` field in MarkResult reports `"lanczos-fallback"` instead of `"x4plus-anime"`. The full Real-ESRGAN path is activated automatically whenever realesrgan is installed.

Trade-off: Lanczos output is visibly softer than Real-ESRGAN on historical scans, but fully usable for gallery, essay illustration, and Wikipedia upload. Any project can run `enhance` without the ML stack.

**Option B — Separate lightweight optional group**  
Split pyproject.toml `[enhance]` into `[enhance-light]` (opencv + vtracer) and `[enhance-full]` (adds realesrgan). Document the tiers. No code change to the pipeline — `enhance` still fails without the full stack.

Trade-off: cleaner dependency communication but does not solve the usability problem. Projects still cannot run `enhance` without committing to the ML install.

**Option C — Full ML stack install**  
`pip install -e ".[enhance]"` installs realesrgan, which pulls in PyTorch. On a GPU machine this is the highest-quality path. On CPU it runs but is slow (~30–120s per image depending on size). Model weights are downloaded on first use (~64 MB for x4plus-anime).

Trade-off: only viable on machines where ~2 GB of ML deps and weight downloads are acceptable. Not appropriate as the default for a research CLI.

---

### Options — Wikipedia

The Wikipedia tooling lives in `src/markery/specialist/publisher/wikipedia/` and exposes two CLI subcommands:

| Subcommand | Function | Status |
|---|---|---|
| `draft` | Generate wikitext from a confirmed match record and its essay | **Working but restricted** — requires confirmed.jsonl entry with `patent_no`, `grant_dt`, `entity`, `essay_path` |
| `submit` | Show diff and POST to Wikipedia API | Working but restricted by same requirement |

**Current `draft` command contract:**

```
markery wikipedia draft <project> <slug>
```

Reads `projects/<project>/matches/confirmed.jsonl`, finds the entry whose `slug` matches, then calls `build_draft_wikitext()` which requires:

- `trademark` — mark name
- `patent_no` — US patent number (patent-trademark pair specific)
- `trademark_serial` — USPTO serial number
- `entity` — canonical entity name
- `filing_dt` / `grant_dt` — dates
- `essay_path` — path to historian's markdown essay

**What this excludes:**

- Standalone trademark research (no patent pair): e.g., the Chicago Pneumatic CP mark (serial 71299042) — has an essay and a serial but no patent match
- Gallery-driven research: marks surfaced through `monthly-image-review` that warrant Wikipedia coverage but are not in any project's `confirmed.jsonl`
- Any future project type that does not use the patent-trademark confirmation pipeline
- `markdown_to_wikitext()` is standalone and project-neutral, but there is no CLI path to reach it without a confirmed pair

**What `build_draft_wikitext()` produces that is pair-specific:**
The patent citation ref (`{{US patent|<no>}}`), the `[[Category:United States patents]]` tag, and the `assignee: <entity>` attribution in the sources section. Everything else (body conversion, trademark ref, sources section) is generalizable.

---

### Options — Wikipedia

**Option A — Add `from-essay` subcommand (recommended)**  
New command: `markery wikipedia from-essay <essay_path> --out <path> [--title <title>] [--serial <serial>] [--categories <cat>...]`  
Calls `markdown_to_wikitext()` directly, appends a minimal sources section (TSDR ref if serial is provided, no patent ref), writes wikitext to the specified output path. Does not require `confirmed.jsonl` or a project directory. Works for any research context.

Trade-off: adds a second entry point for Wikipedia drafting. The `draft` command (patent-trademark pair path) stays unchanged; `from-essay` is additive.

**Option B — Optional fields in `draft`**  
Make `patent_no` and `grant_dt` optional in `build_draft_wikitext()`. When absent, omit the patent citation ref and patent category. The `draft` command already reads from confirmed.jsonl; extend it to also accept `--essay <path>` to bypass the confirmed.jsonl lookup entirely.

Trade-off: less clean interface (one command doing two jobs), but fewer commands for users to learn. The confirmed.jsonl lookup path and the essay-path path share the same subcommand.

**Option C — Project-level wikipedia directory convention**  
Add a `wikipedia` property to the `Project` class. Extend `markery wikipedia draft` to accept a project name and any essay slug present in `projects/<project>/essays/` rather than only slugs in `confirmed.jsonl`. This keeps the project-centric model but removes the patent-pair requirement.

Trade-off: still requires the essay to live inside a known project directory. Does not help for ad-hoc use outside a project.

---

### Work Plan

**P1 — Image enhancement: install vtracer, add Lanczos fallback**

1. Install vtracer into the project venv: `pip install vtracer`
2. In `upscale.py`, wrap the realesrgan/basicsr imports in a try/except inside `upscale()`. On ImportError, log a notice and return `img.resize((w*4, h*4), Image.LANCZOS)`.
3. Update `MarkResult.model_used` convention: `"x4plus-anime"` when Real-ESRGAN ran, `"lanczos-fallback"` otherwise.
4. Update `pyproject.toml`: add `vtracer` to `[enhance]` optional group (it is a required dep for the pipeline to import, not optional).
5. Verify `markery enhance enhance 71299042 --out-dir /tmp/test` runs end-to-end.
6. Verify `markery enhance batch "..."` runs end-to-end.
7. Verify `markery enhance gallery` still works (no regression).

**P2 — Wikipedia: add `from-essay` subcommand**

1. Add `cmd_from_essay()` to `wikipedia/cli.py`. Signature: `markery wikipedia from-essay <essay_path> --out <out_path> [--title <title>] [--serial <serial>] [--category <cat>]...`
2. Build a `build_standalone_wikitext()` function in `wikitext.py`. Calls `markdown_to_wikitext()` on the essay body, then appends:
   - A sources section with a TSDR ref if `--serial` is provided
   - Category tags from `--category` args (plus `[[Category:Trademarks of the United States]]` by default if serial is present)
3. Register the subcommand in the argparse block.
4. Test: `markery wikipedia from-essay projects/monthly-image-review/essays/chicago-pneumatic-cp.md --out projects/monthly-image-review/wikipedia/chicago-pneumatic-cp.wiki --serial 71299042 --title "Chicago Pneumatic Tool Company" --category "Pneumatic tools" --category "Manufacturing companies based in New York City"`
5. Verify output matches expected wikitext structure.

**P3 — Update pyproject.toml dependency documentation**

Clarify the three-tier install in pyproject.toml comments and SETUP.md:
- Base: gallery works, no optional extras needed
- `[enhance]` (after P1 fix): enhance + batch + gallery work, Lanczos upscaling (cv2 + vtracer required, auto-installed)
- `[enhance]` with realesrgan manually installed: full Real-ESRGAN 4× upscaling activated automatically

**P4 — Wikipedia live edit test**

P4 depends on P2 (from-essay command). Goal: demonstrate the full write path — auth, targeted edit, diff review, submission — on real Wikipedia articles using primary source data from Markery databases. Graduated from zero-risk sandbox through to a mainspace citation or external link.

**What the article scan found (2026-05-20, read-only):**

| Article | Length | TSDR ref | Relevant gap | Markery data available |
|---|---|---|---|---|
| Chicago Pneumatic | 15,173 chars | None | External links section has 5 links, no TSDR; article has no mention of 1930 CP trademark filing | Serial 71299042, Reg 274,689, filed 1930-04-18; essay and wikitext draft already written |
| Soundex | 11,723 chars | None | Russell/Odell sentence uncited for trademark/patent filing; no trademark section | Serial 71246709 filed 1927-03-31; but owner chain complex (Kardex Systems now, Remington Rand historically) — requires attribution research before editing |
| Remington Rand | 16,502 chars | None | Mentions Rand Kardex as subsidiary; no trademark citations | SOUNDEX, VARIADEX, KARDEX pairs confirmed; good second-tier target |
| Kardex | 454 chars | None | Disambiguation stub; KARDEX trademark confirmed (serial 71426576, Reg 377,986) | Better as addition to Kardex Group article than the dab page |

Chicago Pneumatic is the primary test target: clean owner chain, existing essay, article already has a logo on Commons, and the External links gap is the lowest-risk entry point.

**Infrastructure needed before P4 can run:**

1. **Wikipedia account** — Must be created manually at en.wikipedia.org. Bot passwords are issued under Special:BotPasswords once logged in. Credentials go in `.env` as `WIKIPEDIA_USERNAME` and `WIKIPEDIA_BOT_PASSWORD`. The API client (`wikipedia/api.py`) already reads these.

2. **`markery wikipedia verify-credentials`** — New subcommand. Calls `client.login()`, reports success or the error from the API. No read or write operation beyond the login token exchange. Analogous to `markery trademark verify-credentials`. Add to `wikipedia/cli.py`.

3. **`markery wikipedia add-external-link`** — New subcommand for targeted read-modify-write on an External links section. Safer than full-page replacement for this class of edit. Signature: `markery wikipedia add-external-link <page-title> <url> <label> [--summary <msg>]`. Reads current wikitext, finds the `== External links ==` section, appends `* [<url> <label>]`, shows a unified diff, prompts for confirmation, then calls `edit_page()`. If the URL is already present, exits with a "already linked" notice.

**Test sequence (graduated):**

*Stage 4a — Sandbox* (zero risk)  
Write a dated test note to `Wikipedia:Sandbox` using the existing `submit` command with `--title "Wikipedia:Sandbox"`. Draft content: a single paragraph noting that this is a test edit from a research tool verifying the auth and write flow. Confirm the edit appears in the sandbox revision history. Verify the interactive diff-and-confirm flow works end-to-end. Revert is automatic (sandbox is periodically reset by Wikipedia bots).

*Stage 4b — External link addition* (minimal impact, mainspace)  
Add the TSDR filing URL to the Chicago Pneumatic article's External links section using `add-external-link`:
```
markery wikipedia add-external-link "Chicago Pneumatic" \
  "https://tsdr.uspto.gov/#caseNumber=71299042&caseType=SERIAL_NO&searchType=statusSearch" \
  "USPTO TSDR — CP trademark Serial No. 71299042 (filed 1930)" \
  --summary "Add primary USPTO filing record for the CP trademark (Serial No. 71299042, filed 1930-04-18)"
```
This adds one line to an existing section. No existing content is modified. The edit is additive and verifiable. Easily reverted by any editor.

*Stage 4c — Inline citation* (small content addition, mainspace)  
After Stage 4b is live and unreverted (give it 48 hours), add one sentence to the Chicago Pneumatic History section citing the 1930 trademark filing. Example: "The CP monogram design trademark (USPTO Serial No. 71299042) was filed on April 18, 1930, covering pneumatic tools, air compressors, and related apparatus.<ref>{{cite web|url=https://tsdr.uspto.gov/#caseNumber=71299042&caseType=SERIAL_NO&searchType=statusSearch|title=TSDR Serial No. 71299042|publisher=United States Patent and Trademark Office}}</ref>" Use `edit_page()` with read-modify-write, show full diff, confirm before submitting.

*Stage 4d — Second article* (deferred)  
After Stages 4a–4c complete, identify the next target. Remington Rand or the Soundex article (pending resolution of the owner attribution question: 1927 filer was almost certainly Rand Kardex Corporation or a predecessor, not Remington Rand itself, since the SOUNDEX filing predates the 1927 merger by months).

**Safety principles:**

- Never modify or remove sourced existing content — only add
- All added facts must cite a public primary source (TSDR URL or USPTO patent number)
- Always show and review the unified diff before confirming
- `bot: false` is already set in `api.py` — all edits are attributed to the account, not flagged as automated
- Edit summary must name the primary source (serial number and filing date)
- Minimum 48 hours between Stages 4b and 4c to monitor for reversions
- If any edit is reverted, treat it as a signal to reconsider the content before proceeding

---

### Phase Gate

P1 PASSED when: `markery enhance enhance <serial>` runs to completion without error in an environment with only `pip install -e ".[enhance]"` (no manual realesrgan install), and `model_used` reports `"lanczos-fallback"`.

P2 PASSED when: `markery wikipedia from-essay <essay_path> --serial <serial>` produces valid wikitext without requiring `confirmed.jsonl` to exist, for any project or no project.

P3 PASSED when: `SETUP.md` accurately describes the three dependency tiers and a new contributor can reach each tier by following the documented steps.

P4 PASSED when: Stage 4b (Chicago Pneumatic external link) is live on English Wikipedia and unreverted after 48 hours.

Phase PASSED when P1, P2, P3, and P4 all pass.
