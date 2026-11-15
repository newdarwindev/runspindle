# Bounded reported failure diagnostics

D07 verification receipts now include `reported_diagnostic` for failed child
processes. This is a hint from untrusted child output, **not a verified cause**.
Exit codes, mandatory checks, timeouts and aggregate decisions are unchanged.

The existing bounded output tail is inspected transiently, then discarded. The
parser retains only fixed categories for missing files, permission failures,
missing Python modules, assertions, subprocess failures and compiler failures.
Everything else is explicitly unclassified. Exception messages, traceback paths,
command arguments, environment values and raw output are never added to receipts.

A checker may emit one JSON line with exactly these fields:

    {"type":"verification_diagnostic","version":1,"stage":"target_preparation","code":"missing_seed"}

Stage/code combinations are a fixed vocabulary in `tools/hygiene.py`. The parser
rejects duplicate keys, extra fields, unknown values, lines over 512 characters,
and multiple valid envelopes. Parsing is limited to the last 64 lines of the
existing 64-KiB tail. Missing or discarded diagnostics do not change failure.
Even a syntactically valid forged report remains `child_output_unverified`.
Current checkers need not emit envelopes; a missing seed raised as Python
FileNotFoundError is reported only as missing_file, not a proven missing seed.

JSON receipts retain these bounded values. Markdown and existing CI failure
summaries render a revalidated `reported=... (unverified)` hint. No new artifact
upload, retention service, raw log capture, permissions or acceptance gate is
introduced. Child failure output still cannot authorize actions or retries.

## Partition pre-check failures

The partition entrypoint also reports a fixed `stage` and `category` when an
existing caught exception aborts before a receipt can be produced. Stages identify
manifest validation, instance/image metadata, image binding, each closure check,
source/run identity, check execution, aggregate input/validation or receipt output.
Categories distinguish invalid JSON/encoding/value, missing file/field, denied
file access, I/O failure or command failure. Unclassified caught failures remain
unclassified. These identify the rejecting code boundary, not an inferred machine
state or an authorization to repair it. No observed/expected metadata values,
paths, exception messages, commands or environment values are emitted.

Existing validation predicates, caught-exception scope and exit codes (0/1/2)
remain unchanged. Successful receipt schema/encoding is unchanged; failed
pre-checks emit no success receipt and never run child checks. Synthetic injection
tests cover every pre-check boundary, canary non-disclosure and receipt stability.
This does not establish the cause of an older run that lacked these diagnostics.

Image-binding failures retain `stage=image_binding`, `category=invalid_value` and
exit code 2. Their optional `binding_failures` list contains at most five fixed
`field:missing` or `field:mismatched` strings, ordered as `image_sha256`,
`image_source_sha`, `controller_sha256`, `recipe_sha256`, `tool_closure_sha256`.
Missing means the key is absent. Present nulls, invalid types and unequal values
are mismatches under the unchanged exact-equality gate. Unrelated metadata does
not affect that gate or appear in the hint. No value, arbitrary key, path or
exception chain is emitted. The output boundary rejects malformed, duplicate,
out-of-order or unknown hints while preserving the failed status. Synthetic
normal and optimized tests cover each field, hostile metadata, multiple failures,
final-boundary tampering and unchanged success behavior. These diagnostics do not
qualify a runner, alter image pins or explain historical failures without them.
