# Required CI document renderer

Status: code-only prerequisite; runtime qualification and CI success remain pending.
The validation workflow now names `/opt/runspindle-documents/bin/python` explicitly
for the renderer preflight and implemented-validation command. There is no install,
interpreter search, hosted fallback, skip or `continue-on-error` path. The existing
isolated Strix labels, feedback candidate lane, component pins and all acceptance
gates are unchanged. On the old image the new path remains unavailable and CI fails.

`tools/check_document_runtime.py` requires Linux x86_64 CPython **3.12.3** and exact
ReportLab **4.4.9**, Pillow **13.0.0**, charset-normalizer **3.5.2** versions. It also
requires a matching document-closure receipt in the environment and image manifest.
The pinned closure SHA-256 is
`7cfe6b9eb076efb723cb7e986c9429ace15eebc7ab6e3536d3fbce8c3aa72b7d`.
Its source contract is `fleet/document-closure.json` in the companion Platform
prerequisite. The preflight checks configuration consistency; it does not by itself
prove isolation, qualify a candidate image or grant deployment authority.

The existing `tests/test_marketing_vision.py` mandatory renderer test is unchanged:
it generates twice into a disposable copy and requires every output to retain its
original bytes. `tools/validate.py` propagates the explicit interpreter through
`sys.executable`. No generated document, notice, source mirror or manifest is updated
by this patch.

The artifact baseline uses CPython **3.12.14**, with the same package versions.
The exact CPython **3.12.3** renderer comparison has **not run**. Identical package
versions are not proof of old/new image or cross-Python byte equivalence. Qualification
must run the existing generator tests and full root validation against untouched
artifacts on the actual candidate. A mismatch blocks qualification and must be
investigated, not accepted by regenerating artifacts or weakening the test.

Wheel staging/installation, image builds, candidate guest qualification, fleet
manager/service/network operations, runner registration, CI dispatch and image
promotion are outside this code-only change and require the applicable separate
authorization. The companion Platform code must be reviewed and the exact resulting
image independently qualified before these workflow changes can make CI pass.

[Local source validation record](document-renderer-validation.json) separates
existing-environment checks from all pending runtime qualification.
