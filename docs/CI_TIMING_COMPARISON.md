# Offline CI timing comparison

This tool reports **observed elapsed differences**, not causal cache savings,
queue reduction, runner qualification, or evidence that any gate passed in
another run. It does not read job logs, connect to GitHub, execute a test, restore
a cache, or modify a workflow.

Use two independently captured, successful GitHub Actions job records from the
Jobs REST API. The jobs must use the same exact source SHA, repository, job
name and reviewed runner recipe. Capture only the job metadata, not raw logs
or environment exports. Wrap each job in a JSON object with:

- `repository`: the canonical GitHub owner/repository name.
- `runner_recipe_sha256`: the SHA-256 of the same reviewed recipe identifier,
  binding runner image/toolchain, checkout policy, isolation and cache policy.
  This is a caller assertion, not attestation; cold/warm runtime state is the
  only intended difference. Carry the recipe and sample provenance separately.
- `cache_state`: `cold` in the first receipt, `warm` in the second.
- `job`: one Jobs REST record with numeric `id` and `run_id`, full `head_sha`,
  name, status/conclusion, UTC start/end timestamps and the step records.

Run `python3 tools/compare_ci_timings.py cold.json warm.json`. The report contains
only fixed phase labels and verified-shape identifiers and integer durations.
Negative differences are retained. Missing timestamp or work step, mismatched
phase list, unsuccessful job, and reused run/job IDs are rejected. A connector
summary without timing metadata is not the required input.

Scope: supported component, quality and Rust job names and exact step labels
listed in the source. Checkout/staging and actual validation are separate;
unrecognized steps are not silently counted as cache savings. Runner waiting
time is excluded. Auth/mutation shards and empty-partition attestations are
not comparison inputs in this slice; never treat their success as work done.
Synthetic unit tests do not provide a measured result on Strix. To estimate
savings, repeat matched pairs on the same runner recipe and report the spread
plus the critical path separately from total job seconds.
