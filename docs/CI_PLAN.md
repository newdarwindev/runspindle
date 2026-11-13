# GitHub Actions plan

Every workflow uses isolated local self-hosted capacity. Enabled does not mean registered, online or passed. No public-fork triggers, scheduled jobs, paid calls or live deployment are introduced by these scaffolds.

| Repository | Workflow | Planned contents | Current implementation |
|---|---|---|---|
| runspindle | `contracts.yml` | Check specification inventory, source provenance and pinned submodule identities. | Scaffold structure only |
| runspindle | `system-test.yml` | Cross-component synthetic acceptance stories; not implemented. | Fails closed: blocked |
| runspindle | `distribution.yml` | Assemble verified pinned binaries/images, checksums, SBOM and install bundles; not implemented. | Fails closed: blocked |
| runspindle-core | `rust-ci.yml` | Structural checks, Rust fmt, offline unit/contract tests and offline clippy with warnings denied. | Configured for the in-memory contract model; GitHub execution not established |
| runspindle-core | `orchestration-test.yml` | Temporal retry/cancellation/replay and identity fixtures; not implemented. | Fails closed: blocked |
| runspindle-host | `host-ci.yml` | Linux and macOS native adapter checks; not implemented. | Scaffold structure only |
| runspindle-host | `adapter-test.yml` | Session launch/reconnect/lost acknowledgement and capture capability tests; not implemented. | Fails closed: blocked |
| runspindle-host | `host-package.yml` | Package signed or checksummed qualified native host binaries; not implemented. | Fails closed: blocked |
| runspindle-browser | `browser-ci.yml` | Credential reference, profile and command contract checks; not implemented. | Scaffold structure only |
| runspindle-browser | `gateway-test.yml` | Disposable OpenBao/PinchTab/KasmVNC origin, lease and handoff fixtures; not implemented. | Fails closed: blocked |
| runspindle-tether | `tether-ci.yml` | Existing Tether parser/transport compatibility checks; source port not performed. | Scaffold structure only |
| runspindle-tether | `mirror-test.yml` | Fake Slack event, duplicate/retry/edit and masking tests; not implemented. | Fails closed: blocked |
| runspindle-refinery | `refinery-ci.yml` | Python and Rust interface, feedback provenance and conflict checks; not implemented. | Scaffold structure only |
| runspindle-refinery | `evaluation.yml` | Locked synthetic offline evaluation and exact candidate rollback tests; not implemented. No paid calls. | Fails closed: blocked |
| runspindle-console | `console-ci.yml` | Type, unit, accessibility and stale/offline-state checks; not implemented. | Scaffold structure only |
| runspindle-console | `console-build.yml` | Production UI build after implementation; not implemented. | Fails closed: blocked |
| runspindle-platform | `platform-ci.yml` | Manifest, dependency digest, license and install validation; not implemented. | Scaffold structure only |
| runspindle-platform | `dev-smoke.yml` | Disposable integrated local development smoke; not implemented. | Fails closed: blocked |
| runspindle-platform | `deploy.yml` | Manual target-specific deployment and rollback after independent acceptance; blocked. | Fails closed: blocked |

Initial lane: `self-hosted, linux, x64, runspindle-isolated`. Native macOS checks require a separately qualified isolated macOS lane and are not silently represented by Linux checks.

Production has no verified target, pinned release, qualified runner or rollout receipt. The deployment workflow does not deploy anything.

Pinned checkout: actions/checkout v4.2.2 commit 11bd71901bbe5b1630ceea73d27597364c9af683.
