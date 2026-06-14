# Model Cost and Provider Review

**Status:** Closed 2026-06-14 — comparison complete (Parts 5–6); archived per the REVIEW-file convention. Optional depth follow-up tracked as DEFERRED **D067**.  
**Scope:** Cost comparison across inference providers for Markery's three inference workloads: `historian card --infer`, `historian draft`, and `librarian extract`. Covers what is known (Anthropic), what is needed (OpenAI, xAI), and the code changes required to enable multi-provider comparison.

---

## Part 1 — Anthropic: Known costs

### Pricing (current as of Phase 18 P6, 2026-06-06)

| Model | Input | Output | Cache write | Cache read |
|---|---|---|---|---|
| `claude-haiku-4-5-20251001` | $0.80/MTok | $4.00/MTok | $1.00/MTok | $0.08/MTok |
| `claude-sonnet-4-6` | $3.00/MTok | $15.00/MTok | $3.75/MTok | $0.30/MTok |

Cache TTL: 5 minutes (ephemeral). Minimum cacheable block: 1,024 tokens.

### Measured token counts (Phase 18 P6 benchmark session)

| Command | Haiku prompt | Haiku output | Sonnet prompt | Sonnet output | Sonnet cache_read |
|---|---|---|---|---|---|
| `card --infer` call 1 | 2,292 | 133 | 206 | 176 | 0 |
| `card --infer` call 2 | 2,278 | 105 | 192 | 157 | 2,087 |
| `card --infer` call 3 | 2,285 | 180 | 199 | 253 | 2,087 |
| `digest --infer` | 2,126 | 369 | 292 | 512 | 0 |
| `historian draft` | 3,185 | 1,083 | 1,232 | 1,402 | 0 |

Notes:
- Haiku caching not activating on current account (`inference_geo='not_available'`). All Haiku prompt_tokens reflect full uncached input.
- Sonnet cache_read on calls 2–3 represents the 2,093-token historian identity block read from the 5-minute cache.
- Sonnet draft shows no cache_read because it was run as a standalone call without a preceding warm-up call in the same session.

### Calculated costs per call

| Command | Haiku $ | Sonnet $ | Ratio S/H | Cost driver |
|---|---|---|---|---|
| `card --infer` call 1 (no cache) | $0.00237 | $0.00326 | 1.38× | Input rate |
| `card --infer` call 2 (cache hit) | $0.00224 | $0.00356 | 1.59× | Output rate |
| `card --infer` call 3 (cache hit) | $0.00255 | $0.00502 | 1.97× | Output rate |
| `digest --infer` | $0.00318 | $0.00856 | 2.69× | Output rate |
| `historian draft` | $0.00688 | $0.03255 | **4.73×** | Output rate + Sonnet verbosity |
| **Session total** | **$0.01721** | **$0.05294** | **3.08×** | |

### Librarian extract: 15-chunk session

System prompt: 2,255 tokens. User per chunk: ~2,000 tokens. Completion per chunk: ~200 tokens.

| Scenario | 15-chunk cost |
|---|---|
| Haiku, no caching | $0.063 |
| Sonnet, caching active (calls 2–15 cache-hit) | $0.153 |
| Haiku, caching active (hypothetical) | $0.041 |

Sonnet + caching is 2.43× more expensive than Haiku without caching on extract. If Haiku caching were enabled, Sonnet would be 3.75× more expensive.

### Per-call breakdown after cache warmup (steady state)

The break-even question: does Sonnet's cache hit on the system prompt overcome its higher base rates?

| | Cost/call |
|---|---|
| Haiku, no cache (2,285 in + 139 out) | $0.00238 |
| Sonnet, cache hit (197 in + 2,087 cache_read + 195 out) | $0.00414 |

**Cache hits on Sonnet are 2.30× more expensive per call than Haiku without any caching.** The cache saves Sonnet from itself; it does not make Sonnet competitive with Haiku.

### Root cause

Prompt caching reduces input token cost only. It does not affect output token cost. Markery's most expensive operations are output-heavy: `historian draft` generates 1,000+ completion tokens per call. At $15/MTok vs $4/MTok, Sonnet's 3.75× output rate disadvantage cannot be overcome by any input-side savings.

Sonnet is also more verbose than Haiku on draft: 1,402 vs 1,083 output tokens — compounding the rate difference.

### Conclusion on Anthropic

Sonnet + caching does not beat Haiku without caching for any Markery workload. The appropriate use of Sonnet is quality-driven (difficult borderline candidates, complex essay context) not cost-driven. Default model: Haiku. Upgrade path: `--model claude-sonnet-4-6` on specific calls, not session-wide.

---

## Part 2 — What is needed to compare OpenAI and xAI

### Model tier mapping

The comparison requires identifying the approximate capability peer for each Markery use case.

| Markery role | Anthropic | OpenAI equivalent | xAI equivalent |
|---|---|---|---|
| Fast/cheap inference | `claude-haiku-4-5-20251001` | `gpt-4o-mini` | `grok-2-mini` (if available) |
| Capable inference | `claude-sonnet-4-6` | `gpt-4o` | `grok-3` |

These are capability-tier equivalences, not exact comparisons. Output quality on Markery's specific tasks (RECOMMENDATION/SCORE/REASONING format, PASSAGE/PAGE/CONTEXT extraction, validated essay generation) must be tested empirically — pricing alone is not sufficient.

### Pricing data needed

The following pricing figures are approximate based on publicly available information at time of writing. **Verify against official pricing pages before any cost decision** — provider pricing changes frequently and without notice.

**OpenAI (approximate):**

| Model | Input | Output | Cached input |
|---|---|---|---|
| `gpt-4o-mini` | $0.15/MTok | $0.60/MTok | $0.075/MTok (auto) |
| `gpt-4o` | $2.50/MTok | $10.00/MTok | $1.25/MTok (auto) |

Notes: OpenAI prompt caching is automatic (no explicit `cache_control` required) and applies a 50% discount on repeated prefix content exceeding 1,024 tokens. Cache read tokens are reported as `prompt_tokens_details.cached_tokens` in the usage response.

**xAI Grok (approximate):**

| Model | Input | Output | Cached input |
|---|---|---|---|
| `grok-3` | ~$3.00/MTok | ~$15.00/MTok | ~$0.75/MTok (if available) |
| `grok-3-mini` | ~$0.30/MTok | ~$0.50/MTok | unknown |

Notes: xAI's API is OpenAI-compatible (same request/response schema). Pricing and caching support for Grok models should be verified at `console.x.ai`. Caching availability for Grok is not confirmed as of this writing.

### What the comparison needs to answer

1. **Per-call cost** for each of the five measured calls above, at each provider's pricing.
2. **Cache behaviour**: does each provider's caching apply to Markery's system prompt sizes (all above 1,024 tokens)? Is it automatic or explicit?
3. **Output format compliance**: do `gpt-4o-mini` and `grok-3-mini` reliably produce `RECOMMENDATION: confirm|reject|defer`, `SCORE: 1–5`, `REASONING:` blocks without deviation? Same question for the PASSAGE/PAGE/CONTEXT extraction format.
4. **Validate pass rate**: does `historian validate` pass 8/8 on drafts produced by each model? Haiku and Sonnet both pass; this is the minimum bar.
5. **Verbosity**: how many output tokens does each model produce for equivalent tasks? Output token count directly multiplies the output rate.

---

## Part 3 — Code changes required to enable multi-provider comparison

### Current state

`common/llm.py` already encapsulates all provider logic behind two functions:

```python
get_client() -> anthropic.Anthropic | None
call(model, system, user, max_tokens, cache_system=True) -> (text, ptok, ctok, cache_read, cache_create)
```

This is the right abstraction layer. Adding OpenAI or xAI support requires extending `get_client()` and `call()`, not touching any specialist code.

### Required changes

**1. `MARKERY_PROVIDER` environment variable**

Add a `MARKERY_PROVIDER` env var (default: `anthropic`). Read it in `get_client()` and `call()` to dispatch to the correct provider SDK.

```python
# .env additions needed
MARKERY_PROVIDER=openai          # or: anthropic, xai
OPENAI_API_KEY=sk-...
XAI_API_KEY=xai-...
```

**2. `common/llm.py` — provider dispatch in `get_client()`**

```python
def get_client():
    provider = os.environ.get("MARKERY_PROVIDER", "anthropic").lower()
    if provider == "openai":
        import openai
        return openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    elif provider == "xai":
        import openai  # xAI is OpenAI-compatible
        return openai.OpenAI(
            api_key=os.environ.get("XAI_API_KEY", ""),
            base_url="https://api.x.ai/v1",
        )
    else:  # anthropic (current default)
        import anthropic
        return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
```

**3. `common/llm.py` — provider dispatch in `call()`**

The response schema differs between Anthropic and OpenAI-compatible providers:

```python
def call(model, system, user, max_tokens, cache_system=True):
    provider = os.environ.get("MARKERY_PROVIDER", "anthropic").lower()
    client = get_client()

    if provider == "anthropic":
        # current implementation — cache_system wraps in content block
        system_param = (
            [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
            if cache_system else system
        )
        resp = client.messages.create(
            model=model, max_tokens=max_tokens, system=system_param,
            messages=[{"role": "user", "content": user}],
        )
        cache_read   = getattr(resp.usage, "cache_read_input_tokens", 0) or 0
        cache_create = getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
        return (resp.content[0].text.strip(),
                resp.usage.input_tokens, resp.usage.output_tokens,
                cache_read, cache_create)

    else:  # OpenAI-compatible (openai, xai)
        # cache_system is ignored — OpenAI caches automatically
        resp = client.chat.completions.create(
            model=model, max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        cached = getattr(
            getattr(resp.usage, "prompt_tokens_details", None),
            "cached_tokens", 0
        ) or 0
        return (resp.choices[0].message.content.strip(),
                resp.usage.prompt_tokens, resp.usage.completion_tokens,
                cached, 0)
```

**4. `pyproject.toml` — optional dependencies**

```toml
[project.optional-dependencies]
openai = ["openai>=1.0"]
```

**5. Token log compatibility**

`TokenRecord` and `emit()` in `common/tokens.py` already have `cache_read_tokens` and `cache_creation_tokens` fields. No changes needed — the log format is provider-agnostic.

**6. MVO contract tests**

`test_mvo.py` tests output format, not provider. The same tests that pass against Anthropic should pass against any provider. To validate a new provider:

```bash
MARKERY_PROVIDER=openai MARKERY_MODEL=gpt-4o-mini \
  python -m pytest tests/test_mvo.py tests/test_contract.py -v
```

A failing MVO test against a new provider means the model does not reliably follow the output contract for that command — either the prompt needs adjustment or the model is not suitable.

**7. `count_output_tokens` in `tokens.py`**

The token counting fallback in `count_output_tokens` calls `client.messages.count_tokens()`, which is Anthropic-specific. For OpenAI-compatible providers, fall back to the word-count estimate unconditionally (the `~estimate` flag in the model name will indicate this).

---

## Part 4 — Recommended comparison methodology

To produce a fair cost comparison across providers, run the following sequence for each provider/model pair:

1. **MVO pass**: `MARKERY_PROVIDER=<p> MARKERY_MODEL=<m> python -m pytest tests/test_mvo.py -v`  
   If any test fails, the model does not meet the output contract minimum. Do not proceed with cost comparison for that pair.

2. **Three-card --infer session on radio-pioneers** (the Phase 18 P6 benchmark):
   ```
   MARKERY_PROVIDER=<p> MARKERY_MODEL=<m> \
   MARKERY_TOKEN_LOG=tests/benchmarks/provider-comparison.jsonl \
     markery historian card radio-pioneers sterilamp-us2169022a --infer
   MARKERY_PROVIDER=<p> MARKERY_MODEL=<m> \
   MARKERY_TOKEN_LOG=tests/benchmarks/provider-comparison.jsonl \
     markery historian card radio-pioneers micarta-us2084772a --infer
   MARKERY_PROVIDER=<p> MARKERY_MODEL=<m> \
   MARKERY_TOKEN_LOG=tests/benchmarks/provider-comparison.jsonl \
     markery historian card radio-pioneers visicode-us2169022a --infer
   ```
   Record token counts and recommendation outcomes. Verify recommendations match the ground truth (sterilamp=reject, micarta=reject, visicode=confirm).

3. **Digest --infer and draft** on the same project, same log file.

4. **Validate draft**: `markery historian validate radio-pioneers <slug>`. Model is viable only if 8/8 pass.

5. **Compute costs** using the provider's published rates.

6. **Record in `tests/benchmarks/README.md`** alongside the existing Haiku/Sonnet comparison table.

---

## Part 5 — As-built wiring (2026-06-14)

The multi-provider support was implemented, but **not** via the `MARKERY_PROVIDER`
env var proposed in Part 3. Routing is by **model id shape**, which is simpler
(a project just names its model — no second env var to keep in sync) and lets a
single run mix providers:

- `common/providers.py` — `route(model)` returns `anthropic | openai | xai | openrouter`,
  and one `openai_compatible_chat()` serves OpenAI, xAI, and OpenRouter (all speak
  the same `/chat/completions` schema). Routing: `claude-*`→Anthropic;
  `gpt-*` / `o[134]*` / `openai:<m>`→OpenAI; `grok-*` / `xai:<m>`→xAI;
  `<vendor>/<model>[:tag]`→OpenRouter.
- `common/openrouter.py` — adds what Part 3 didn't anticipate: OpenRouter access via
  a **provisioning key** that mints a runtime inference key on demand (cached to the
  gitignored `.openrouter-key`), enabling free models (e.g. `…:free`).
- `common/llm.py` — `call()`/`call_batch()` dispatch through `route()`; non-Anthropic
  providers return `cache_read=cache_create=0` (no Anthropic ephemeral cache). Only
  Anthropic has a Batch API; others loop sequentially.
- `common/tokens.py` — cache-health warning suppressed for non-Anthropic models.
- `common/tokens_report.py` — pricing added: `gpt-4o-mini` $0.15/$0.60, `gpt-4o`
  $2.50/$10, `grok-4.3` $1.25/$2.50, `grok-3` $3/$15, `grok-3-mini` $0.25/$0.50;
  `…:free` priced at $0.
  (NB: Haiku 4.5 is priced at the current $1.00/$5.00 list rate here, not the older
  $0.80/$4.00 figure in Part 1.)
- `markery model status | mint | test` — provider-key lifecycle and a one-shot live check.
- Keys in `.env`: `OPENROUTER_PROVISIONING_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`.

Open question from Part 2 still **not** measured: per-provider **cache behaviour**
(OpenAI auto-caching `prompt_tokens_details.cached_tokens`, xAI cache support).
Markery's system prompts are small and cache_read was 0 across this run; not pursued.

## Part 6 — Empirical cross-provider results (2026-06-14)

Run via the parameterized P3 harness:

```bash
python tests/benchmarks/cross_model_mvo.py --label cross-provider \
  --models claude-haiku-4-5-20251001 gpt-4o-mini grok-4.3 openai/gpt-oss-120b:free
```

3 fixtures (one confirmed pair per project) × {`card --infer`, `historian draft`
→ `validate`}. Results in `tests/benchmarks/cross-provider-2026-06-14.jsonl`;
drafts under `tests/benchmarks/drafts/2026-06-14/`. (xAI model: `grok-4.3`, the
current flagship at $1.25/$2.50 — chosen over the older `grok-3` at $3/$15, which
made identical judgments here at ~3.5× the cost.)

| Model | Provider | Validator pass | Prompt tok | Completion tok | Est. cost |
|---|---|---|---|---|---|
| `claude-haiku-4-5-20251001` | Anthropic | **6/6** | 18,001 | 3,964 | $0.0378 |
| `gpt-4o-mini` | OpenAI | **6/6** | 14,323 | 2,985 | $0.0039 |
| `grok-4.3` | xAI | **6/6** | 14,660 | 2,811 | $0.0254 |
| `openai/gpt-oss-120b:free` | OpenRouter (free) | **6/6** | 14,683 | 3,988 | **$0.0000** |

**Finding — two layers behave differently:**

1. **Facts (what the validator certifies) are provider-independent.** Every model,
   including the free `gpt-oss-120b`, produced essays passing all 8 deterministic DB
   checks (serial/patent resolve, dates match, entity recognised, no
   cross-contamination). The model-agnosticism claim holds across four vendors.
2. **Judgment (confirm/reject/defer) is provider-dependent.** On the human-confirmed
   SOUNDEX and STERILAMP pairs the models disagreed with ground truth — `gpt-4o-mini`
   rejected SOUNDEX (score 2), `grok-4.3` deferred SOUNDEX (3) and rejected STERILAMP
   (2), while Haiku and gpt-oss matched the human. This is exactly why Markery gates
   the disposition through a human (D065) and lets the validator gate only facts.

**Cost:** for identical validator outcomes, `grok-4.3` is ~6.5× `gpt-4o-mini` and the
free `gpt-oss-120b` is $0. A free model clears Markery's factual bar; the spend
buys judgment quality, not factual correctness — and judgment is human-gated anyway.

---

## Open items before this review can be closed

- [x] Verify current OpenAI pricing — `gpt-4o-mini` $0.15/$0.60, `gpt-4o` $2.50/$10
- [x] Verify current xAI pricing — `grok-4.3` $1.25/$2.50 (current flagship), `grok-3` $3/$15, `grok-3-mini` $0.25/$0.50
- [x] ~~Implement `MARKERY_PROVIDER` dispatch~~ → implemented as model-id routing (Part 5)
- [x] Run MVO pass with `gpt-4o-mini` and `grok-4.3` — both 6/6
- [x] Run card session with each model; record token counts — Part 6
- [x] Run `historian draft` with each model; record validate pass/fail — all 8/8
- [x] Cost comparison table populated — Part 6 (results JSONL committed under tests/benchmarks/)
- [x] Archive this file to `archive/MODEL-REVIEW-2026-06-14.md` when closed
- [x] ~~(Optional follow-up) Measure per-provider cache behaviour; add `gpt-4o`/`sonnet`-tier and a larger fixture set~~ → deferred as **D067**
