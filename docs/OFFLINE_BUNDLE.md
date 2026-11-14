# Runnable offline development bundle

This bundle supports the tested Linux arm64 development subset: core immutable
artifact storage and denial checks, refinery durable lineage and cumulative
budgets, pinned DSPy with a synthetic local LM, exact candidate serving readback,
interrupted upgrade recovery and rollback. Native, Tether, browser, console,
providers and production services are unsupported. Full-system acceptance remains
blocked. Independent review was user-waived for this tranche; no review occurred.

The streaming v1 contract is separate from the existing JSON metadata format.
Its manifest pins all seven component revisions, the composition revision,
executable and dependency bytes, toolchains, notices, Linux arm64, entrypoints,
file sizes, modes and SHA256 values. The bundle is uncompressed and bounded.
Unsupported versions, traversal, unsafe links/modes, mismatched pins/target,
changed/incomplete/trailing payloads and missing notices fail before activation.
A checksum establishes artifact identity, not an execution grant or publisher
signature.

After explicit preparation of the exact core runtime image and refinery dependency
cache, run the composition qualification command (from this repository):

```sh
python3.13 tools/maintained_scenarios.py \
  --manifest specs/maintained-scenarios-v1.json \
  --core-prepared /path/to/qualified/core/local/runtime-prepared \
  --report local/maintained-report.json \
  --artifacts local/offline-development-bundle
```

Candidate qualification can use explicit `--component name=/clean/worktree`
overrides. Each source must match the manifest's exact revision, extend its
recorded base and be clean. The driver validates the actual prepared core image,
extracted executable and dependency inventory before packaging. Executable code,
source records and required notices are included; no selected legacy history or
unselected source files are imported. Preparation is separate from execution.
This command deliberately exits 78 while required full-system gates are blocked,
even when the bounded H10/H11/H12 lanes pass.

The saved artifact directory contains `baseline.stream`, `upgrade.stream`, exact
manifest/pin input, a byte-bound bootstrap and `run.py`. Copy the entire directory
to a host with Python, Docker and the already-loaded exact runtime image:

```text
python@sha256:0e58fc4a4575979bfce26735236422a48b38dae99d72b9d72a15e8e3fe0f7f93
```

Then run inside that directory:

```sh
python3 run.py --artifacts .
```

This saved launcher needs no component checkout, compiler, dependency cache,
credentials or network acquisition. It checks bootstrap/launcher bytes against
the bundled manifest before launching a disposable Linux arm64 container with
`--pull never`, denied network, a read-only root, dropped capabilities, bounded
CPU/memory/processes and an executable temporary target. It installs and verifies
all bytes/modes, executes the installed core and packaged refinery/dependencies,
kills a fresh upgrade process after staging, recovers from the retained archive,
interrupts rollback after durable intent, and recovers the exact predecessor.
Independent filesystem hashes, SQL call order and serving bytes establish the
bounded result. Targets and containers are removed on completion or failure.
No daemon, service registration, host enrollment or production installation is
included. Power loss and hostile concurrent filesystem modification remain
unqualified.

H08 remains blocked. The selected Langfuse release and dependencies are retained;
the official MinIO source fallback has 256 exact module archive/mod hashes and
notice evidence. A complete original `go-localereader v0.0.1` notice is unresolved,
so its build and all Langfuse service execution/API readback remain blocked. File
exporter and durable Collector queue diagnostics remain separate evidence.
