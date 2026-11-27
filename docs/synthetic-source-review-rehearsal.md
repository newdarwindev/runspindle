# Offline source import review rehearsal

From the repository root:

```sh
for case in allowed conflicting-grant missing-notice wrong-destination wrong-use; do
  python3 tests/test_synthetic_source_review.py "$case" || exit
done
python3 -m unittest discover -s tests -p 'test_synthetic_source_review.py' -v
```

All paths, grants, uses and notices are invented. Each fixture request gets an
explicit decision for its exact source, destination and intended use. An
allow record does not override a matching contradictory grant or waive a
required notice, even if the request says the destination already has bytes.
Wrong destinations and uses stay outside the mock allowlist.

The rehearsal reads only the local invented records and does not examine or
copy actual source files. It makes no legal conclusion. Actual import still
needs reviewed rights and licenses, permission for the exact scope,
attribution and notice evidence, and explicit treatment of exclusions.
