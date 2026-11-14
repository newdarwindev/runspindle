# Streaming development bundle v1

The separate `runspindle.streaming-development-bundle.v1` interface packages the
qualified offline development executable, selected refinery code and pinned
Python dependencies, platform installation helpers, source/toolchain inventories
and required notices. It implements the reproducibility obligations in
[desired intent](desired-intent.md). Metadata v1 validation and runtime, fixture,
lineage, evaluation and serving semantics remain unchanged.

The [descriptor](../contracts/streaming-development-bundle-v1.json) defines a
bounded uncompressed stream. Every regular file has an exact byte size, SHA256
and mode (0644 or 0755). The canonical manifest binds seven component revisions,
the composition revision, Linux arm64, exact dependency/toolchain inventories,
included license bytes and executable entrypoints. Its digest identifies a
candidate; checksums do not authenticate a third-party publisher or grant
execution authority. Unknown formats reject before installation.

Only owned disposable Linux arm64 targets support this implementation. Installers
retain a verified archive separately from a schema-versioned SQLite journal.
They commit immutable manifest/predecessor intent and advance an ownership
generation before copying. Recovery checks the retained payload, staged files,
installed files and actual version pointer. A verified predecessor must exist
with exact installed bytes before rollback; missing bytes are a blocker rather
than permission to reconstruct history. Competing owners, stale generations,
conflicting readback and failed rollback must preserve non-success.

Tests must interrupt fresh processes after intent, staging and pointer replacement
and after rollback intent, independently read installed bytes/modes, then execute
the installed development subset without external egress. This establishes only
bounded offline compatibility. Native, Tether, browser, console and production
adapters remain unsupported. Full-system acceptance stays blocked.

The user waived the independent-review gate for this offline tranche. That waiver
is standing authorization, not evidence that an independent review occurred.
