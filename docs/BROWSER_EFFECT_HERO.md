# H05 Browser effect recovery

The composition check runs the pinned Browser `GuardedJournal.dispatch` and
`GuardedJournal.reconcile` entrypoints against a durable SQLite journal. The
existing Browser test site records every submission in a separate SQLite store
and deliberately allows duplicates. Composition injects a synthetic one-use
authority guard, a fixed clock, and an origin under `.invalid`.

## Reproduce

Initialize the pinned Browser submodule in a clean composition checkout. Run:

```sh
python3 -B tools/browser_effect_hero.py
python3 -OB tools/browser_effect_hero.py
```

The check verifies all seven lock and gitlink pairs and the Browser checkout
revision. It stages the seven listed Browser source files from pinned Git objects
after checking their hashes. Fresh isolated Python processes run each operation.
They record attempted Python socket and process creation calls before refusing
them. The parent reads both SQLite stores and the helper call journal directly.
The test uses temporary directories and gives each process a 12-second deadline.
Ordinary composition unittest discovery includes the check.

## Observed

| Synthetic fault | Site effects | Outcome before readback | Outcome after readback and reopen |
| --- | ---: | --- | --- |
| Accepted, reply lost | 1 | Unknown | Confirmed |
| Process exits before site commit | 0 | Unknown | Unknown |
| Process exits after site commit | 1 | Unknown | Confirmed |

All three cases ran twice with identical observations. None resubmitted after
restart. Wrong tab, account and lease epoch caused zero readback calls. Stale
and revoked authority caused zero submit calls and zero journal reservations.

For the lost-reply case, each readback failure runs in a fresh process against
the same SQLite stores. The parent independently verifies one retained site
effect, one submit total, and an unknown journal row with no stored evidence
after every failure.

| Readback fault | Worker observation | Retained outcome |
| --- | --- | --- |
| Synthetic timeout | Unknown | Unknown |
| Different payload digest | Unknown | Unknown |
| Different binding revision | Unknown | Unknown |
| Grant revoked after the site read | Denied | Unknown |
| Worker exits after the site read | Exit 19 | Unknown |

A later exact site read confirms that same operation. The next two workers
return the retained confirmation with zero extra site calls, even when one is
configured to return a mismatched digest if invoked. Three disposable source
mutations exercise duplicate dispatch, stale observation admission and
acceptance of a mismatched readback digest. The last mutation fails the
parent's direct SQL check of the unsettled journal row.

Local verification used macOS arm64, Python 3.13.18 and SQLite 3.54.1.
Normal and optimized runs emitted identical receipts on composition base
`1880adf` and Browser pin `595dd6e75b85ce2069e8aa8a8adb5a9271ab67e3`.

| Input | SHA-256 |
| --- | --- |
| Composition lock | `c42564215bfa5a8eab659c01196a3727e30787355dadd593f3f9a3b6f69ea1b0` |
| Scenario and Browser file hashes | `259052a9497fd6edde4db339f2269c8c1ed997530bdc68e24d0206656e5579c4` |
| Runner | `14e1e50afb9cb328b3b4386b1c945e76d9d0e37fa24af9b4f29e4ea8d9a385be` |
| Tests | `210eea8a6a0f1b2a5df9df702ad06c5a46629de2f2239dea5e8f8785aed593e5` |

This is the Browser component lane for composition issues #12 and #45. Core and
Host recovery, native browser fencing, actual site/vault adapters, and
full-system and live acceptance remain open.
