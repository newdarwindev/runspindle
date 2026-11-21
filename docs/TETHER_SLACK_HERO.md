# H01 signed Slack work and delivery recovery

The [scenario manifest](../scenarios/tether-slack-v1.json) pins the Tether source
used by this lane. The runner checks the composition lock against all seven
gitlinks before staging only the named, hash-verified Tether modules. The
fixture fixes the clock, source identities, host, synthetic session, and
accepted artifact bytes.

| Boundary | Exercised |
| --- | --- |
| Tether | Signed Slack revision ingress, real SQLite admission and projections, and SQLite provider attempt journal |
| Native input | Tether's synthetic exposed-event fixture with invented session identity |
| Core and Host | Synthetic approval/route and native event inputs |
| Slack | Separate non-idempotent SQLite effect store with scripted replies |

The first process admits the original signed request and one edit. Replays,
invalid or stale signatures, a cross-channel callback, and an edit without its predecessor
cannot add an admission. A new process mirrors only the public event and stores
one sanitized projection for the exact current revision. Wrong-session, stale,
reordered, hidden, and duplicate events make no projection calls.

The same worker rejects a send for the superseded revision and sends the current
accepted artifact once. The provider commits its effect before dropping the
acknowledgment. A second scenario terminates the worker immediately after the
provider commit, before Tether can record a response. Both retain the original
send reservation. Fresh workers recover during an outage, on a wrong-thread
response, and on exact readback. The first two observations remain unknown.
An independent read-only SQLite check verifies the provider call order, reply
identity, exact destination, attachment bytes, and single committed effect.
The harness scans the retained files and worker output for the synthetic
redaction canary. An isolated mutation that resends on recovery must produce
extra provider effects and fail the same oracle.

## Reproduce

```sh
git submodule update --init -- components/tether
python3 -B tools/tether_slack_hero.py
python3 -O -B tools/tether_slack_hero.py
```

Each invocation runs the same fault schedule twice and compares its normalized
observations. Workers have a 15-second deadline and deny network and external
process operations. The parent removes all staged sources, mutation copies
and evidence databases when the temporary directory closes.

The exit code covers this bounded Tether lane. The JSON report keeps the system
aggregate blocked and the Core-only, Host-only, and live lanes unrun. Actual
Slack transport, native capabilities, and cross-component acceptance remain
open under [H01](https://github.com/newdarwindev/runspindle/issues/8) and
[issue #45](https://github.com/newdarwindev/runspindle/issues/45).
