"""Independent evidence oracle mutations; these are synthetic contract evidence."""
import copy
import types
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
source = ROOT / 'tools/core_temporal_scenario.py'
scenario = types.ModuleType('core_scenario')
scenario.__file__ = str(source)
exec(compile(source.read_bytes(), str(source), 'exec'), scenario.__dict__)


class ScenarioOracle(unittest.TestCase):
    def setUp(self):
        self.admission = {'task_id': 'task-17', 'revision': 1, 'operation_id': 'operation-17',
                          'policy_revision': 'policy-17', 'host_id': 'host-17',
                          'workspace_id': 'workspace-17', 'lease_epoch': 1}
        import hashlib
        job = 'job-' + hashlib.sha256(b'task-17\n1').hexdigest()
        binding = scenario.binding(self.admission)
        recovered = {'binding': binding, 'state': 'acknowledged', 'cancellation': 'not_requested',
                     'native_session_id': 'observed-native-17'}
        terminal = dict(recovered, state='observed_cancelled', cancellation='observed_terminal')
        calls = [{'admission': self.admission, 'action': action, 'native_session_id': session}
                 for action, session in [('observe_host', None), ('launch', None),
                                         ('discover', None), ('cancel', 'observed-native-17')]]
        self.good = {'admission_replies': [{'status': 'admitted', 'job_id': job},
                                          {'status': 'duplicate_delivery', 'job_id': job}],
                     'offline_launch_count': 0, 'conflict': {'status': 'delivery_conflict'},
                     'active_revision': {'status': 'predecessor_active'}, 'worker_exit': 93,
                     'duplicate_after_restart': {'status': 'duplicate_delivery', 'job_id': job},
                     'recovered': recovered, 'wrong_cancel': {'accepted': False},
                     'cancel': {'accepted': True}, 'cancel_acknowledged': dict(recovered, cancellation='acknowledged'),
                     'terminal': terminal, 'calls': calls,
                     'effect_receipts': [{'binding': binding, 'native_session_id': 'observed-native-17'}],
                     'replay': {'status': 'passed'}, 'calls_after_replay': len(calls)}

    def test_synthetic_oracle_accepts_complete_observations(self):
        self.assertEqual(scenario.assert_observations(self.good, self.admission)['launch_calls'], 1)

    def test_second_launch_and_offline_effect_are_detected(self):
        for mutate in (lambda o: o['calls'].append(copy.deepcopy(o['calls'][1])),
                       lambda o: o.update(offline_launch_count=1)):
            bad = copy.deepcopy(self.good)
            mutate(bad)
            with self.assertRaises(AssertionError):
                scenario.assert_observations(bad, self.admission)

    def test_binding_session_receipt_and_order_mutations_are_detected(self):
        for mutate in (lambda o: o['recovered']['binding'].update(lease_epoch=2),
                       lambda o: o['effect_receipts'][0].update(native_session_id='fabricated'),
                       lambda o: o['calls'].reverse(),
                       lambda o: o['calls'][1]['admission'].update(host_id='alternate-host')):
            bad = copy.deepcopy(self.good)
            mutate(bad)
            with self.assertRaises(AssertionError):
                scenario.assert_observations(bad, self.admission)

    def test_unknown_and_acknowledgement_cannot_be_terminal_success(self):
        for mutate in (lambda o: o['terminal'].update(state='unknown'),
                       lambda o: o['cancel_acknowledged'].update(state='observed_cancelled'),
                       lambda o: o.update(wrong_cancel={'accepted': True})):
            bad = copy.deepcopy(self.good)
            mutate(bad)
            with self.assertRaises(AssertionError):
                scenario.assert_observations(bad, self.admission)

    def test_replay_cannot_create_external_effect(self):
        bad = copy.deepcopy(self.good)
        bad['calls_after_replay'] += 1
        with self.assertRaises(AssertionError):
            scenario.assert_observations(bad, self.admission)

    def test_required_unavailable_system_gates_are_non_success(self):
        for state in ('blocked', 'not_run', 'unknown'):
            self.assertEqual(scenario.aggregate('passed', {'required': state}), 'blocked')
        self.assertEqual(scenario.aggregate('passed', {'required': 'failed'}), 'failed')
        self.assertEqual(scenario.aggregate('failed', {'required': 'blocked'}), 'failed')
        self.assertEqual(scenario.exception_status(AssertionError('broken invariant')), 'failed')
        self.assertEqual(scenario.exception_status(scenario.Blocked('missing pin')), 'blocked')
        self.assertEqual(scenario.aggregate('passed', {}), 'blocked')
        self.assertEqual(scenario.aggregate('blocked', {'required': 'passed'}), 'blocked')
        self.assertEqual(scenario.aggregate('passed', {'required': 'passed'}), 'passed')

    def test_current_pinned_inventory_is_exact(self):
        inventory = scenario.inventory()
        self.assertEqual(set(inventory['components']), {'core', 'host', 'browser', 'tether', 'refinery', 'console', 'platform'})
        self.assertEqual(inventory['seed'], 17)


if __name__ == '__main__':
    unittest.main()
