# H09 Platform fleet freshness

The [fleet freshness fixture](../scenarios/platform-fleet-freshness-v1.json)
qualifies a single Platform lane for
[H09](https://github.com/newdarwindev/runspindle/issues/16) and
[real component adapters](https://github.com/newdarwindev/runspindle/issues/45).
It exercises the pinned Platform runner-fleet observer and the SQLite state it
reads. It covers freshness and admission of free capacity on the two-slot fleet.

| Boundary | Exercised implementation |
| --- | --- |
| Platform | `tools.runner_fleet.service.observed`, `lifecycle.capacity_snapshot`, and `state.State` |
| Service and guests | Scripted `systemctl show` response and two slot observations |
| Storage | A temporary SQLite store seeded with Platform's reservation and update methods. Each observer process reads it with a read-only SQLite connection. |
| Clock, identity, and job | Fixed clock and invented reservation, job, and runner identifiers |
| Browser, Console, Core, Host, Refinery, and Tether | Synthetic boundary with zero peer calls |
| Provider, live runner service, and hypervisor | Zero calls |

The harness checks all seven gitlinks against the composition lock and fixture.
It stages only the listed Platform Python modules from the reviewed Git
object. The report records the composition commit, lock and harness digests,
component commits, staged file digests, fixture and SQLite schema digests,
clock, and Python and SQLite versions.

## Fault schedule and expected observations

- A healthy idle inventory reports two free slots. A healthy guest tied to a
  running reservation reports one free slot. Draining reports zero free slots.
- Heartbeat expiry at the 120-second boundary, a missing heartbeat, a stale
  poll, and a future poll each block capacity. A missing guest response or
  missing manager status also blocks capacity.
- A running guest with an older reservation identity and an orphaned running
  guest each block capacity. A missing running guest retains the durable
  reservation as occupied and blocks free capacity.
- After the older identity is rejected, a fresh observer process reads the
  same store and receives the current guest identity. It reports one free
  slot with the same reservation and event history.

The parent reads SQLite directly before and after each observation and compares
the stored identity, ordered events, control values, schema, and database
bytes. It checks the exact read and observation calls in order. During
observation, SQLite permits only read statements. Python audit hooks reject
and record network, subprocess, and filesystem mutation attempts. The mutation
test removes the guest owner comparison from a temporary copy of the actual
Platform source. The older owner case must then fail the capacity check.

## Run locally

From a composition checkout with its Platform submodule already initialized:

```sh
python3 tools/platform_fleet_freshness.py
python3 -m unittest discover -s tests -p test_platform_fleet_freshness.py
python3 -O -m unittest discover -s tests -p test_platform_fleet_freshness.py
```

The CLI writes a sanitized report to stdout. It runs the fixture twice in
temporary directories with a deadline for each worker and compares normalized
observations. The harness cleans up the fixture stores and staged source when
the run exits normally or raises an error.

The lane leaves the H09 system aggregate blocked. The pinned observer uses
manager `ActiveState` for availability. Manager process exit status and PID
validation, a live guest lifecycle, the UI and desktop stream, and isolated
cross-component integration remain outside this evidence.
