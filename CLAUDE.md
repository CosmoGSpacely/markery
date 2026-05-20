# Markery — Project Contract

This file governs all Claude Code sessions in this repository. It is automatically loaded and applies to every agent working here.

---

## Work Classification

Every piece of work belongs to one of three tiers. Classify before acting; place results in the right tier.

| Tier | What it covers | Canonical paths |
|---|---|---|
| **Markery** | Shared infrastructure: CLI, databases, tests, top-level docs | `src/markery/` (excluding specialist subdirs), `tests/`, `CLAUDE.md`, `CONTEXT.md`, `DESIGN.md`, `SETUP.md`, `README.md`, `ROADMAP.md`, `DEFERRED.md`, `STATUS.md`, `archive/` |
| **Specialist** | One agent's domain: Python modules, CLI commands, persona files | `src/markery/specialist/<name>/` — each specialist owns its subtree exclusively |
| **Project** | One research project's artifacts: entities, matches, content, site | `projects/<name>/` |

A single task may touch multiple tiers. Classify each change independently.

---

## Work Routing

**When work surfaces, route it before acting.**

**ROADMAP.md** — Active phases currently in flight. Add work here when:
- It has a defined sequence of actions and a phase gate
- It is the current priority and work is imminent or in progress

**DEFERRED.md** — Known work that is not the current priority. Add an entry here when:
- Work surfaces that is out of scope for the current phase
- Work is blocked by an external condition (quota, dependency, design decision)
- Work is explicitly postponed with a named reopen trigger

Every DEFERRED entry requires: a unique ID (`Dnnn`), a one-line description, and an explicit reopen trigger. No entry without a trigger.

**ROADMAP phase completion format:**
- Append `— CLOSED` to the phase heading: `### P3 — Description — CLOSED`
- Append `— PASSED` to the phase gate line when all criteria are met
- Do not use strikethrough markup (`~~`) in ROADMAP — it obscures content for future reference
- Body text is preserved as written; only the heading status tag changes

When a full ROADMAP is complete, archive it to `archive/ROADMAP-<date>.md` and remove it from `ROADMAP.md`.

---

## Review File Convention

A REVIEW file is an ad-hoc cross-cutting analysis document. It is not permanent documentation.

- Create `<NAME>-REVIEW.md` at repo root when beginning a structured audit or analysis
- Work from it during the analysis; record findings and decisions in it
- When complete: copy to `archive/<NAME>-REVIEW-<date>.md`, then `git rm <NAME>-REVIEW.md`
- Never leave a REVIEW file at root after its analysis is complete

---

## Specialist Boundary Enforcement

Each specialist owns its subtree exclusively. Before writing any file, verify it falls within the active specialist's Scope (see `## Scope` in each specialist's `identity.md`). If a task requires writing outside scope, stop — create or update a DEFERRED entry and halt.

Specialist identity files:
- PATENT: `src/markery/specialist/patent/persona/identity.md`
- TRADEMARK: `src/markery/specialist/trademark/persona/identity.md`
- MATCHMAKER: `src/markery/specialist/matchmaker/persona/identity.md`
- HISTORIAN: `src/markery/specialist/historian/persona/identity.md`
- PUBLISHER: `src/markery/specialist/publisher/persona/identity.md`

---

## Constraints

- **Never commit `.env`** — contains `EPO_CONSUMER_KEY`, `EPO_CONSUMER_SECRET`, `USPTO_API_KEY`; gitignored
- **No Claude attribution in commits** — do not add `Co-Authored-By` or any model credit line to commit messages
- **Classify before acting** — tier, paths, scope; then act
