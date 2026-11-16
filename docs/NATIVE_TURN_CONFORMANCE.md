# Bounded native-turn conformance

Issue: [composition #43](https://github.com/newdarwindev/runspindle/issues/43).
Base: `bd8aa7465ac0176df061bb5c0c7ef146e43e6cee` (public main verified before coding).
This is original source-only contract and independent synthetic mapping evidence.
No component pin, historical envelope, Admission grant, runner, credentials,
input store or operational permission is changed.

## Entrypoints and observations

`conformance/native-turn-v1/native_turn.py` provides `produce`, `decode`, `encode`,
`native_params`, `rpc_bytes` and the default-deny synthetic `consume` seam. It
imports no component serializer. `vectors.json` independently fixes three exact
request/UTF-8/canonical-digest/upstream-RPC examples, including non-normalized
Unicode, escaped controls and maximum-u64 revision/epoch values. Expected vectors
were constructed with stdlib JSON/hashlib, not the producer under test.

The independent adapter-call ledger observes actual emitted callback bytes.
Negative tests require zero calls for missing/extra/duplicate fields at every
depth, noncanonical JSON, unknown versions/profiles, invalid scalar/counter
aliases, every mismatched binding field, wrong thread, absent/false/changed
exact-request authority, changed model/content address, mismatched input bytes
and escaped RPC size overflow. An independent size calculation covers exact
4096-byte acceptance and 4097-byte rejection, including the final newline.

Three deliberately changed in-memory implementations demonstrate test sensitivity:
substituting task ID for thread ID breaks the independent expected RPC; removing
both authority checks produces a forbidden adapter call; removing content-hash
verification allows wrong bytes and produces a forbidden call. Repository source
is not mutated during these tests. The same checks run under optimized Python.
The default verifier never grants authority; test callbacks are synthetic trusted
code, not production authentication.

## Reproduction and results

On a prepared isolated local runner, the bounded dependency-free command is:

```sh
python3 -B -m unittest discover -s tests -p 'test_native_turn.py' -v
```

Observed on CPython 3.12.14:

- Native-turn focused suite: **13 tests passed**, including optimized subprocess
  coverage and all three deliberate mutation observations.
- Existing envelope regression suite: **18 tests passed**.
- Scaffold/artifact-integrity and repository-hygiene checks: **passed**.
- Targeted Ruff 0.14.5 lint/format and mypy 1.18.2 strict checks: **passed**.
- Full repository static-quality gate: **passed**, 0 new diagnostics, 462 existing
  baseline diagnostics. Its required Refinery import source was the verified clean
  existing workflow pin `b68ba9d77d51ca453b3f0fa3a9fa31573d065250`.
- Full Python suite after preparing the unchanged source/history prerequisites:
  **301 tests passed, no skips**. The first unprepared run had 21 errors from
  missing pinned component source and 3 feedback skips; the second had one
  ancestry-guard error because the composition checkout was shallow. Fetching
  the existing history and pins resolved prerequisites; no guards were changed.
  The previously blocked feedback suite also passed all 8 tests separately.
- Rust compilation/cross-language vectors: **not run** in this cloud environment,
  which has no Rust toolchain. Vectors are supplied for separate pinned Host lane
  qualification; no toolchain installation or native execution was attempted.
- Full aggregate `tools/validate.py`, isolated-runner/CI qualification, installed
  native binary, live provider, production authority/input store, durability and
  full-system acceptance: **not run / not inferred** by this tranche.

Full Python reproduction also requires existing composition submodules and the
exact clean feedback dependencies configured by `.github/workflows/validation.yml`:
Tether `670989839a0fccbcf2014d01609778ae6e4df424` and Refinery
`b68ba9d77d51ca453b3f0fa3a9fa31573d065250`. Static-quality needs that Refinery
checkout on `MYPYPATH`. No dependency version or source pin was updated.

Reviewed candidate source hashes:

- `conformance/native-turn-v1/native_turn.py`: `20c46b14f3c86b83b66475efb029095b122d8cd686ca1aaef0d059a84f93bb6e`
- `conformance/native-turn-v1/vectors.json`: `04cefda4aba43f8c2616ade76a5a0994804eda69e9ce45ca1f4e9117a465634c`
- `tests/test_native_turn.py`: `831ce1a9efca6ebb349e5a4a78da894d9a61a3a714819a3bcc250256544ca7c7`
- `contracts/native-turn-v1.json`: `258bb383758c73d36c239b4aafacfca6bfb0502d74641868f3f88b4d5a969ae8`
- `specs/native-turn-v1.md`: `48cafc109c86f1b0a7d13a3155a82c03c094d068da263c5ca03aa185f51c4301`

The candidate commit/tree is reported separately. Independent final-tree review
and remote CI remain pending. Issue #43 and its parent stay open for the broader
runtime, authority and lifecycle criteria.

## Explicit unsupported boundaries

The upstream source schema pin is recorded in the descriptor/spec. Matching that
schema is not proof of installed-binary/source correspondence. Model, approval
and sandbox overrides persist to subsequent turns. Omitted plugin controls can
inherit tools/plugins and thread history/instructions. `turn/start` can steer an
already-active turn; returned identity is not proof of a new turn or completion.
The profile constrains input/mapped policy, not the entire environment.

The Python consumer is stateless and invokes only the injected observation seam.
It has no owner-fenced durable reservation, replay protection, storage or native
transport. It must not substitute for Host dispatch. Host's implementation and
its independent review/tests remain separate, including authority immediately
before input access, dispatch, unforgeable submission capability and uncertain
outcome handling. Task-terminal/cancel-result mapping remains unsupported.
No activation or tool-isolation claim follows from these synthetic results.
