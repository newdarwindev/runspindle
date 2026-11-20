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
Two mutations in disposable staged copies exposed duplicate and stale-authority
submissions and failed the independent call and site-row assertions.

Local verification used macOS arm64, Python 3.13.18 and SQLite 3.54.1. Normal and
optimized runs emitted identical receipts. The composition base was
`fc68cb72528922217d50663c6761a148e1a3cb35`.

| Input | SHA-256 |
| --- | --- |
| Composition lock | `c42564215bfa5a8eab659c01196a3727e30787355dadd593f3f9a3b6f69ea1b0` |
| Scenario and Browser file hashes | `e86a0addffecf2d17ccb70b59ced1f13a3d80ef54e55b1dcf189896b351104c4` |
| Runner | `7b4fa02659367ce514dab56fd81fa885be3e830447abbed3217e6c00d0290371` |
| Tests | `ab713a07c429ceb3bde967f54fdd724c721c7548a1bb8b7aa861bca83250b36b` |

This is the Browser component lane for composition issues #12 and #45. Core and
Host recovery, native browser fencing, actual site/vault adapters, and
full-system and live acceptance remain open.
