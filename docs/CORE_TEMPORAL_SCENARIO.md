# One real core with Temporal

The `core-temporal-pinned-recovery-v1` lane exercises the implemented Rust core
worker/client and the real Temporal development database. Host launch/discovery/
cancellation are scripted activity ports with a separately fsynced peer ledger.
Browser, delivery, provider, refinery and console operations are **not exercised**;
this lane does not qualify those adapters. The manifest records these boundaries
and keeps all required system gates blocked/not-run.

## Preparation and offline run

Use the exact committed Linux arm64 pins, Docker with isolated gateway support,
Python 3.11+ and Cargo for preparation. Do not select another version or service
when a prerequisite is missing. See the pinned component instructions in
[platform](../components/platform/docs/TEMPORAL_LANE.md) and
[core](../components/core/docs/TEMPORAL_RUNTIME.md).

Preparation can acquire dependencies and records artifact/license checksums:

```sh
python3 components/platform/tools/temporal_lane.py prepare --directory local/temporal-prepared
python3 components/core/tools/prepare_temporal_runtime.py --acquire
```

Prepared runs never download dependencies. Extract the exact `image_id` from
`components/core/docs/runtime-build.json` and supply it explicitly:

```sh
python3 tools/core_temporal_scenario.py \
  --platform-prepared local/temporal-prepared \
  --core-image sha256:<image_id_from_pinned_core_build_record> \
  --report local/core-temporal-report.json
```

The driver checks all seven checkout/index/lock pins and hashes source, contract,
fixtures and fault configurations. It checks the image against committed core
build evidence, exact source/lock/dependency hashes and image labels, then copies
and hashes executable bytes without running the unverified image. The platform
source is executed from its exact verified bytes; untracked bytecode cannot
replace it. Platform preparation is independently revalidated before execution.

A disposable internal Docker network, read-only containers, per-run database
volume and synthetic effects directory are removed on exit. The prepared download,
build and image cache remains for offline reuse. Tests expose no host service
ports and use no account credentials, live provider or paid calls.

## Observations and limits

The driver independently asserts concurrent duplicate admission returns one job;
conflicting delivery and active supersession reject; an offline host causes zero
launches; a peer accepts one launch and the worker exits before its reply; fresh
worker and server processes reconcile the same operation/session from the same
real database; a stale cancellation binding rejects; cancellation acknowledgement
is not terminal; and observed cancellation is preserved. It asserts one launch,
one cancellation call, call order, exact binding/session receipts and no activity
calls during real history replay. SDK logs alone cannot satisfy these assertions.

The report stores exact component commits, images, toolchain/dependency/config
hashes, raw synthetic observations, normalized outcome hash and independent
cleanup readbacks. Repeat the command into another report: normalized outcome
hashes must agree, while timestamps, process IDs and read-only poll counts may vary.
Oracle tests deliberately alter session/epoch/host, duplicate effects, call order,
unknown state, cancellation state and replay call counts and must fail.

A successful development lane reports `real_core_lane=passed` and
`aggregate=blocked`: full-system/native/browser/delivery/telemetry/serving/live
requirements remain incomplete. The command therefore returns **78**; a failed
assertion returns **1**. Missing/incompatible prerequisites are blocked, never
passed by scaffold success. This is bounded development persistence evidence,
not production durability, browser fencing or completed issue #2 acceptance.

The [recorded two-run evidence](core-temporal-scenario-evidence.json) has matching
normalized outcomes, source pins, image/toolchain bindings and all staged script
hashes. Both real-core lanes passed and returned 78 for the blocked system
aggregate. The unrelated-image negative control also returned blocked/78 before
execution. Twenty-nine composition tests cover the oracle and setup regressions.
