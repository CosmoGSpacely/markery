"""Discovery-loop on/off state (Phase 30 P6).

The continuous discovery loop runs as a **persistent service the user toggles**.
This module owns the toggle: a small JSON flag at ``library/discovery_state.json``
that the loop runner (markery-langgraph ``discovery_graph``) reads each tick — when
disabled, a tick is a no-op. Markery owns the *switch*; langgraph owns the *work*.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from markery.common import config

_DEFAULT = {
    "enabled": False,
    "projects": [],          # discovery scope; empty = all match-review-essay projects
    "sources": ["loc", "chronam"],
    "relevance_floor": 3,    # score (1-5) at/above which a candidate is acted on
    "last_tick": None,
}


def state_path() -> Path:
    return config.ROOT / "library" / "discovery_state.json"


def read_state() -> dict:
    p = state_path()
    if not p.exists():
        return dict(_DEFAULT)
    data = dict(_DEFAULT)
    data.update(json.loads(p.read_text(encoding="utf-8")))
    return data


def write_state(state: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".discovery-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def set_enabled(enabled: bool, **overrides) -> dict:
    state = read_state()
    state["enabled"] = enabled
    for k, v in overrides.items():
        if v is not None:
            state[k] = v
    write_state(state)
    return state


def mark_tick() -> dict:
    state = read_state()
    state["last_tick"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_state(state)
    return state
