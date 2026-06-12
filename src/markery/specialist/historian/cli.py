"""Historian specialist CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from markery.common.config import DB, DEFAULT_MODEL as _DEFAULT_MODEL
from markery.common.project import Project, require_project
from markery.common.tokens import TokenRecord, count_output_tokens, emit as emit_tokens

# ---------------------------------------------------------------------------
# Inference system prompts
# Identity loaded at module init; task suffixes appended to grow the prefix.
# NOTE: the cacheable-prefix minimum is model-dependent — Haiku 4.5 (the
# default) requires 4096 tokens, not 1024. These ~2K-token prompts are below
# that threshold, so prompt caching does NOT activate on the default model.
# See common/llm.py for the per-model table.
# ---------------------------------------------------------------------------

_PERSONA_DIR = Path(__file__).parent / "persona"
_HISTORIAN_IDENTITY: str = (
    (_PERSONA_DIR / "identity.md").read_text(encoding="utf-8")
    if (_PERSONA_DIR / "identity.md").exists() else ""
)

_CARD_TASK = """\
---

## Assessment Task: Confirm or Reject a Patent-Trademark Pair

You will be given a compact candidate card. Assess whether the pair represents a genuine \
historical correspondence — that a specific patent describes the technical invention \
underlying the trademarked product.

A genuine correspondence requires all four criteria to be satisfied:

**1. Date alignment.** The trademark filing date should follow the patent grant date, \
typically within five years. A negative date gap (trademark predates patent) is a \
strong signal against confirmation unless the entity had continuous prior use. A gap \
of zero days to two years is the strongest positive signal.

**2. Entity continuity.** The assignee named in the patent and the owner named in the \
trademark filing should be the same legal entity or a documented successor. Name variants \
(abbreviations, "& Co." vs. "Company") are acceptable when the entity is clearly the same \
organisation. A gap in entity continuity — different companies, no documented acquisition — \
is disqualifying unless other evidence compensates.

**3. Goods-claims match.** The trademark's goods description (the "G&S" field) should \
plausibly cover the product the patent describes. CPC class alone is insufficient — \
a patent in class H01J (vacuum tubes) paired with a trademark for "office furniture" \
fails this test. Where goods descriptions are absent or truncated, rely on the patent title \
and CPC class to assess plausibility.

**4. Historical defensibility.** The correspondence must be explicable as deliberate \
commercial strategy, not coincidental proximity. A company routinely filed trademarks \
for products enabled by their patent portfolio; a pair is defensible when that logic \
applies. Pairs that are coincidental — same assignee, adjacent dates, unrelated goods — \
should be rejected or deferred.

**Scoring:**
- 5 — all four criteria clearly met; strong historical case
- 4 — three criteria met; one minor gap that doesn't undermine the case
- 3 — two criteria met or significant uncertainty on one key criterion; defer for review
- 2 — only one criterion met; likely reject but warrants a second look
- 1 — two or more criteria clearly fail; reject

Respond with exactly this format and no other text:
RECOMMENDATION: confirm | reject | defer
SCORE: <integer 1–5>
REASONING: <one to three sentences citing specific evidence from the card>\
"""

_DIGEST_TASK = """\
---

## Prioritisation Task: Rank the Next-Review Candidates

You have been shown a project digest summarising the current state of a patent-trademark \
matching queue. Your task is to identify which unreviewed candidates are most worth \
examining first and explain why.

Prioritisation criteria, in descending weight:

1. **Signal strength.** Candidates with title_hit (T) or abstract_hit (A) in the signals \
field have name-level evidence of correspondence — these are higher-priority than \
signal-free candidates at the same score.

2. **Score and date gap.** Higher scores indicate stronger temporal and entity alignment. \
Within the same score band, prefer candidates with smaller date gaps (patent grant to \
trademark filing).

3. **Entity diversity.** Reviewing candidates from multiple entities in one session gives \
a broader picture of the project. If the top candidates all belong to the same entity, \
note which other entities have high-scoring candidates worth including.

4. **Research question fit.** If you can infer the project's research question from the \
trademark names and entity list, flag candidates that seem most directly relevant — even \
if their score is not the absolute highest.

Rank the top three candidates. For each, give one sentence explaining why it is a priority.\
"""

_DRAFT_TASK = """\
---

## Essay Drafting Task

You will be given a match essay scaffold — a Markdown file with YAML frontmatter and \
section headers, but with placeholder comments (<!-- ... -->) in place of prose. \
Your task is to replace those placeholders with analytical prose grounded in the evidence \
already present in the scaffold.

Drafting rules:

- **Preserve the YAML frontmatter exactly.** Do not change any field values, add fields, \
or reformat the block. The frontmatter is a data record; altering it breaks downstream \
validation.

- **Preserve the ## Primary Sources section exactly.** The primary sources section lists \
the specific USPTO and patent records; it must not be changed.

- **Replace each placeholder with 2–4 sentences of prose.** Each section has a comment \
indicating what it should cover. Write to that specification without expanding scope.

- **The trademark filing date must appear in the essay body.** The year-month from \
tm_filing_dt in the frontmatter (e.g. "1931-11") must appear somewhere in the written prose. \
This is a validation requirement.

- **Do not invent identifiers.** Every serial number, patent number, date, and assignee \
name in the prose must come directly from the scaffold. Do not introduce identifiers not \
present in the scaffold, even if you believe them to be accurate.

- **Write in specialist register.** Evidence-forward, primary-source grounded, hedged \
where the record is incomplete. Do not write in general-reader register for match essays.

- **Do not reference the tool or methodology.** Do not mention DuckDB, Markery, \
candidates.jsonl, or any internal tooling. Present the evidence as historical analysis.

Output only the complete essay markdown, starting with the opening ---\
"""

_CARD_INFER_SYSTEM  = (_HISTORIAN_IDENTITY + "\n\n" + _CARD_TASK).strip()
_DIGEST_INFER_SYSTEM = (_HISTORIAN_IDENTITY + "\n\n" + _DIGEST_TASK).strip()
_DRAFT_SYSTEM       = (_HISTORIAN_IDENTITY + "\n\n" + _DRAFT_TASK).strip()


def _parse_infer_result(text: str) -> dict:
    rec_m   = re.search(r'^RECOMMENDATION:\s*(confirm|reject|defer)', text,
                        re.IGNORECASE | re.MULTILINE)
    score_m = re.search(r'^SCORE:\s*([1-5])', text,
                        re.IGNORECASE | re.MULTILINE)
    reason_m = re.search(r'^REASONING:\s*(.+?)(?=\n[A-Z]+:|$)', text,
                         re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return {
        "recommendation": rec_m.group(1).lower() if rec_m else "defer",
        "score":          int(score_m.group(1)) if score_m else 3,
        "reasoning":      reason_m.group(1).strip() if reason_m else text.strip(),
    }


def _context_budget() -> int:
    """Return MARKERY_CONTEXT_BUDGET as int, or 0 (unlimited) if unset."""
    raw = os.environ.get("MARKERY_CONTEXT_BUDGET", "").strip()
    try:
        return max(0, int(raw)) if raw else 0
    except ValueError:
        return 0


def _est_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 0.75))


def _parse_slug(slug: str) -> tuple[str, str]:
    """Return (trademark_slug, patent_no) from a slug like 'soundex-us1261167a'."""
    m = re.match(r'^(.+)-(us\d+[a-z]+)$', slug.lower())
    if not m:
        print(f"Cannot parse slug '{slug}'. Expected format: <trademark>-<patent_no>", file=sys.stderr)
        sys.exit(1)
    tm_slug  = m.group(1)
    pat_no   = m.group(2).upper()
    return tm_slug, pat_no


def _slug_matches_trademark(slug: str, trademark: str | None) -> bool:
    if trademark is None:
        return slug == "figurative"
    normalised = re.sub(r'[^a-z0-9]+', '-', trademark.lower()).strip('-')
    return slug == normalised or slug in normalised


def cmd_card(args: argparse.Namespace) -> None:
    import duckdb

    t0 = time.monotonic()
    proj     = require_project(args.project)
    tm_slug, pat_no = _parse_slug(args.slug)

    if not proj.candidates.exists():
        print(f"No candidates.jsonl found for project '{args.project}'.", file=sys.stderr)
        sys.exit(1)

    # Find candidate record
    cand = None
    for line in proj.candidates.read_text().splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        if c["patent_no"].upper() == pat_no and _slug_matches_trademark(tm_slug, c["trademark"]):
            cand = c
            break
    if cand is None:
        print(f"No candidate found matching slug '{args.slug}' in {proj.candidates}.", file=sys.stderr)
        sys.exit(1)

    serial_no = str(cand["trademark_serial"])

    # Pull goods description
    conn_tm = duckdb.connect(str(DB["trademarks"]), read_only=True)
    goods_rows = conn_tm.execute(
        "SELECT statement_text FROM statement WHERE serial_no = ? AND statement_type_cd LIKE 'GS%'",
        [int(serial_no)],
    ).fetchall()
    goods_raw  = goods_rows[0][0] if goods_rows else ""
    goods_trunc = (goods_raw[:80] + "…") if len(goods_raw) > 80 else goods_raw

    intl_rows = conn_tm.execute(
        "SELECT intl_class FROM intl_class WHERE serial_no = ?", [int(serial_no)]
    ).fetchall()
    class_count = len(intl_rows)
    conn_tm.close()

    # Pull patent fields
    conn_pat = duckdb.connect(str(DB["patents"]), read_only=True)
    pat_row = conn_pat.execute(
        "SELECT title, abstract, grant_dt, assignee_name FROM patents WHERE patent_no = ?",
        [pat_no],
    ).fetchone()
    conn_pat.close()
    pat_title    = pat_row[0] if pat_row else ""
    pat_abstract = pat_row[1] if pat_row else ""
    pat_grant    = pat_row[2] if pat_row else ""
    pat_assignee = pat_row[3] if pat_row else ""
    abstract_trunc = (pat_abstract[:80] + "…") if pat_abstract and len(pat_abstract) > 80 else (pat_abstract or "")

    # Date gap
    try:
        from datetime import date
        g = date.fromisoformat(str(pat_grant)[:10])
        f = date.fromisoformat(cand["tm_filing_dt"][:10])
        gap_str = f"{(f - g).days / 365.25:.1f}y"
    except Exception:
        gap_str = "?"

    # Signal fields
    signals = {
        "title_hit":    cand.get("title_name_hit", False),
        "abstract_hit": cand.get("abstract_name_hit", False),
        "goods_title":  round(cand.get("goods_title_overlap", 0.0), 3),
        "goods_abs":    round(cand.get("goods_abstract_overlap", 0.0), 3),
    }

    # Essay and figure status
    essay_path = proj.root / "content" / f"{args.slug}.md"
    essay_status = "present" if essay_path.exists() else "absent"

    cards_dir = proj.root / "matches" / "cards"

    # Confirmed status
    confirmed_key = (pat_no, serial_no)
    is_confirmed = False
    if proj.confirmed.exists():
        for line in proj.confirmed.read_text().splitlines():
            if not line.strip():
                continue
            c2 = json.loads(line)
            if c2["patent_no"] == pat_no and str(c2["trademark_serial"]) == serial_no:
                is_confirmed = True
                break

    # Format card
    status_str = 'confirmed' if is_confirmed else 'candidate'
    lines = [
        f"## CARD: {args.slug}  [{status_str}  {cand['score']:.4f}  gap={gap_str}]",
        f"mark:      {cand['trademark']} (serial {serial_no})",
        f"filed:     {cand.get('tm_filing_dt', '?')}",
        f"owner:     {cand.get('tm_owner', '?')}",
        f"goods:     {goods_trunc}" + (f"  [{class_count} class(es)]" if class_count else ""),
        f"entity:    {cand['entity']} (id {cand['entity_id']})",
        f"patent:    {pat_no}",
        f"title:     {pat_title}",
        f"grant:     {pat_grant}",
        f"assignee:  {pat_assignee}",
        f"cpc:       {', '.join(cand.get('cpc_classes', []))}",
        f"abstract:  {abstract_trunc}",
        f"signals:   {'T' if signals['title_hit'] else ''}{'A' if signals['abstract_hit'] else ''}  gt={signals['goods_title']}  ga={signals['goods_abs']}",
        f"essay:     {essay_status}",
    ]
    card_text = "\n".join(lines)

    budget = _context_budget()
    if budget and _est_tokens(card_text) > budget:
        # Trim the most variable fields (abstract, goods) to fit budget
        for i, ln in enumerate(lines):
            if ln.startswith("abstract:") or ln.startswith("goods:"):
                words = ln.split()
                while _est_tokens("\n".join(lines)) > budget and len(words) > 3:
                    words.pop()
                    lines[i] = " ".join(words) + "…"
                if _est_tokens("\n".join(lines)) <= budget:
                    break
        card_text = "\n".join(lines)

    json_mode = getattr(args, "json", False)

    # In --json mode stdout must be a single machine-parseable object, so the
    # human-readable card print/write is suppressed (card_text rides in the JSON).
    if not json_mode:
        if args.out == "-":
            print(card_text)
        else:
            out_path = Path(args.out) if args.out else cards_dir / f"{args.slug}.md"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(card_text + "\n", encoding="utf-8")
            print(f"Card written → {out_path}")

    tokens_flag = getattr(args, "tokens", False)
    if tokens_flag or os.environ.get("MARKERY_TOKEN_LOG"):
        rec = count_output_tokens(card_text)
        rec.wall_ms = int((time.monotonic() - t0) * 1000)
        emit_tokens(rec, specialist="historian", command="card", tokens_flag=tokens_flag)

    if getattr(args, "infer", False) or json_mode:
        import json as _json
        from markery.common.llm import call as llm_call
        model = getattr(args, "model", None) or os.environ.get("MARKERY_MODEL", _DEFAULT_MODEL)
        user_msg = card_text + "\n\nAssess this candidate pair."
        try:
            resp_text, ptok, ctok, cache_read, cache_create = llm_call(
                model, _CARD_INFER_SYSTEM, user_msg, 256)
            result = _parse_infer_result(resp_text)
            if json_mode:
                # Stable subprocess contract (D062): {recommendation, score, reasoning, card_text}.
                print(_json.dumps({
                    "recommendation": result["recommendation"],
                    "score":          result["score"],
                    "reasoning":      result["reasoning"],
                    "card_text":      card_text,
                }))
            else:
                print(f"\n[infer]  recommendation={result['recommendation']}  score={result['score']}")
                print(f"         {result['reasoning']}")
            infer_rec = TokenRecord(
                model=model,
                prompt_tokens=ptok,
                completion_tokens=ctok,
                cache_read_tokens=cache_read,
                cache_creation_tokens=cache_create,
                wall_ms=int((time.monotonic() - t0) * 1000),
            )
            emit_tokens(infer_rec, specialist="historian", command="card.infer",
                        tokens_flag=not json_mode)
        except Exception as exc:
            if json_mode:
                print(_json.dumps({
                    "recommendation": "defer", "score": 3,
                    "reasoning": f"inference error: {exc}", "card_text": card_text,
                }))
            else:
                print(f"\n[infer]  error: {exc}", file=sys.stderr)


def cmd_digest(args: argparse.Namespace) -> None:
    import json as _json
    from datetime import datetime, timezone

    t0 = time.monotonic()
    proj = require_project(args.project)

    lines: list[str] = [f"## DIGEST: {args.project}  [{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M')}Z]", ""]

    # Queue summary
    candidates = []
    if proj.candidates.exists():
        candidates = [_json.loads(l) for l in proj.candidates.read_text().splitlines() if l.strip()]

    confirmed_pairs: list[dict] = []
    if proj.confirmed.exists():
        confirmed_pairs = [_json.loads(l) for l in proj.confirmed.read_text().splitlines() if l.strip()]

    rejected_set: set[tuple] = set()
    if proj.rejected.exists():
        for l in proj.rejected.read_text().splitlines():
            if l.strip():
                r = _json.loads(l)
                rejected_set.add((r["patent_no"], str(r["trademark_serial"])))

    conf_keys = {(c["patent_no"], str(c["trademark_serial"])) for c in confirmed_pairs}
    unreviewed = [
        c for c in candidates
        if (c["patent_no"], str(c["trademark_serial"])) not in conf_keys
        and (c["patent_no"], str(c["trademark_serial"])) not in rejected_set
        and c.get("score", 0) >= args.min_score
    ]

    lines.append(f"queue:  confirmed={len(confirmed_pairs)}  rejected={len(rejected_set)}  unreviewed≥{args.min_score}={len(unreviewed)}  total_candidates={len(candidates)}")

    # Next-review candidates (top by score), capped by MARKERY_CONTEXT_BUDGET
    budget = _context_budget()
    all_sorted = sorted(unreviewed, key=lambda c: -c["score"])[:args.top_n]
    if budget:
        fixed_tokens = _est_tokens("\n".join(lines))
        remaining = budget - fixed_tokens
        top: list[dict] = []
        for c in all_sorted:
            sig = ""
            if c.get("title_name_hit"):    sig += "T"
            if c.get("abstract_name_hit"): sig += "A"
            if c.get("goods_title_overlap", 0) > 0.05: sig += "G"
            tm = c['trademark'] or '(figurative)'
            candidate_line = f"  {c['score']:.3f}  {tm:<28}  {c['patent_no']:<14}  {c['entity']:<20}  sig={sig or '-'}"
            if _est_tokens(candidate_line) > remaining:
                break
            remaining -= _est_tokens(candidate_line)
            top.append(c)
    else:
        top = all_sorted
    if top:
        lines.append("")
        lines.append(f"next_review (top {len(top)}):")
        for c in top:
            sig = ""
            if c.get("title_name_hit"):    sig += "T"
            if c.get("abstract_name_hit"): sig += "A"
            if c.get("goods_title_overlap", 0) > 0.05: sig += "G"
            tm = c['trademark'] or '(figurative)'
            lines.append(f"  {c['score']:.3f}  {tm:<28}  {c['patent_no']:<14}  {c['entity']:<20}  sig={sig or '-'}")

    # Confirmed pairs — summary line only; full list via `markery review`
    cards_dir   = proj.root / "matches" / "cards"
    content_dir = proj.root / "content"
    if confirmed_pairs:
        seen: set[tuple] = set()
        essays_done = cards_done = 0
        for c in confirmed_pairs:
            key = (c["patent_no"], str(c["trademark_serial"]))
            if key in seen:
                continue
            seen.add(key)
            tm_slug = re.sub(r'[^a-z0-9]+', '-', (c["trademark"] or "figurative").lower()).strip('-')
            slug    = f"{tm_slug}-{c['patent_no'].lower()}"
            if (content_dir / f"{slug}.md").exists(): essays_done += 1
            if (cards_dir   / f"{slug}.md").exists(): cards_done  += 1
        n = len(seen)
        lines.append("")
        lines.append(
            f"confirmed_pairs:  {n} total"
            f"  (essays: {essays_done}/{n}"
            f"  cards: {cards_done}/{n})"
        )

    # Enrichment status
    enriched_count = sum(1 for c in candidates if "title_name_hit" in c)
    lines.append("")
    lines.append(f"enrichment:  signals={enriched_count}/{len(candidates)} candidates enriched")

    # Preflight timestamp
    preflight_path = proj.root / "matches" / "preflight.json"
    if preflight_path.exists():
        pf = _json.loads(preflight_path.read_text())
        lines.append(f"preflight:   {pf.get('timestamp', '?')}")
    else:
        lines.append("preflight:   never run")

    digest_text = "\n".join(lines)
    json_mode = getattr(args, "json", False)
    if not json_mode:
        print(digest_text)

    tokens_flag = getattr(args, "tokens", False)
    if tokens_flag or os.environ.get("MARKERY_TOKEN_LOG"):
        rec = count_output_tokens(digest_text)
        rec.wall_ms = int((time.monotonic() - t0) * 1000)
        emit_tokens(rec, specialist="historian", command="digest", tokens_flag=tokens_flag)

    if getattr(args, "infer", False) or json_mode:
        import json as _json
        from markery.common.llm import call as llm_call
        model = getattr(args, "model", None) or os.environ.get("MARKERY_MODEL", _DEFAULT_MODEL)
        user_msg = (
            digest_text
            + "\n\nWhich of the unreviewed candidates listed above are most worth examining "
            "first? Rank the top three and give a one-sentence reason for each."
        )
        try:
            ranked_text, ptok, ctok, cache_read, cache_create = llm_call(
                model, _DIGEST_INFER_SYSTEM, user_msg, 512)
            if json_mode:
                print(_json.dumps({"ranking": ranked_text.strip(), "digest": digest_text}))
            else:
                print("\n" + ranked_text)
            infer_rec = TokenRecord(
                model=model,
                prompt_tokens=ptok,
                completion_tokens=ctok,
                cache_read_tokens=cache_read,
                cache_creation_tokens=cache_create,
                wall_ms=int((time.monotonic() - t0) * 1000),
            )
            emit_tokens(infer_rec, specialist="historian", command="digest.infer",
                        tokens_flag=not json_mode)
        except Exception as exc:
            if json_mode:
                print(_json.dumps({"ranking": "", "digest": digest_text,
                                   "error": str(exc)}))
            else:
                print(f"\n[infer]  error: {exc}", file=sys.stderr)


def cmd_scaffold(args: argparse.Namespace) -> None:
    import duckdb

    t0 = time.monotonic()
    proj = require_project(args.project)
    tm_slug, pat_no = _parse_slug(args.slug)

    # Find in confirmed
    if not proj.confirmed.exists():
        print(f"No confirmed.jsonl found for '{args.project}'.", file=sys.stderr)
        sys.exit(1)

    pair = None
    for line in proj.confirmed.read_text().splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        if c["patent_no"].upper() == pat_no and _slug_matches_trademark(tm_slug, c["trademark"]):
            pair = c
            break
    if pair is None:
        print(f"No confirmed pair matching '{args.slug}' in confirmed.jsonl.", file=sys.stderr)
        sys.exit(1)

    serial_no = str(pair["trademark_serial"])

    # Pull trademark fields
    conn_tm = duckdb.connect(str(DB["trademarks"]), read_only=True)
    goods_rows = conn_tm.execute(
        "SELECT statement_text FROM statement WHERE serial_no = ? AND statement_type_cd LIKE 'GS%'",
        [int(serial_no)],
    ).fetchall()
    goods_raw  = goods_rows[0][0] if goods_rows else ""
    goods_text = (goods_raw[:150] + "…") if len(goods_raw) > 150 else goods_raw
    owner_rows = conn_tm.execute(
        "SELECT own_name FROM owner WHERE serial_no = ? ORDER BY own_type_cd LIMIT 1",
        [int(serial_no)],
    ).fetchall()
    owner_name = owner_rows[0][0] if owner_rows else pair.get("tm_owner", "")
    conn_tm.close()

    # Pull patent fields
    conn_pat = duckdb.connect(str(DB["patents"]), read_only=True)
    pat_row = conn_pat.execute(
        "SELECT title, abstract, grant_dt, assignee_name, app_dt FROM patents WHERE patent_no = ?",
        [pat_no],
    ).fetchone()
    conn_pat.close()
    pat_title    = pat_row[0] if pat_row else ""
    pat_abstract = (pat_row[1] or "")[:150]
    pat_grant    = str(pat_row[2])[:10] if pat_row else ""
    pat_assignee = pat_row[3] if pat_row else ""
    pat_app_dt   = str(pat_row[4])[:10] if pat_row else ""

    # Confirmed records lack filing/reg fields — fall back to candidates.jsonl
    tm_filing = pair.get("tm_filing_dt", "")
    tm_reg    = pair.get("tm_reg_no", "")
    if not tm_filing and proj.candidates.exists():
        for line in proj.candidates.read_text().splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            if c["patent_no"].upper() == pat_no and str(c["trademark_serial"]) == serial_no:
                tm_filing = c.get("tm_filing_dt", "")
                tm_reg    = c.get("tm_reg_no", "")
                break
    tm_filing = tm_filing[:10] if tm_filing else ""
    tm_reg    = tm_reg or ""

    try:
        from datetime import date
        g = date.fromisoformat(pat_grant)
        f = date.fromisoformat(tm_filing)
        gap_str = f"{(f - g).days / 365.25:.1f} years"
    except Exception:
        gap_str = "?"

    content_dir = proj.root / "content"
    content_dir.mkdir(exist_ok=True)
    out_path = content_dir / f"{args.slug}.md"
    if out_path.exists() and not args.force:
        print(f"Essay already exists at {out_path}. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    scaffold = f"""---
title: "{pair['trademark'] or '(figurative)'} — {pat_no}"
trademark_serial: {serial_no}
trademark: "{pair['trademark'] or '(figurative)'}"
tm_filing_dt: "{tm_filing}"
tm_reg_no: "{tm_reg}"
tm_owner: "{owner_name}"
patent_no: "{pat_no}"
patent_grant_dt: "{pat_grant}"
patent_assignee: "{pat_assignee}"
entity: "{pair['entity']}"
date_gap: "{gap_str}"
---

## Primary Sources

- USPTO Trademark Serial No. {serial_no} — [{pair['trademark'] or '(figurative)'}](https://tsdr.uspto.gov/#caseNumber={serial_no}&caseType=SERIAL_NO&searchType=statusSearch)
  - Filed: {tm_filing}  ·  Registered: {tm_reg}  ·  Owner: {owner_name}
  - Goods and services: {goods_text}
- US Patent {pat_no} — [{pat_title}](https://patents.google.com/patent/{pat_no.replace('US','').replace('A','')})
  - Applied: {pat_app_dt}  ·  Granted: {pat_grant}  ·  Assignee: {pat_assignee}

## The Invention

<!-- Summarise what the patent describes. Source: abstract below. Do not invent facts. -->

> {pat_abstract}

## The Mark

<!-- Describe the trademark — its goods/services class, what product it named, how it was marketed. -->

## The Connection

<!-- Explain how this patent underlies the trademarked product. What does the patent enable? -->

## Historical Context

<!-- Place the patent-trademark pair in the industrial and commercial context of the period. -->

## Significance

<!-- Why does this pair matter for the research project? What does it illustrate? -->
"""

    out_path.write_text(scaffold, encoding="utf-8")
    print(f"Scaffold written → {out_path}")

    tokens_flag = getattr(args, "tokens", False)
    if tokens_flag or os.environ.get("MARKERY_TOKEN_LOG"):
        rec = count_output_tokens(scaffold)
        rec.wall_ms = int((time.monotonic() - t0) * 1000)
        emit_tokens(rec, specialist="historian", command="scaffold", tokens_flag=tokens_flag)


def cmd_draft(args: argparse.Namespace) -> None:
    """Call the API to produce a first-draft essay from an existing scaffold."""
    t0 = time.monotonic()
    proj = require_project(args.project)

    scaffold_path = proj.root / "content" / f"{args.slug}.md"
    if not scaffold_path.exists():
        print(
            f"No scaffold at {scaffold_path}.\n"
            f"Run: markery historian scaffold {args.project} {args.slug}",
            file=sys.stderr,
        )
        sys.exit(1)

    scaffold_text = scaffold_path.read_text(encoding="utf-8")
    model = getattr(args, "model", None) or os.environ.get("MARKERY_MODEL", _DEFAULT_MODEL)

    from markery.common.llm import call as llm_call
    print(f"Drafting '{args.slug}' with {model}…", flush=True)
    try:
        draft_text, ptok, ctok, cache_read, cache_create = llm_call(
            model, _DRAFT_SYSTEM, scaffold_text, 2048)
    except RuntimeError as exc:
        print(f"Inference error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Ensure output starts with frontmatter (model may prepend prose)
    if not draft_text.startswith("---"):
        fm_start = draft_text.find("---")
        if fm_start >= 0:
            draft_text = draft_text[fm_start:]
        else:
            print("Warning: draft response does not contain YAML frontmatter.", file=sys.stderr)

    content_dir = proj.root / "content"
    content_dir.mkdir(exist_ok=True)
    draft_path = content_dir / f"{args.slug}-draft.md"
    draft_path.write_text(draft_text, encoding="utf-8")
    print(f"Draft written → {draft_path}")

    wall_ms = int((time.monotonic() - t0) * 1000)
    draft_rec = TokenRecord(
        model=model,
        prompt_tokens=ptok,
        completion_tokens=ctok,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_create,
        wall_ms=wall_ms,
    )
    emit_tokens(draft_rec, specialist="historian", command="draft", tokens_flag=True)

    # Validate the draft immediately
    print("Validating draft…")
    val_args = argparse.Namespace(project=args.project, slug=args.slug, essay=str(draft_path))
    try:
        cmd_validate(val_args)
    except SystemExit as exc:
        if exc.code and exc.code != 0:
            sys.exit(exc.code)


def _candidate_slug(c: dict) -> str:
    """Derive the canonical slug for a candidate record."""
    tm = (c.get("trademark") or "figurative")
    tm_slug = re.sub(r"[^a-z0-9]+", "-", tm.lower()).strip("-")
    return f"{tm_slug}-{c['patent_no'].lower()}"


def cmd_infer_queue(args: argparse.Namespace) -> None:
    """Batch `card --infer` across all unreviewed candidates via the Batch API (50%).

    Generates each card deterministically through `markery historian card` (no API),
    then submits all inference requests as one batch. Prints a recommendation table
    and logs aggregated token usage (flagged batch=True so `tokens report` halves it).
    """
    import json as _json
    import subprocess

    proj = require_project(args.project)
    if not proj.candidates.exists():
        print(f"No candidates.jsonl for {args.project}.", file=sys.stderr)
        sys.exit(1)

    candidates = [_json.loads(l) for l in proj.candidates.read_text().splitlines() if l.strip()]
    confirmed = set()
    if proj.confirmed.exists():
        for l in proj.confirmed.read_text().splitlines():
            if l.strip():
                c = _json.loads(l)
                confirmed.add((c["patent_no"], str(c["trademark_serial"])))
    rejected = set()
    if proj.rejected.exists():
        for l in proj.rejected.read_text().splitlines():
            if l.strip():
                c = _json.loads(l)
                rejected.add((c.get("patent_no"), str(c.get("trademark_serial"))))

    # Unreviewed, de-duplicated by slug, optionally score-filtered.
    seen: set[str] = set()
    queue: list[tuple[str, dict]] = []
    for c in candidates:
        key = (c["patent_no"], str(c["trademark_serial"]))
        if key in confirmed or key in rejected:
            continue
        if c.get("score", 0) < args.min_score:
            continue
        slug = _candidate_slug(c)
        if slug in seen:
            continue
        seen.add(slug)
        queue.append((slug, c))

    if not queue:
        print("No unreviewed candidates above the score threshold.")
        return

    print(f"Generating {len(queue)} cards…", flush=True)
    items: list[tuple[str, str]] = []
    for slug, _c in queue:
        cp = subprocess.run(
            ["markery", "historian", "card", args.project, slug, "--out", "-"],
            capture_output=True, text=True,
        )
        if cp.returncode != 0:
            print(f"  card failed for {slug}: {cp.stderr[:120]}", file=sys.stderr)
            continue
        items.append((slug, cp.stdout.strip() + "\n\nAssess this candidate pair."))

    model = getattr(args, "model", None) or os.environ.get("MARKERY_MODEL", _DEFAULT_MODEL)
    from markery.common.llm import call_batch
    print(f"Submitting {len(items)} inferences as one batch ({model}, 50% price)…", flush=True)
    t0 = time.monotonic()
    results = call_batch(model, _CARD_INFER_SYSTEM, items, max_tokens=256)

    tp = tc = tcr = tcc = 0
    rows: list[tuple[str, str, int]] = []
    for slug, _c in queue:
        r = results.get(slug)
        if not r or "error" in r:
            rows.append((slug, "error", 0))
            continue
        parsed = _parse_infer_result(r["text"])
        rows.append((slug, parsed["recommendation"], parsed["score"]))
        tp += r["prompt_tokens"]; tc += r["completion_tokens"]
        tcr += r["cache_read_tokens"]; tcc += r["cache_creation_tokens"]

    print(f"\n{'slug':<42}{'recommendation':<14}score")
    for slug, rec, score in rows:
        print(f"{slug:<42}{rec:<14}{score}")

    if tp or os.environ.get("MARKERY_TOKEN_LOG"):
        rec = TokenRecord(
            model=model, prompt_tokens=tp, completion_tokens=tc,
            cache_read_tokens=tcr, cache_creation_tokens=tcc,
            wall_ms=int((time.monotonic() - t0) * 1000), batch=True,
        )
        emit_tokens(rec, specialist="historian", command="infer-queue",
                    tokens_flag=True, n_calls=len(items))


def cmd_validate(args: argparse.Namespace) -> None:
    import duckdb
    import re as _re

    proj = require_project(args.project)
    essay_path = Path(args.essay) if args.essay else proj.root / "content" / f"{args.slug}.md"

    if not essay_path.exists():
        print(f"Essay not found: {essay_path}", file=sys.stderr)
        sys.exit(1)

    text = essay_path.read_text(encoding="utf-8")
    results: list[tuple[str, bool, str]] = []  # (check_name, passed, detail)

    def check(name: str, passed: bool, detail: str = "") -> None:
        results.append((name, passed, detail))

    # Extract frontmatter
    fm: dict = {}
    fm_match = re.match(r'^---\n(.+?)\n---', text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ':' in line:
                k, _, v = line.partition(':')
                fm[k.strip()] = v.strip().strip('"')

    serial_no = fm.get("trademark_serial", "")
    patent_no = fm.get("patent_no", "").upper()

    # Check 0a: title present
    check("title_present", bool(fm.get("title", "")),
          "title missing from frontmatter" if not fm.get("title") else "")

    # Check 0b: trademark present
    check("trademark_present", bool(fm.get("trademark", "")),
          "trademark missing from frontmatter" if not fm.get("trademark") else "")

    # Check 1: serial resolves
    if serial_no:
        conn_tm = duckdb.connect(str(DB["trademarks"]), read_only=True)
        row = conn_tm.execute(
            "SELECT serial_no FROM case_file WHERE serial_no = ?", [int(serial_no)]
        ).fetchone()
        conn_tm.close()
        check("serial_resolves", row is not None, f"serial_no={serial_no}")
    else:
        check("serial_resolves", False, "trademark_serial missing from frontmatter")

    # Check 2: patent resolves
    if patent_no:
        conn_pat = duckdb.connect(str(DB["patents"]), read_only=True)
        pat_row = conn_pat.execute(
            "SELECT patent_no, grant_dt, assignee_name FROM patents WHERE patent_no = ?", [patent_no]
        ).fetchone()
        conn_pat.close()
        check("patent_resolves", pat_row is not None, f"patent_no={patent_no}")
    else:
        check("patent_resolves", False, "patent_no missing from frontmatter")

    # Check 3: grant date matches DB
    if patent_no and pat_row:
        db_grant = str(pat_row[1])[:10]
        fm_grant = fm.get("patent_grant_dt", "")[:10]
        check("grant_date_matches", db_grant == fm_grant,
              f"frontmatter={fm_grant!r}  db={db_grant!r}")

    # Check 4: filing date present in frontmatter and appears in essay body
    fm_filing = fm.get("tm_filing_dt", "")
    if fm_filing:
        filing_in_body = fm_filing[:7] in text  # year-month must appear in body
        check("filing_date_in_body", filing_in_body,
              f"filing {fm_filing!r} not found in essay body")
    else:
        check("filing_date_in_body", False, "tm_filing_dt missing from frontmatter")

    # Check 5: entity variant recognised
    entity_name = fm.get("entity", "")
    if entity_name:
        import duckdb as _duck
        conn_ent = _duck.connect(str(DB["entities"]), read_only=True)
        row_ent = conn_ent.execute(
            "SELECT 1 FROM company_entity WHERE canonical_name = ? "
            "UNION SELECT 1 FROM entity_name_variant WHERE variant_name = ?",
            [entity_name, entity_name],
        ).fetchone()
        conn_ent.close()
        check("entity_recognised", row_ent is not None, f"entity={entity_name!r}")
    else:
        check("entity_recognised", False, "entity missing from frontmatter")

    # Check 6: no cross-pair contamination (no other serial numbers appear in body)
    other_serials = _re.findall(r'\b7[01]\d{6}\b', text)
    own_serial    = str(serial_no)
    alien         = [s for s in other_serials if s != own_serial]
    check("no_cross_contamination", len(alien) == 0,
          f"found alien serial(s): {alien}" if alien else "")

    # Report
    all_passed = all(p for _, p, _ in results)
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        suffix = f"  ({detail})" if detail and not passed else ""
        print(f"  {status}  {name}{suffix}")

    print(f"\n{'All checks passed.' if all_passed else 'Validation FAILED.'}")
    if not all_passed:
        sys.exit(1)


def historian_main() -> None:
    parser = argparse.ArgumentParser(
        prog="markery historian",
        description="Historian specialist commands",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    prep = sub.add_parser("prepare", help="Generate BRIEF.md for a project session")
    prep.add_argument("project", help="Project name (directory under projects/)")
    prep.add_argument(
        "--min-score", type=float, default=0.5, metavar="SCORE",
        help="Minimum candidate score to count as unreviewed (default: 0.5)",
    )

    card_p = sub.add_parser("card", help="Generate compact candidate card (~250 tokens)")
    card_p.add_argument("project", help="Project name")
    card_p.add_argument("slug",    help="Candidate slug, e.g. soundex-us1261167a")
    card_p.add_argument("--out",   default=None, metavar="PATH",
                        help="Output path (default: matches/cards/<slug>.md); use '-' for stdout")
    card_p.add_argument("--tokens", action="store_true",
                        help="Print token count of card output to stderr")
    card_p.add_argument("--infer", action="store_true",
                        help="Call the API for a confirm/reject/defer recommendation")
    card_p.add_argument("--json", action="store_true",
                        help="Emit a single JSON object {recommendation, score, reasoning, card_text} "
                             "(implies --infer; for the langgraph subprocess contract)")
    card_p.add_argument("--model", default=None, metavar="MODEL",
                        help="Override MARKERY_MODEL for this --infer call")

    digest_p = sub.add_parser("digest", help="Project state summary (~800-1200 tokens)")
    digest_p.add_argument("project", help="Project name")
    digest_p.add_argument("--min-score", type=float, default=0.5, dest="min_score",
                          help="Min score for unreviewed count (default: 0.5)")
    digest_p.add_argument("--top", type=int, default=5, dest="top_n",
                          help="Number of next-review candidates to list (default: 5)")
    digest_p.add_argument("--tokens", action="store_true",
                          help="Print token count of digest output to stderr")
    digest_p.add_argument("--infer", action="store_true",
                          help="Call the API for ranked candidate prioritization")
    digest_p.add_argument("--json", action="store_true",
                          help="Emit the ranked prioritization as JSON {ranking} (implies --infer)")
    digest_p.add_argument("--model", default=None, metavar="MODEL",
                          help="Override MARKERY_MODEL for this --infer call")

    draft_p = sub.add_parser("draft", help="Generate first-draft essay from scaffold via API")
    draft_p.add_argument("project", help="Project name")
    draft_p.add_argument("slug",    help="Confirmed pair slug, e.g. sterilamp-us2168861a")
    draft_p.add_argument("--model", default=None, metavar="MODEL",
                         help="Override MARKERY_MODEL for this call")

    scaffold_p = sub.add_parser("scaffold", help="Generate essay skeleton for a confirmed pair")
    scaffold_p.add_argument("project", help="Project name")
    scaffold_p.add_argument("slug",    help="Confirmed pair slug, e.g. soundex-us1261167a")
    scaffold_p.add_argument("--force", action="store_true",
                            help="Overwrite existing essay file")
    scaffold_p.add_argument("--tokens", action="store_true",
                            help="Print token count of scaffold output to stderr")

    validate_p = sub.add_parser("validate", help="Validate essay against DB records")
    validate_p.add_argument("project", help="Project name")
    validate_p.add_argument("slug",    nargs="?", default=None,
                            help="Pair slug (derives essay path if --essay not given)")
    validate_p.add_argument("--essay", metavar="PATH", default=None,
                            help="Explicit path to essay file")

    iq_p = sub.add_parser("infer-queue",
                          help="Batch card --infer over all unreviewed candidates (Batch API, 50%)")
    iq_p.add_argument("project", help="Project name")
    iq_p.add_argument("--min-score", type=float, default=0.0, dest="min_score", metavar="S",
                      help="Only infer candidates with score ≥ S (default: 0.0)")
    iq_p.add_argument("--model", default=None, metavar="MODEL",
                      help="Override MARKERY_MODEL for this batch")

    args = parser.parse_args()

    if args.action == "prepare":
        from markery.specialist.historian.prepare import prepare
        prepare(args.project, min_score=args.min_score)
    elif args.action == "card":
        cmd_card(args)
    elif args.action == "digest":
        cmd_digest(args)
    elif args.action == "draft":
        cmd_draft(args)
    elif args.action == "scaffold":
        cmd_scaffold(args)
    elif args.action == "validate":
        cmd_validate(args)
    elif args.action == "infer-queue":
        cmd_infer_queue(args)
