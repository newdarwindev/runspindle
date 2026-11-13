"""Rebuild the test-only fixture manifest; review its diff before upgrading pins."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'fixtures/v1'
files = ['artifact.txt', 'contract.json', 'faults.json', 'fixturekit.py', 'golden.json', 'vectors.json']
manifest = {
    'schema': 'runspindle.fixture.v1',
    'provenance': 'Original synthetic fixtures; no imported source, private data or real credentials.',
    'upstream_compatibility': 'provisional-not-qualified',
    'components': {
        'core': ['admission.observed', 'native.observed', 'artifact.observed'],
        'host': ['native.observed'],
        'browser': ['browser.observed'],
        'tether': ['admission.observed', 'event.observed', 'feedback.observed'],
        'refinery': ['feedback.observed', 'candidate.observed'],
        'console': ['native.observed', 'browser.observed', 'artifact.observed', 'telemetry.observed'],
        'platform': ['telemetry.observed', 'candidate.observed'],
    },
    'files': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files},
}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
