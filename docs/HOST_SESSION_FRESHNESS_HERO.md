# H09 Host session freshness

This lane exercises the actual Host lifecycle adapter and its SQLite store at the
composition pin. These checks cover session identity and freshness for
[H09](https://github.com/newdarwindev/runspindle/issues/16) and the
[real adapter rollout](https://github.com/newdarwindev/runspindle/issues/45).

| Boundary | Exercise |
| --- | --- |
| Host | `Adapter::submit`, `event`, `reconcile`, `snapshot`, and `Capabilities::scripted` from `runspindle_host::lifecycle` |
| Storage | Actual `runspindle_host::storage::Sqlite`, reopened by a fresh worker for every step |
| Native peer and verifier | Scripted launch and discovery responses and grants scoped to the exact binding and action |
| Browser, Console, Core, Platform, Refinery, Tether | Synthetic peers with zero runtime calls. The prepared Rust dependency inventory comes from the Platform pin. |
| Desktop capture, providers, and physical hosts | No live calls. The Host reports the synthetic capability flags for Linux and macOS. |

## Expected observations

- Two tasks start on the same synthetic host with separate workspaces, native
  session IDs, and operation IDs. Unknown host reachability leaves a third
  task queued with no peer launch and no native timestamp.
- After selecting task B, a late observation for A is rejected against B.
  Replaying an accepted event, delivering a lower sequence, regressing the
  timestamp, and sending expired or future timestamps leave the current
  snapshot intact. A wrong session or lease epoch also leaves it intact.
- An empty discovery marks the session unknown and retains its last known
  identity and timestamp. Discovery in a fresh process restores the same
  session with a newer sequence. Task B keeps its own older observation.
- Every passive snapshot makes zero peer calls and leaves SQLite entries,
  generation, and ordered receipts intact. Retained snapshots can age without
  new writes. The harness labels their recorded timestamps `unknown`,
  `stale_retained`, or `recent_retained`. Host provides the stored timestamp
  and execution state. The freshness labels belong to the harness.
- Removing Host's sequence comparison in a temporary source copy makes the
  reordered event alter SQLite. The parent must reject the mutant at that
  step even if the worker reports success.

## Run the regression

From composition with the Host and Platform submodules initialized and the
locked Rust dependencies already in the local Cargo cache:

```sh
python3 tools/host_session_freshness.py --check-mutation
python3 -O tools/host_session_freshness.py --check-mutation
```

The existing Rust validation partition runs the first command. Both commands
build offline from reviewed Git blobs and the exact Host `Cargo.lock`. The
harness verifies that all dependency checksums are in the prepared Platform
closure. It runs the [fixed schedule](../scenarios/host-session-freshness-v1.json)
twice, checks a separate scripted peer ledger, and reads the actual SQLite
state directly after each process exits. The CLI writes a sanitized report
with source, fixture, dependency, and schema digests, ordered call and effect
observations, toolchain versions, and normalized outcomes. Build and worker
processes have deadlines. Temporary staged code, binaries, databases, and
ledgers are removed when the command exits normally or raises an error.

The H09 system aggregate remains blocked. This lane covers the pinned Host
library with a scripted native peer. An authenticated native transport,
physical host and desktop capture, and isolated cross-component integration
still require separate evidence.
