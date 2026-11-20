# H08 Platform telemetry recovery

The Platform-only lane for [H08](https://github.com/newdarwindev/runspindle/issues/15)
executes the pinned `Pipeline.emit`, `Pipeline.flush`, and `Pipeline.receipt`
over its real SQLite spool. The supervisor verifies all seven composition
gitlinks against the lock and stages only the committed Platform files named
in [the scenario manifest](../scenarios/platform-telemetry-recovery-v1.json).
It uses the pinned synthetic producer and injected transport, and an independent
synthetic receiver with its own SQLite database for calls and persisted bytes.

| Fault or observation | Expected evidence |
| --- | --- |
| Reordered input, duplicate emission, transport errors and timeouts | Four exact events remain queued in the spool and the receiver stores no records |
| Receiver writes, then the pipeline loses the acknowledgment and exits | A fresh process sees one persisted event alongside four still-queued events |
| Fresh-process replay | Three accepted and one rejected delivery, with two matching copies of only one event |
| Accepted without a row, or with the same event ID and wrong policy digest | Zero exact copies for those events and no additional measured usage |
| Unmatched row containing resource and scope schema-URL canaries | Privacy is blocked without increasing the matching count |
| Deliberate correlation mutation | Matching only event ID falsely counts the wrong-policy row and fails the oracle |

The receiver ledger checks nine exact calls and the SHA-256 of each transmitted
envelope. It checks the task, session, event, trace, span, producer, configuration,
and policy contents independently of the pipeline receipt. The two matching
copies count as one event and seven usage units. Independent SQLite reads verify
the committed data across process boundaries. The interrupted child exits
after the receiver commits and before the pipeline records acceptance. This
exercises process interruption and SQLite reopen.

From the repository root with Platform checked out at the composition gitlink,
run with Python 3.13 or later.

```sh
python3 -I -B tools/platform_telemetry_hero.py
python3 -I -O -B tools/platform_telemetry_hero.py
python3 -B -m unittest discover -s tests -p test_platform_telemetry_hero.py
```

Each run compares two normalized campaigns with fixed IDs, seed, and clock.
Workers run in fresh isolated interpreters with 10-second deadlines. An audit
hook records and rejects attempted socket or process activity. The parent
removes the temporary campaign directory, including the interrupted worker's
files. The receipt identifies the exact composition head, pins, manifest, Python
and SQLite versions, and observation time.

The Platform-only result qualifies the synthetic spool and receipt adapter.
The all-fake, Core-only, Host-only, and Console-only lanes were not run.
Actual Collector schema-URL masking, Langfuse persistence, native telemetry,
joint integration, and live acceptance remain separate gates. Overall H08
acceptance stays blocked.
