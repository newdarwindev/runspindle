import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('envelope_codec', ROOT/'conformance/envelope-v1/codec.py')
codec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(codec)


class Envelopes(unittest.TestCase):
    def setUp(self):
        self.vectors = json.loads((ROOT/'conformance/envelope-v1/vectors.json').read_text())

    def test_vectors_and_independent_component_mappings(self):
        for v in self.vectors:
            e = codec.decode(codec.encode(v['envelope']))
            self.assertEqual(codec.component(e), v['component'])

    def test_invalid_before_adapter(self):
        observed = []
        e = self.vectors[0]['envelope']
        invalid = []
        for key, value in [('version', 'unsupported'), ('message_type', 'unknown'), ('message_id', '-bad')]:
            x = copy.deepcopy(e); x[key] = value; invalid.append(json.dumps(x))
        for key in e:
            x = copy.deepcopy(e); del x[key]; invalid.append(json.dumps(x))
        x = copy.deepcopy(e); x['payload']['binding'] = e['binding']; invalid.append(json.dumps(x))
        for value in [0, -1, 1.0, True, 2**64]:
            x = copy.deepcopy(e); x['binding']['lease_epoch'] = value; invalid.append(json.dumps(x))
        invalid += [json.dumps(e)[:-1]+',"version":"runspindle.envelope.v1"}', json.dumps(e).replace('"revision": 1', '"revision": 1,"revision": 2')]
        for raw in invalid:
            with self.assertRaises((AssertionError, ValueError, TypeError)):
                codec.consume(raw, e['binding'], observed.append)
        self.assertEqual(observed, [])

    def test_stale_epoch_session_sequence_and_wrong_destination_zero_calls(self):
        calls = []
        for v in self.vectors:
            e = v['envelope']; expected = dict(e['binding'], lease_epoch=2)
            with self.assertRaises(AssertionError):
                codec.consume(codec.encode(e), expected, calls.append)
        e = self.vectors[1]['envelope']
        for args in [dict(session='wrong'), dict(session='session-1', last_sequence=1)]:
            with self.assertRaises(AssertionError):
                codec.consume(codec.encode(e), e['binding'], calls.append, **args)
        for v in self.vectors[2:4]:
            e = v['envelope']
            with self.assertRaises(AssertionError):
                codec.consume(codec.encode(e), e['binding'], calls.append, destination=('account-1','wrong'))
        self.assertEqual(calls, [])
