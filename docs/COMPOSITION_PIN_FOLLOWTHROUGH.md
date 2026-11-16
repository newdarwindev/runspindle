# Composition pin follow-through candidate

Partial composition #45 integration, based on root
`a622177553f54a71d09454fe05fcc122049a6cb8`. This is a draft candidate, not a
release-qualified upgrade or full product acceptance.

## Paired source changes

| Component | Previous lock and gitlink | Candidate lock and gitlink |
|---|---|---|
| Browser | `56b78515fc3edbfb5e199cebc9c60db110c60f68` | `595dd6e75b85ce2069e8aa8a8adb5a9271ab67e3` |
| Tether | `ef4c99a8eea8918350666948a32868e3763e1dbe` | `c3fbfb9ff5ed0483e522c93268ced9e40a6cb79d` |
| Refinery | `8959700953b14b8fe7fb86efd8d7647ad364bfe1` | `3b14229b32cd0abef65937f3a9d9a9474a2ca937` |

Tether is included because the selected Refinery already requires that exact
commit. Core, Host, Console and Platform pins are unchanged. No component
implementation is edited. Current source manifests, requirement-reference hashes
and existing CI checkout refs follow the selected sources; runner policy,
permissions, triggers, package pins and validation assignments are unchanged.

The real H10 seam exposed two compatibility changes: FeedbackStore now resolves
`feedback_schema.open_feedback_store`, and its durable head table is
`feedback_heads_v2`. Explicit constructor identity checks are retained. The
missing-table regression additionally removes `feedback_invalidations` and
independently requires zero lineage writes and no schema repair. All newly
imported verified Refinery modules are included in the source hash closure.

## Evidence boundary

Fresh standalone retained-feedback H10 runs passed in normal and optimized
Python. Each runs the actual pinned SQLite stores twice, reopens fresh processes,
checks three negative cases and five missing-schema denials, observes precommit
crash recovery and detects a deliberately removed authority recheck. Both produce
the same independent object digest:
`d40f8b7bc90b5e02c48c7ef8cbea210810b07d13cadc4434412420ffece9d08f`.
This lane uses synthetic authority/provider adapters, invokes no model or training,
and explicitly reports system acceptance blocked.

Full Python discovery passed 347 tests with zero skips in each normal and
optimized mode on the final executable source. The initial full run found one
stale test expectation (four rather than five schema denials); it was corrected
and both final modes passed.

Scaffold/artifact integrity, Core/Host library alignment, core-product requirement
coverage, repository hygiene, seven-component maintained-manifest inventory and
whitespace checks passed. Static-quality execution is blocked because this
workspace has no Ruff package metadata; no missing check is called passed.

Historical receipts are unchanged. STATUS explicitly limits previous H10/H11/H12
passes to the immutable old manifest. The new maintained manifest is source-bound
only: actual maintained H10/H11/H12 execution, prepared DSPy dependencies,
Core/Platform container artifacts, Browser runtime integration, full aggregate,
remote CI, runner qualification and all live/provider/deployment acceptance remain
not run. These prerequisites remain gates before release qualification.

## Reproduction

Initialize exact submodules and use the manifest-pinned sources, not moving main
branches. Run `python3 -B tools/feedback_hero.py` and the same with `-O`. For full
Python discovery set `RUNSPINDLE_FEEDBACK_HERO_TETHER` and
`RUNSPINDLE_FEEDBACK_HERO_REFINERY` to the exact clean component checkouts; run
`python3 -B -m unittest discover -s tests -v` and repeat with `-O`.

Initial diagnostic attempts intentionally exposed old source-manifest/pin guards,
the changed FeedbackStore constructor and renamed table. Those failures were not
ignored or reported as passes. Historical qualification was not transferred.
