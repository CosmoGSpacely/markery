# projects/ and site/ archived — 2026-06-24

After Phase 27 (test hermeticity) made the suite independent of real project/corpus
data, the `projects/` and `site/` trees were archived so the platform can be rebuilt
on the improved database (Phase 28), library (Phase 29), and the autonomous loops
(Phases 30–31).

Nothing is lost:

- **`projects/` (git-tracked, 23 MB, 6 projects)** — preserved in git history. The last
  commit that contains the full tree is the one **immediately preceding** this archival
  commit. Retrieve any project with:

  ```
  git log --oneline -- projects/                  # find the last commit with projects/
  git checkout <that-commit> -- projects/<name>   # restore one project
  git checkout <that-commit> -- projects/         # restore all
  ```

  Projects archived: `animal-marks-1930`, `annual-design-review`,
  `information-systems`, `photographic-equipment`, `precision-tools`,
  `radio-pioneers`.

- **`site/` (gitignored, 129 MB)** — pure build output. Not preserved and not needed:
  it is regenerable at any time with `markery site build-all`.

- **Wikipedia work** — the only external evidence of Markery; retrievable from
  Wikipedia itself via `markery wikipedia check-revision` (per-project
  `wikipedia/submissions.jsonl` is inside the archived `projects/` tree in git history
  if needed).

The rebuild happens in the autonomous-growth phases: the spawning pipeline (Phase 31)
recreates projects from the corpus, and the site-design-pass stub (end of ROADMAP)
rebuilds the annual-review project and refreshes the site design first.
