"""Independent conformance oracles for the provisional synthetic fixture kit."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'fixtures/v1'
spec = importlib.util.spec_from_file_location('fixturekit', BUNDLE / 'fixturekit.py')
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.golden = kit.load_json(BUNDLE / 'golden.json')

    def oracle(self, fixture):
        result = {fixture['state']: {'identity': fixture['identity'], 'detail': fixture['detail']}}
        if fixture['kind'] == 'artifact.observed':
            result['accepted_digest'] = hashlib.sha256((BUNDLE / 'artifact.txt').read_bytes()).hexdigest()
        if fixture['kind'] == 'candidate.observed':
            result['approved_digest'] = hashlib.sha256(b'Synthetic candidate v1').hexdigest()
        return result

    def assertRejected(self, code, callback):
        with self.assertRaises(kit.ContractError) as context:
            callback()
        self.assertEqual(str(context.exception), code)

    def test_bundle_integrity_and_exact_artifact_bytes(self):
        kit.verify_bundle(BUNDLE)
        artifact = next(x for x in self.golden if x['kind'] == 'artifact.observed')
        self.assertEqual(artifact['identity']['artifact_digest'], hashlib.sha256(b'Synthetic Runspindle artifact. No private content.\n').hexdigest())

    def test_all_boundary_golden_oracles(self):
        self.assertEqual(len(self.golden), 8)
        for fixture in self.golden:
            with self.subTest(kind=fixture['kind']):
                self.assertTrue(kit.assert_conforms(fixture, fixture['identity'], fixture['state'], self.oracle(fixture)))

    def test_published_mutations_fail_independent_oracle(self):
        for vector in kit.load_json(BUNDLE / 'vectors.json'):
            original = next(x for x in self.golden if x['kind'] == vector['kind'])
            broken = copy.deepcopy(original)
            target = broken
            path = vector['mutation']['path']
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = vector['mutation']['value']
            with self.subTest(vector=vector['id']):
                self.assertRejected(vector['expected_error'], lambda: kit.assert_conforms(broken, original['identity'], original['state'], self.oracle(original)))

    def test_required_identity_and_extra_data_rejected(self):
        for original in self.golden:
            for name in original['identity']:
                broken = copy.deepcopy(original)
                del broken['identity'][name]
                with self.subTest(kind=original['kind'], missing=name):
                    self.assertRejected('required-keys', lambda: kit.validate(broken))
            for section in ['identity', 'detail', None]:
                broken = copy.deepcopy(original)
                target = broken if section is None else broken[section]
                target['secret'] = 'synthetic-canary-do-not-emit'
                with self.subTest(kind=original['kind'], section=section):
                    self.assertRejected('unknown-key', lambda: kit.validate(broken))

    def test_invalid_identity_combinations(self):
        envelope = copy.deepcopy(self.golden[0])
        envelope['identity']['lease_epoch'] = 1
        self.assertRejected('unknown-key', lambda: kit.validate(envelope))

    def test_bool_negative_and_oversized_integer_rejected(self):
        envelope = next(x for x in self.golden if x['kind'] == 'browser.observed')
        for key in ['intent_revision', 'policy_revision', 'lease_epoch', 'attempt', 'sequence']:
            for bad in [True, False, -1, 2**53, 1.0, '1', None]:
                broken = copy.deepcopy(envelope)
                broken['identity'][key] = bad
                with self.subTest(key=key, bad=bad):
                    self.assertRejected('field-type-or-bound', lambda: kit.validate(broken))
        for key in ['intent_revision', 'policy_revision', 'lease_epoch', 'attempt']:
            broken = copy.deepcopy(envelope)
            broken['identity'][key] = 0
            self.assertRejected('field-type-or-bound', lambda: kit.validate(broken))

    def test_id_bounds_and_origin_restriction(self):
        for bad in ['', 'a'*129, 'white space', 'line\nbreak', '🧪']:
            broken = copy.deepcopy(self.golden[0])
            broken['identity']['task_id'] = bad
            self.assertRejected('field-type-or-bound', lambda: kit.validate(broken))
        for bad in ['https://site.example.evil', 'https://user:secret@site.example', 'http://site.example', 'https://site.example/path']:
            broken = copy.deepcopy(self.golden[2])
            broken['detail']['top_origin'] = bad
            self.assertRejected('field-type-or-bound', lambda: kit.validate(broken))

    def test_unknown_events_versions_states_and_timestamp(self):
        for key, value, code in [('kind','future.event','unknown-event'),('schema','runspindle.fixture.v2','schema-version'),('state','made-up','state'),('status',[],'status'),('state',{},'state'),('observed_at','2026-99-31T00:00:00Z','field-type-or-bound'),('observed_at',None,'field-type-or-bound'),('evidence_class','live_acceptance','evidence-class')]:
            broken = copy.deepcopy(self.golden[0]);broken[key] = value
            self.assertRejected(code, lambda: kit.validate(broken))

    def test_serialization_and_message_bounds(self):
        broken = copy.deepcopy(self.golden[0]);broken['detail']['action'] = 'a'*70000
        self.assertRejected('size',lambda:kit.validate(broken))
        broken['detail']['action'] = float('nan')
        self.assertRejected('serialization',lambda:kit.validate(broken))

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'duplicate.json';path.write_text('{"schema":1,"schema":2}')
            self.assertRejected('duplicate-key',lambda:kit.load_json(path))

    def test_fabricated_receipts_not_accepted(self):
        for envelope in self.golden:
            if envelope['state'] in ['delivered','persisted','serving']:
                self.assertRejected('missing-independent-receipt',lambda:kit.assert_conforms(envelope,envelope['identity'],envelope['state']))
        artifact = self.golden[4]
        observations = self.oracle(artifact);observations['accepted_digest'] = '0'*64
        self.assertRejected('unaccepted-bytes',lambda:kit.assert_conforms(artifact,artifact['identity'],'delivered',observations))
        candidate = self.golden[7]
        observations = self.oracle(candidate);observations['approved_digest'] = '0'*64
        self.assertRejected('unapproved-candidate',lambda:kit.assert_conforms(candidate,candidate['identity'],'serving',observations))

    def test_incomplete_required_lanes_fail_closed(self):
        for status in ['not-run','failed','blocked','unknown']:
            self.assertEqual(kit.aggregate(['passed',status]),'blocked')
        self.assertEqual(kit.aggregate(['passed','passed']),'passed')
        self.assertRejected('status',lambda:kit.aggregate([]))
        self.assertRejected('status',lambda:kit.aggregate(['invented']))

    def test_bundle_tampering_and_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory)/'bundle';shutil.copytree(BUNDLE,copied,ignore=shutil.ignore_patterns('__pycache__'))
            (copied/'artifact.txt').write_bytes(b'altered bytes')
            self.assertRejected('bundle-digest',lambda:kit.verify_bundle(copied))
            shutil.copyfile(BUNDLE/'artifact.txt',copied/'artifact.txt')
            (copied/'unexpected.txt').write_text('synthetic extra')
            self.assertRejected('bundle-inventory',lambda:kit.verify_bundle(copied))

    def test_all_consumers_export_without_siblings_and_verify_in_fresh_process(self):
        with tempfile.TemporaryDirectory() as directory:
            for component in ['core','host','browser','tether','refinery','console','platform']:
                destination = Path(directory)/component
                result = kit.export_bundle(component,destination)
                self.assertEqual(result['origin_manifest_sha256'],hashlib.sha256((BUNDLE/'manifest.json').read_bytes()).hexdigest())
                process = subprocess.run([sys.executable,str(destination/'fixturekit.py')],cwd=directory,timeout=10,capture_output=True,text=True)
                self.assertEqual(process.returncode,0,process.stderr)
                fixtures = kit.load_json(destination/'golden.json')
                self.assertTrue(fixtures)
                allowed = kit.load_json(BUNDLE/'manifest.json')['components'][component]
                self.assertTrue(all(x['kind'] in allowed for x in fixtures))
                self.assertTrue(kit.load_json(destination/'vectors.json'))
                repeated = Path(directory)/(component+'-repeat')
                kit.export_bundle(component,repeated)
                self.assertEqual({p.name:p.read_bytes() for p in destination.iterdir()}, {p.name:p.read_bytes() for p in repeated.iterdir()})

    def test_export_never_overwrites_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory)/'marker';marker.write_text('keep')
            with self.assertRaises(FileExistsError):
                kit.export_bundle('core',directory)
            self.assertEqual(marker.read_text(),'keep')

    def test_clock_ids_spy_reset_and_cleanup_after_failure(self):
        a,b=kit.Ids(90210),kit.Ids(90210)
        self.assertEqual([a.next() for _ in range(8)],[b.next() for _ in range(8)])
        clock=kit.Clock();clock.advance(5);self.assertEqual(clock.seconds,5)
        spy=kit.Spy(['reconcile']);spy.call('reconcile',{'operation_id':'synthetic-op'})
        self.assertRejected('forbidden-call',lambda:spy.call('send',{'operation_id':'synthetic-op'}))
        self.assertEqual([call[0] for call in spy.calls],['reconcile','send'])
        self.assertEqual(kit.Spy().calls,[])
        path=None
        with self.assertRaises(RuntimeError):
            with kit.temporary_store() as path:
                (path/'fixture').write_text('synthetic')
                raise RuntimeError('injected failure')
        self.assertFalse(path.exists())

    def test_fault_inventory_covers_required_boundaries(self):
        faults=kit.load_json(BUNDLE/'faults.json')
        self.assertEqual({x['id'] for x in faults['cases']},{'duplicate','reorder','timeout','partial-response','retry','restart','uncertain-effect'})
        self.assertEqual(faults['classification'],'model_schedule_not_runtime_recovery')


if __name__ == '__main__':
    unittest.main()
