# H03 scoped Browser credential qualification

The Browser-only lane for [H03](https://github.com/newdarwindev/runspindle/issues/10)
runs the pinned `Resolver.resolve_and_inject` and OpenBao KV `Vault.read`,
`Vault.current`, and `Vault.consume` together. The exact Browser gitlink,
selected source digests, and fault schedule are in
[browser-credential-scope-v1.json](../scenarios/browser-credential-scope-v1.json).
The runner compares all seven gitlinks with `composition.lock.json` and stages
committed Browser files from the clean pinned checkout.

| Boundary | Implementation used |
| --- | --- |
| Browser credential resolution and KV version checks | Pinned Browser code |
| Ticket and trusted runtime observations | Synthetic one-shot ticket, guard, and fixed clock |
| OpenBao transport | Pinned Browser test peer with synthetic token and KV response |
| Website field injection | Synthetic guarded sink with an independent effect ledger |
| Core-only and Host-only lanes | Not run |
| Joint integration, real browser, and actual OpenBao service | Blocked for this lane |
| Live or production execution | Not run |

A fixed clock and the pin's fixture load a single scoped account at synthetic
intent revision 2. The authorized attempt observes exactly one data request,
two metadata requests, one helper invocation, and one sink call. Reusing the
ticket on both the same resolver and a new resolver within the process adds
zero calls. The wrong account, top-level origin, frame origin, session, lease
epoch, old revision, and missing or stale observations must make zero vault
requests and zero injection calls.

A redirect during data loading or metadata verification, revocation or expiry
during the read, version rotation, provider timeout, and provider redirect all
deny before the sink runs. The harness checks exact request routes and call
order against a separate ledger. It checks captured output and the formatted
denial, including exception chaining, for both token and secret canaries.
There is no runtime history store in this lane. A temporary source copy with
the freshness guard disabled must reach the effect ledger and fail the stale
observation case.

With Browser checked out at the composition gitlink, run from the repository
root with Python 3.13 or later.

```sh
python3 -I -B tools/browser_credential_hero.py
python3 -I -O -B tools/browser_credential_hero.py
python3 -B -m unittest discover -s tests -p test_browser_credential_hero.py
```

Each invocation repeats the full matrix in fresh isolated subprocesses and
compares the normalized outcomes. Each child has a 10-second deadline.
An audit hook records and rejects attempted socket and child-process activity.
The input and effect logs are confined to a temporary directory for the
campaign. The JSON receipt records the exact composition commit, seven pins,
lock and scenario hashes, Python runtime, and observed outcomes. A failed
Browser check exits nonzero. The aggregate H03 acceptance remains blocked.
The all-fake model lane, replay across processes with real Core admission,
and actual website credential injection require separate qualification.
