# Offline visual-release review rehearsal

From the repository root:

```sh
for case in matched changed-bytes missing-notice wrong-class; do
  python3 tests/test_synthetic_visual_release.py "$case" || exit
done
python3 -m unittest discover -s tests -p 'test_synthetic_visual_release.py' -v
```

The storyboard, screen pattern and deck are invented text stand-ins, not media
from an application. The fixture pins a digest, notice and evidence class for
each item. Mismatched bytes, missing notices and a storyboard relabeled as
actual UI evidence do not enter the mock allowlist. Missing, unknown or
duplicate items also stay out.

No capture, credentials, publication, uploads or network access is involved.
The resulting mock list is not a release approval. Real publication still
needs separately reviewed actual evidence, notices and explicit per-artifact
permission.
