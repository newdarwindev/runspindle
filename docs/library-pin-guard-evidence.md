# Optimization-safe composition library pin guard

Partial offline composition #1/#2 work, based on
`da1094484973154e0869a136ebb7e3b8394331d6`. No component pin or runtime changed.

## Demonstrated defect and fix

The previous alignment checker used `assert` for its version, index and Cargo
checks. Python optimization removed these checks. Running the new wrong-revision
regression against the unchanged old checker demonstrated exit 0 under `-O`;
normal mode rejected the same mismatch.

The checker now uses explicit exceptions under both interpreter modes. It parses
Cargo.toml and Cargo.lock rather than treating comments or unrelated substrings
as dependency evidence. The selected package name, exact repository and revision,
unique lock package/source, fixed component paths, unique components and exact
stage-zero gitlinks must agree. Missing source checkouts remain blocked (78), not
passed. Malformed parser/input errors emit a fixed public category rather than
raw parser text; known validation failures retain bounded diagnostic labels.

Independent review identified that a Cargo `package` alias could still select a
different crate under the host dependency key. This was fixed and covered by
normal/optimized rejection of a wrong package and acceptance of explicit same-name
package selection.

## Bounded reproduction

Python 3.11+ is required for standard-library TOML parsing. With the existing pinned
Core/Host checkouts materialized:

```
python3 tools/check_library_pins.py
python3 -O tools/check_library_pins.py
python3 -m unittest discover -s tests -p 'test_library_pin*.py' -v
python3 -O -m unittest discover -s tests -p 'test_library_pin*.py' -v
```

Both real pinned structural checks passed. The 13 focused tests passed in normal
and optimized interpreter modes, including real disposable Git indexes, malformed
versions, duplicate entries, wrong revisions/repositories/packages, comment decoys,
missing source and sanitized parser failure. A deliberate removed-revision-guard
mutant must fail the independent exit-code assertion; compilation/parser failure
is not counted as successful mutation detection. Tests use synthetic metadata and
do not build or execute component packages.

## Limits

This establishes structural alignment, not Cargo resolution/build compatibility,
cleanliness of materialized sources, production authenticity or end-to-end
integration. Core/Host pins and other gitlinks are unchanged. There is no install,
service, provider, deployment, credential or permission change. Full shared-fixture
and composition acceptance remain separate; issues #1/#2 stay open. Static tooling
and CI are not qualified by these results.

## Full offline regression evidence

All 357 Python tests passed (Python 3.14.8) after explicit preparation of the
unchanged retained Tether/Refinery sources. The earlier run without those explicit
paths had 354 passing tests and three setup skips; it was not counted as complete.
The earlier minimal checkout had 19 missing-source errors, resolved by materializing
the existing pinned component sources without changing gitlinks. Scaffold and
artifact-integrity checks passed. No Rust build, Docker or live provider ran.

## Input SHA-256

- `tools/check_library_pins.py`: `7a90a51ae0688c2f05d6b82dfb8df3c0ccc05272232e92106aa3cc119da2f01e`
- `tests/test_library_pin_optimized.py`: `c4eb06c3f80cfd5953f35b4e12717ec83f9079c25f0ac6fa79d2227d250456eb`
