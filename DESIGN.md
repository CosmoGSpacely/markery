# Design Decisions

Engineering rationale for the Markery architecture. This document covers the technical choices and the tradeoffs made consciously.

---

## Why DuckDB

DuckDB is a column-oriented analytical database optimized for read-heavy aggregation workloads — exactly the query pattern of historical research. The typical research query is a range scan across filing dates, a GROUP BY on owner name, or a cross-join between two sets of records. DuckDB handles these faster than SQLite and without the operational overhead of Postgres.

The decisive feature for this project is the single-file format. Each database is a single `.duckdb` file committed to the repository. The three database files together are ~25 MB — small enough to commit, portable across machines, and shareable as complete artifacts. No server, no connection pooling, no migration scripts. A researcher cloning the repo immediately has access to the full dataset.

The Python API returns results directly as Python objects or Pandas DataFrames, and DuckDB's `ATTACH` feature enables cross-database queries without copying data. Both are important for a project where data exploration happens in notebooks and ad-hoc scripts as much as in formal pipelines.

**Alternative considered:** SQLite. Row-oriented, slower for analytical aggregations, no `ATTACH` for cross-database joins. Rejected.

---

## Why Three Databases

Each database has an independent source and independent rebuild path:

- `trademarks.duckdb` — built from the USPTO bulk CSV download (2011 snapshot) or incrementally via the TSDR API; the two routes are not mutually exclusive
- `patents.duckdb` — built by querying the EPO OPS API, class by class, year by year
- `entities.duckdb` — populated from per-project CSV files (`entities.csv`, `variants.csv`)

Separation means a database can be rebuilt, extended, or replaced without touching the others. Adding new CPC classes to `patents.duckdb` does not require dropping or reloading trademark data. Changing the entity registry does not invalidate either primary source.

DuckDB's `ATTACH` makes cross-database joins as syntactically simple as single-database joins — there is no duplication penalty for keeping them separate. The entity registry exists specifically as a cross-reference hub: it holds no primary source data, only the mappings between name variants in the other two databases. Merging it into either primary database would couple two independently-sourced datasets.

**Alternative considered:** One database with all tables. Rejected because a schema change or rebuild in one source would ripple across all data, and the mixed-provenance schema would be harder to reason about.

---

## Why Human Curation, Not Automated Confirmation

The intellectual claim in a confirmed patent-trademark pair — that a specific patent describes the invention underlying a specific product name — is a historical judgment, not an algorithmic one.

A high scoring pair might still be wrong: a company could have filed a trademark for a product line that predated the patent, or scored 0.80 because the dates align without any product correspondence. A low-scoring pair might still be right: the SOUNDEX trademark predates the Odell patent by five years, but the pair is clearly valid.

The error asymmetry is also lopsided. A false positive in `confirmed.jsonl` corrupts the scholarly record; a false negative means a pair is simply unrecognized until someone notices it. Given this, human review before confirmation is not a workflow convenience — it is the appropriate epistemic standard for a research tool making historical claims.

`candidates.jsonl` is generated automatically and is never edited. `confirmed.jsonl` is curated by hand and is what the research essays are built from.

---

## The Scoring Formula

Two additive components, max 0.80:

**Temporal score (max 0.5):** Patent grant date precedes trademark filing date → positive, tapering from 0.5 at zero gap to 0.0 at 20 years. Trademark filed before patent grant → slight negative (max −0.4), which is not disqualifying — brand names often preceded specific patents. The 20-year taper is intentional: a 15-year gap is less compelling evidence than a 2-year gap, but should not score zero.

**Classification score (0.3, binary):** Fires when any of the patent's CPC classes falls in the project's product signal set. Binary rather than graded because the CPC classifications for pre-1940 patents were applied retroactively by algorithmic mapping — fine-grained subgroup precision is not reliable enough to justify a graded signal. Which classes constitute the signal set is defined by the project, not by the tool.

The model scores candidate identification, not confirmation. The 0.80 ceiling is intentional: a perfect score would imply a certainty the model cannot deliver.

---

## Tradeoffs Made Consciously

**Image blobs in DuckDB.** Mark images are stored as BLOBs in `mark_images` rather than as files on disk. This keeps the database self-contained and portable, but means the `.duckdb` file grows when images are added and must be committed in full. Acceptable at the current scale (~96 images); would need reconsideration at thousands.

**ATTACH over materialized joins.** Cross-database queries via `ATTACH` require all three database files to be present. For a project where all three are committed to the repository, this is fine. In a distributed or multi-user context it would require rethinking.

**Additive scoring over interaction terms.** The linear additive model is interpretable and easy to explain. It misses interaction effects (a close temporal match plus a matching CPC class should probably score higher than the sum of independent components). Kept simple intentionally — the model's purpose is candidate ranking, not probabilistic confirmation.

---

## Specialist Ownership Pattern

The codebase is organized into five specialists under `src/markery/specialist/`. Each specialist owns exactly one data source and all functionality that reads from or writes to it.

| Specialist | Owns | CLI entry point |
|---|---|---|
| `patent/` | `data/patents.duckdb` | `markery patent` |
| `trademark/` | `data/trademarks.duckdb` | `markery trademark` |
| `matchmaker/` | `data/entities.duckdb` | `markery match / matchmaker` |
| `historian/` | `confirmed.jsonl`, `rejected.jsonl`, interactive review | `markery review / status` |
| `publisher/` | Site output, image enhancement | `markery site / enhance / publisher` |
| `librarian/` | `library/` — secondary literature corpus and embedding index | `markery librarian` |

A specialist exposes three layers: a **queries module** (pure DB reads, no side effects), a **build/pipeline module** (writes or transforms), and a **CLI module** (entry point). Cross-specialist reads use DuckDB `ATTACH` where a join cannot be expressed through individual specialist APIs without multiple round trips — this is the only permitted cross-specialist coupling.

Each specialist also owns a **`persona/` directory** containing its agent contract: `README.md` (purpose and commands), `identity.md` (role, capabilities, explicit limits), `instructions/` (operation-specific instruction cards), and `reference/` (domain reference material). This structure is uniform across all five specialists — acquisition agents and editorial agents alike.

---

## Projects as Independent Research Units

Research projects live under `projects/<name>/` and are entirely independent of each other. A project contains only:
- Configuration (`entities.txt`) — which entity IDs are in scope
- Curated data (`matches/confirmed.jsonl`) — hand-reviewed pairs
- Content (`content/`) — research essays and narrative pages

Everything else — candidates, site output, enhanced images — is generated from these three inputs and is gitignored. Any project can be rebuilt from scratch by running `markery match`, reviewing, and `markery site build`.

Projects do not share confirmed pairs, entities, or content. The same entity (e.g. Remington Rand) can appear in multiple projects with independent confirmation decisions in each.

---

## Agentic Architecture

Markery is an agentic tool, not a pipeline. The specialist pattern is the structural expression of that: five bounded agents, each with its own data domain and API, coordinated by an orchestrator. An agent calling `markery patent build` or `markery match generate` is making the same call a human makes at the terminal — the CLI is the agent interface and the human interface simultaneously.

Each specialist exposes three surfaces:

1. **CLI** — the human interface. Every operation is a named subcommand with documented arguments.
2. **Queries module** — the programmatic interface. Pure functions, typed inputs and outputs, no CLI dependency. A model calling `get_confirmed_matches()` gets the same result as the site builder, without going through the CLI.
3. **`persona/` directory** — the agent-as-collaborator interface. A structured set of documents that define the specialist's identity, scope, capabilities, and explicit limits. Loaded into a Claude project, the persona turns a model into that specialist without requiring knowledge of the codebase.

The three surfaces serve different callers but describe the same agent. This is why the persona format is uniform across all five specialists — `README.md`, `identity.md`, `instructions/`, `reference/` — even for purely mechanical acquisition agents like PATENT and TRADEMARK. A data-acquisition agent still has a defined scope (what classes, what years, what rate limits), still has explicit limits (what it will not do), and still benefits from instruction cards for its key operations.

The `identity.md` file in each persona is particularly important: it states what the agent does *not* do as explicitly as what it does. These limits prevent a model operating as the Patent specialist from making research judgments it is not equipped to make, and prevent the Historian from attempting database operations that belong to another specialist.

The session-level enforcement of these boundaries is handled by two mechanisms: `CLAUDE.md` at the repository root defines the work classification tiers (Markery, Specialist, Project), routing rules to `ROADMAP.md` and `DEFERRED.md`, and the review file lifecycle; and the `## Scope` section in each specialist's `identity.md` enumerates owned reads, owned writes, and forbidden paths. Together these make the agentic contract explicit enough to route new work automatically and prevent cross-specialist writes without human intervention.

---

## Model-Agnosticism by Design

Markery classifies each workflow task along two dimensions: **context dependency** — how much correct completion relies on knowledge the model must supply from training versus knowledge provided explicitly in the prompt — and **output structure** — how constrained the expected output is.

Tasks with low context dependency and structured output are model-agnostic by construction: all necessary facts arrive in the prompt, and correctness can be verified by code. Tasks with high context dependency and open prose output are irreducibly model-sensitive: they require domain knowledge that cannot be fully supplied as structured input, and quality requires judgment to assess. Everything between is a design choice.

Three principles move tasks toward the model-agnostic quadrant:

**Bring Your Own Knowledge.** Never ask a model to recall domain facts; provide all facts as structured inputs. The model's role is transformation — arrange, judge, narrate — not retrieval. When a scaffold supplies every serial number, date, and goods description, a model with no prior knowledge of 1930s industrial history produces the same factual accuracy as one trained on it.

**Checkable Outputs.** Design task outputs so correctness can be verified by code rather than by a human or a stronger model. If a validator can be written for the output, the task is structurally model-agnostic. This is why `validate` is not only a token-reduction device: it converts "was this essay accurate?" from a model-sensitive judgment into a deterministic check. Any model whose output passes the validator is producing correct factual content.

**Progressive Commitment.** Break complex tasks into stages where each stage's output is validated before the next begins. This converts a single complex model-sensitive task into a sequence of simpler model-agnostic steps, each with a defined minimum viable output (MVO) that code can check before the next stage starts.

**Minimum viable output (MVO):** For each task, the minimum output that downstream code would accept without error or that a downstream tool would act on correctly. If the MVO can be fully specified and checked by code, the task is model-agnostic in principle — testing reduces to whether a given model can produce valid-format output, a low bar. If assessing the MVO requires a human or a stronger model, the task is inherently model-sensitive regardless of prompt design.

| Task | MVO checkable by code? | Tier |
|---|---|---|
| Auto-disposition | — entirely deterministic; no model involved | Model-agnostic |
| Y/N candidate review | Yes — decision is Y, N, or UNCERTAIN with required fields | Model-agnostic |
| Factual essay sections | Yes — serial numbers, dates, patent numbers resolve against DB | Model-agnostic |
| Entity variant suggestion | Yes — output strings are present in the source DB tables | Model-agnostic |
| Narrative essay paragraphs | No — quality requires judgment | Model-sensitive |
| Wikipedia policy compliance | No — NPOV, notability require interpretation | Model-sensitive |
| Historical significance analysis | No — interpretive; no ground truth | Model-sensitive |

The Phase 11 token-reduction tools operationalize all three principles simultaneously. `scaffold` removes context dependency by pre-filling factual sections from DB records. `card` provides structured fixed-format input any model can act on. `validate` makes output correctness code-checkable. `auto-disposition` removes the model from the loop entirely. `digest` and `preflight` reduce session context footprint, making small-context models viable for tasks already in the model-agnostic tier.

The practical consequence: once Phase 11 tools exist, there is a principled answer to "what can a local or cheaper model do?" — any task whose inputs are pre-generated by these tools and whose outputs pass `validate`. That is the model-agnostic tier. Interpretive narrative, Wikipedia analysis, and historical significance remain model-sensitive. This is an honest architectural boundary, not a capability gap to be closed by testing more models.

### Empirical verification (Phase 22 P3)

The claim above is no longer only argued — it is measured. The cross-model MVO benchmark (`tests/benchmarks/cross_model_mvo.py`) runs the model-agnostic-tier tasks `historian card --infer` and `historian draft` over a fixed three-fixture set (one confirmed pair from each existing project) under two models, and asserts each output passes its MVO validator: the structured RECOMMENDATION/SCORE/REASONING parse for infer, and `historian validate` (8/8 DB-backed checks) for drafts.

Run 2026-06-11 (3 fixtures × {infer, draft} = 6 validated outputs per model):

| Model | Validator pass | Prompt tok | Completion tok | Cache read | Est. cost |
|---|---|---|---|---|---|
| `claude-haiku-4-5-20251001` | 6/6 | 16,721 | 3,861 | 0 | $0.0360 |
| `claude-sonnet-4-6` | 6/6 | 3,324 | 4,474 | 8,082 | $0.0947 |

Both models pass every validator. That is the proof: the model-agnostic tier is genuinely model-agnostic — a 5×-cheaper model produces output that clears the same deterministic correctness gate as the stronger one. Model choice on this tier is a cost decision, not a correctness one.

The token columns also independently confirm the prompt-cache finding from Phase 22 P2: the ~2K-token system prefix caches on Sonnet 4.6 (2048-token minimum — `cache_read` 8,082, accumulated across the separate CLI invocations within the cache TTL) but **never on Haiku 4.5** (4096-token minimum — `cache_read` 0). The same prompt, the same code, opposite cache behaviour, decided entirely by the model's minimum. Haiku is still cheaper here in absolute terms despite caching nothing, because its per-token price is lower; but the result shows exactly where raising the prefix above 4096 tokens (or accepting no cache) would change the Haiku economics.

---

## Scope-Neutral Databases

The three databases are shared infrastructure, not project artifacts. No project-specific data — date windows, CPC class sets, entity rosters, seed records — is baked into the database layer or the tool's source code. The databases grow as projects define new scope; they never shrink or reset between projects.

The practical consequence: adding a second project to Markery requires adding that project's data files and running the appropriate build commands. It does not require modifying any source code, changing any schema, or rebuilding data that existing projects depend on. Two projects can share `patents.duckdb` without interfering with each other's fetch logs or confirmed pairs.

This was not always the case. Earlier versions of Markery had `DATE_START`, `DATE_END`, `CPC_CLASSES`, `SEED_PATENTS`, and `ENTITIES`/`VARIANTS` as module-level constants in the build scripts — all specific to the information-systems project. A database review pass moved all of this into per-project data files and made the build commands scope-neutral. The databases are now reusable across projects without code changes.

---

## Token Instrumentation

Markery commands that call Claude accept a `--tokens` flag and an optional `MARKERY_TOKEN_LOG` environment variable. When set, each API call appends a JSONL record to the log file with `specialist`, `command`, `model`, `prompt_tokens`, `completion_tokens`, and `wall_ms` fields.

```bash
MARKERY_TOKEN_LOG=tests/benchmarks/my-project.jsonl \
  markery historian digest my-project --tokens
```

The instrumentation serves two purposes: **cost tracking** (actual API spend per command per session) and **baseline enforcement** (prompt token counts for `digest` and `card` are tracked across projects to detect regressions caused by schema changes or content growth).

The token baseline for each command type (established in Phase 14) is recorded in `tests/benchmarks/README.md`. Any command whose token count exceeds the baseline by >20% on a new project is a regression signal and must be investigated before the session continues.

**Context budget control:** The `MARKERY_CONTEXT_BUDGET` environment variable (integer, token count) limits how much context historian commands assemble. Default 4000. Useful for running the same commands on smaller models without changing code.

**LIBRARIAN extraction:** `markery librarian extract` is the highest-cost API operation — it chunks raw OCR text (~8,000 chars/chunk, 800-char overlap) and calls Claude once per chunk to extract relevant passages. Token counts for extract scale with the size of the work and are always recorded in the session benchmark log.

---

## Publishing as a Specialist Operation

The publisher is a full specialist agent, not a post-processing script. This matters because publishing involves non-trivial decisions: resolving figure references against stored BLOBs, enhancing trademark images for legibility, pulling Wikipedia summaries for entity context pages, and rendering structured Markdown into HTML with the right asset paths. These are mechanical but consequential — a broken figure reference or a missing image silently degrades the published result.

Making the publisher a specialist agent with its own queries module means: the build is deterministic (the same content files always produce the same site), the build is auditable (every figure reference is resolved through a single code path), and the agent can build the site as easily as a human can. The site directory is gitignored because it is always regenerable from the content files and the databases — the content files and `confirmed.jsonl` are the durable artifacts, not the rendered output.

---

## Prompt Caching

### What is cached

Every call to `common.llm.call()` wraps its system prompt in an `{"type": "ephemeral"}` cache_control block. The system prompt is the canonical cache candidate: it is identical across all calls of the same command type in a session, while the user message changes (new card text, new scaffold, new chunk).

Three commands have cacheable system prompts:
- **`historian card --infer` / `digest --infer`:** The full historian `identity.md` + task instructions (~2,100 tokens). On the second card call within a session, the identity block is read from cache; only the new card text is billed at standard input rates.
- **`historian draft`:** Same identity + draft task instructions (~1,960 tokens).
- **`librarian extract`:** Librarian `identity.md` + extraction task specification (~2,255 tokens). On a typical 15-chunk extract run, chunk 1 creates the cache and chunks 2–15 read it — a 93% hit rate.

### How to verify

With `MARKERY_TOKEN_LOG` set, each log record includes `cache_read_tokens` and `cache_creation_tokens`. A cache hit shows `cache_read_tokens > 0`; a cache creation shows `cache_creation_tokens > 0`. The effective cost of a repeated call is `(prompt_tokens + cache_read_tokens)` but only `prompt_tokens` is billed at the standard rate — `cache_read_tokens` are billed at roughly 10% of the input rate.

```
[tokens] prompt=192 completion=253 cache_read=2,087 wall=7636ms (claude-sonnet-4-6)
```

This card call: 192 tokens billed at standard rate, 2,087 tokens billed at cache-read rate.

### Cache TTL and session boundaries

The Anthropic prompt cache TTL is 5 minutes. Calls more than 5 minutes apart within a session will miss the cache and re-create it on the next call. A single `librarian extract` run (all chunks processed within seconds) achieves near-100% hit rate. A multi-hour research session will have periodic re-creation events.

### Current status (Phase 18 P6)

Caching confirmed active on `claude-sonnet-4-6` (cache_read_input_tokens > 0 observed on repeated calls). Not activating on `claude-haiku-4-5-20251001` with the current API key — likely an account or regional routing limitation (`inference_geo='not_available'` in usage response). The mechanism is correctly implemented in all three call sites; no code changes are required when Haiku caching becomes available.
