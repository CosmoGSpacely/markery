# Instruction Card: Trademark Verify Credentials

## When to use

At the start of any session that will call the USPTO TSDR API — before `markery trademark enrich-project`, `markery trademark fetch`, or `markery match preflight`. Also use to diagnose 401/403 errors.

Requires `USPTO_API_KEY` in the environment (or `.env` file at repo root).

## What this produces

Prints the API key prefix and response status to stdout. Exits with code 0 on success, 1 on failure.

## Command

```bash
markery trademark verify-credentials
```

## Troubleshooting

| Output | Cause | Fix |
|--------|-------|-----|
| `EnvironmentError: USPTO_API_KEY not set` | Missing env var | Add key to `.env` and run `source .env` |
| `Credential check failed: 401` | Invalid or revoked key | Re-issue key at developer.uspto.gov |
| `Credential check failed: 403` | Rate limit or IP restriction | Wait for rate window to reset; check API dashboard |
