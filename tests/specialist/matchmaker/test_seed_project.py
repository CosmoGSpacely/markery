"""Phase 32 P4 — `project init --type` + `matchmaker seed-project`, hermetic."""

from __future__ import annotations

import csv
import json

from tests.fixtures.synthetic import build_synthetic_repo, run_markery, ENTITY_VARIANT


def test_init_type_then_seed_project(tmp_path):
    repo = build_synthetic_repo(tmp_path)

    out, rc = run_markery(repo, "project", "init", "acme", "--type", "match-review-essay")
    assert rc == 0, out
    pj = json.loads((repo.root / "projects" / "acme" / "project.json").read_text())
    assert pj["type"] == "match-review-essay"

    out, rc = run_markery(repo, "matchmaker", "seed-project", "acme",
                          "--entity", "Synthex Manufacturing Company", "--json")
    assert rc == 0, out
    result = json.loads(out.strip().splitlines()[-1])
    assert result["project"] == "acme" and result["entity_id"] >= 9001
    assert result["variants"] >= 1

    proj = repo.root / "projects" / "acme"
    ents = list(csv.DictReader((proj / "entities.csv").open()))
    assert ents[0]["canonical_name"] == "Synthex Manufacturing Company"
    # the corpus variant is resolved into variants.csv
    variants = [r["variant_name"] for r in csv.DictReader((proj / "variants.csv").open())]
    assert ENTITY_VARIANT in variants
    assert (proj / "entities.txt").read_text().strip() == str(result["entity_id"])


def test_seed_project_requires_existing_project(tmp_path):
    repo = build_synthetic_repo(tmp_path)
    out, rc = run_markery(repo, "matchmaker", "seed-project", "nope", "--entity", "X")
    assert rc != 0 and "No project" in out
