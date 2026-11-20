# H09 Console freshness and passive views

This composition lane runs the pinned Console `createProjection`, `select`,
`refresh`, `merge`, `view` and `dispose` entrypoints. The test supplies scripted
snapshot reads, revisioned events, a clock and passive-view handles. The selected
identity includes task, host, workspace, native session, browser and lease epoch.

Run in a clean composition checkout with the pinned Console submodule and Node
available:

```sh
python3 -B tools/console_freshness_hero.py
```

The harness checks each composition lock/gitlink pair and loads the exact Console
projection source from pinned Git bytes. It then runs two independent Node
processes with the same fixture and compares receipts. The pinned module loads
inside a VM context with URL and abort primitives, a restricted module loader
and no socket or process API. The temporary directory is removed when the run
ends. Each worker has a 12-second process deadline. Existing composition
unittest discovery includes the lane.

| Schedule | Observation |
| --- | --- |
| Switch A to B and supersede an in-flight B snapshot | Late A and late B responses cannot change the selected B snapshot |
| Send the wrong lease, a repeated revision, a regressed timestamp and a missing timestamp | Invalid observations leave the active projection unchanged |
| Supply unknown time, a sequence gap, a disconnect and a failed read | The projection reports unknown, offline or error and never opens a view in these states |
| Reconnect, cancel a pending view, disconnect an active view, reconnect again and advance the clock | Freshness returns only on the snapshot, both handles close exactly once, task B stays selected, and the view stays closed once stale |

The observed receipt records seven snapshot reads, two passive open calls, two
handle closes and zero control requests. Two deliberate faults in temporary
copies failed the expected assertions by applying a superseded response and
reporting an unknown timestamp as fresh.

Local verification used macOS arm64, Python 3.13.18 and Node v26.13.0. Normal and
optimized Python emitted identical receipts. The composition base was
`fc68cb72528922217d50663c6761a148e1a3cb35`.

| Input | SHA-256 |
| --- | --- |
| Composition lock | `c42564215bfa5a8eab659c01196a3727e30787355dadd593f3f9a3b6f69ea1b0` |
| Fixture | `1dfe4ae491e4286f45e4a83ea06f4315b0217212e7fd66468673770a43da10f9` |
| Console projection | `daf72b3303a88e18742ab86380dff1f540b095116255845b6a80b4753f466d64` |
| Runner | `b8c5ed22a6d2fe7bd73bc213cda463738f5492b424872964f4bf98bfa1daef74` |
| Tests | `5a093b96b3afd47107fffd769410827bf81c39e51c90b9210013c53dd5446701` |

This is the Console component lane for composition issues #16 and #45. The
projection is process-local. Real fleet and session streams, runtime desktop
handles, the other component lanes, and full system and live acceptance remain
open.
