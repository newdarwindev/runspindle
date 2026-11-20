# H04 Browser profile recovery and forgetting

[Composition #11](https://github.com/newdarwindev/runspindle/issues/11) and
[#45](https://github.com/newdarwindev/runspindle/issues/45).

The Browser-only lane exercises the pinned `MaterializedStore`,
`DirectoryProfileIO`, profile custody, AES-GCM encryption, credential
`Resolver` and OpenBao `Vault` adapter. SQLite, filesystem effects and new
Python processes are real. Grants, observations, provider replies and the
credential injection sink use public synthetic fixtures. Browser automation,
actual OpenBao deletion, website session revocation and joint Core authority
remain open.

| Stage | Independent observation |
| --- | --- |
| Concurrent account isolation | The owner reaches a private write before the competing account attempts admission. The rival is denied and adds zero directory preparations, key fetches, or materializations. A same-epoch request from a different native owner is also denied before profile IO. |
| Interrupted restore | The owner stops at the private write. The durable restore stays unknown. The canary scan detects the interrupted staging residue. A fresh process reconciles the previous exact generation and removes staging without another custody fetch or plaintext consumption. |
| Bad ciphertext | A separate SQLite writer flips one byte. A fresh restore reaches the pinned crypto path with zero plaintext-sink calls and retains the previous exact generation. After restoring the original checkpoint bytes, a distinct fresh grant materializes exactly once. |
| Expiry and outage | Expired authority reaches no adapter. A synthetic provider outage reaches the fetch boundary and produces zero issued leases or plaintext calls. |
| Credential boundary | The profile grant fails before the credential provider. A separate grant performs one synthetic injection. After simulated provider-side credential deletion, the adapter denies use. A separate SQLite read shows the same encrypted profile checkpoint, and the profile ledger shows zero effects from the credential path. |
| Profile boundary | A separate forget removes the profile checkpoint, leaves a durable tombstone, and clears discoverable test canaries. A fresh restore is denied before profile IO or custody. No website endpoint participates. |

A deliberate mutation drops the ciphertext tombstone write from a disposable
copy of the exact pinned source. An independent SQLite read rejects the result
even though directory cleanup reported success. Temporary store files, stage
copies and parent-owned worker processes are bounded and cleaned up. The
interruption is a process stop. File scans cover discoverable raw and encoded
canaries in the disposable directory.

## Reproduce

Use a clean checkout with the Browser submodule already prepared at the
composition gitlink. The tool compares all seven index gitlinks to
`composition.lock.json`, verifies the Browser checkout and stages only the
files and digests in [the scenario manifest](../scenarios/browser-profile-v1.json).
It runs each campaign twice with the same operation IDs and clock, compares the
normalized receipts, and then runs the deliberate mutation. Python workers
deny sockets and additional process operations through a local audit hook.

```sh
python3.15 -B tools/browser_profile_hero.py
python3.15 -B -O tools/browser_profile_hero.py
python3.13 -B -m unittest discover -s tests -p test_browser_profile_hero.py
```

Local evidence used the available macOS arm64 development closure, with
CPython 3.15.2, SQLite 3.54.1, cryptography 50.0.2, cffi 2.1.1 and pycparser
3.12. The preferred Linux x86-64 wheel closure in the Browser pin specifies
pycparser 3.0 and has no result for this H04 lane. Missing crypto prerequisites
produce a blocked receipt and a nonzero exit. No assets are downloaded by the
harness.

The report binds the composition revision, all component pins, scenario,
harness and selected source hashes. The Browser result applies to the
standalone component lane. H04 system acceptance remains blocked pending
Core-only and joint integration lanes. Live acceptance remains not run.
