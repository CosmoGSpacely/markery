# Instruction Card: Patent Verify Credentials

## When to use

At the start of any session that will call the EPO OPS API — before `markery patent build`, `markery patent pull`, or `markery patent fetch`. Also use to diagnose 403 errors or token expiry issues.

Requires `EPO_CONSUMER_KEY` and `EPO_CONSUMER_SECRET` in the environment (or `.env` file at repo root).

## What this produces

Prints the active token prefix and remaining TTL to stdout. Exits with code 0 on success, 1 on failure.

## Command

```bash
markery patent verify-credentials
```

## Troubleshooting

| Output | Cause | Fix |
|--------|-------|-----|
| `EnvironmentError: EPO_CONSUMER_KEY not set` | Missing env var | Add key to `.env` and run `source .env` |
| `Credential check failed: 401` | Wrong key/secret | Re-check EPO developer portal credentials |
| `Expires in: 0s` | Token expired | Normal — the client refreshes automatically on next API call |
