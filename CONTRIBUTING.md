# Contributing to Markery

Thank you for your interest in contributing. Markery is a research tool under active development. Contributions are welcome, particularly around:

- Additional CPC class coverage or entity definitions for new research projects
- New specialist commands or output formats
- Test coverage improvements
- Documentation corrections and SETUP.md clarity

---

## Getting started

1. Fork the repository and clone your fork
2. Follow [SETUP.md](SETUP.md) through step 1 (clone and environment)
3. API credentials are only needed if you plan to call the EPO or USPTO APIs; most code changes can be tested without them
4. Install with dev dependencies: `pip install -e ".[dev]"`
5. Run tests: `python -m pytest`

---

## Code conventions

- **Python 3.11+** with type annotations on all public functions
- **No cross-specialist imports** — specialists communicate only through `orchestrator.py`
- **Classify before acting** — see `CLAUDE.md` for the three-tier work classification (Markery / Specialist / Project)
- **No comments explaining what the code does** — names should do that. Comments are for non-obvious constraints or workarounds only.
- **No hardcoded project names** in source — `information-systems` is the live research project, not a default

---

## Testing

All changes should include or update tests. The test suite is in `tests/`. Tests use `tmp_path` fixtures and do not require live API credentials or the committed `.duckdb` files.

```bash
python -m pytest          # full suite
python -m pytest tests/test_common.py   # one file
```

CI runs on every push and pull request.

---

## Pull requests

- One logical change per PR
- Include a description of what changed and why — not just what
- If the change affects CLI behavior or command output, update the relevant `persona/instructions/` card
- If the change adds a new command or modifies a command's interface, update `SETUP.md` if that command appears there

---

## Specialist boundary rule

Each specialist owns its subtree exclusively. A PR that writes to `src/markery/specialist/patent/` should not also write to `src/markery/specialist/trademark/`. Cross-specialist coordination belongs in `orchestrator.py`. See `CLAUDE.md` for the full boundary enforcement rule.

---

## Reporting issues

Open an issue on GitHub with:
- What you ran (exact command)
- What you expected
- What happened (full error output)
- Python version and OS
