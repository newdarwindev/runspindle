#!/usr/bin/env python3
"""One real core/Temporal development scenario; full-system gates remain blocked."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'scenarios/core-temporal-v1.json'


class Blocked(RuntimeError):
    """Missing prerequisite, incompatible pin, or incomplete evidence."""


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, timeout=15).strip()


def inventory(root=ROOT):
    """Bind actual source checkouts, index gitlinks, lock and contract bytes."""
    root = pathlib.Path(root).resolve()
    lock_path = root / 'composition.lock.json'
    lock = json.loads(lock_path.read_text())
    expected = {'core', 'host', 'browser', 'tether', 'refinery', 'console', 'platform'}
    if lock.get('schema_version') != 1 or len(lock.get('components', [])) != 7:
        raise Blocked('invalid composition lock')
    components = {}
    for item in lock['components']:
        name = item['component']
        if name not in expected or name in components or item['path'] != f'components/{name}':
            raise Blocked('invalid component inventory')
        component = root / item['path']
        if not (component / 'component.json').is_file():
            raise Blocked('missing component: ' + name)
        entry = git(root, 'ls-files', '--stage', '--', item['path']).split()
        if len(entry) != 4 or entry[:3] != ['160000', item['commit'], '0']:
            raise Blocked('gitlink/lock mismatch: ' + name)
        if git(component, 'rev-parse', 'HEAD') != item['commit']:
            raise Blocked('checkout/lock mismatch: ' + name)
        if git(component, 'status', '--porcelain', '--untracked-files=no'):
            raise Blocked('modified pinned component: ' + name)
        components[name] = {'commit': item['commit'], 'repository': item['repository']}
    if set(components) != expected:
        raise Blocked('incomplete component inventory')
    contract = root / 'contracts/runtime-v1.json'
    if json.loads(contract.read_text()).get('version') != 'runspindle.runtime.v1':
        raise Blocked('incompatible runtime contract')
    manifest = root / 'scenarios/core-temporal-v1.json'
    config = json.loads(manifest.read_text())
    if config.get('runtime_contract') != 'runspindle.runtime.v1' or config.get('seed') != 17:
        raise Blocked('incompatible scenario')
    return {
        'composition_commit': git(root, 'rev-parse', 'HEAD'),
        'components': components,
        'lock_sha256': sha256(lock_path),
        'contract_sha256': sha256(contract),
        'scenario_sha256': sha256(manifest),
        'fixture_manifest_sha256': sha256(root / 'fixtures/v1/manifest.json'),
        'driver_sha256': sha256(root / 'tools/core_temporal_scenario.py'),
        'seed': config['seed'],
    }


def aggregate(real_core_lane, gates):
    """A passing development lane cannot turn unimplemented system gates green."""
    if real_core_lane == 'failed' or 'failed' in gates.values():
        return 'failed'
    return 'passed' if real_core_lane == 'passed' and gates and all(
        state == 'passed' for state in gates.values()) else 'blocked'


def binding(admission):
    keys = ('task_id', 'revision', 'operation_id', 'policy_revision', 'host_id', 'workspace_id', 'lease_epoch')
    return {key: admission[key] for key in keys}


def assert_observations(observed, admission):
    """Independent assertions over client replies and the scripted peer's ledger."""
    job = 'job-' + hashlib.sha256(f"{admission['task_id']}\n{admission['revision']}".encode()).hexdigest()
    replies = observed['admission_replies']
    assert sorted(reply['status'] for reply in replies) == ['admitted', 'duplicate_delivery']
    assert all(reply['job_id'] == job for reply in replies)
    assert observed['offline_launch_count'] == 0
    assert observed['conflict']['status'] == 'delivery_conflict'
    assert observed['active_revision']['status'] == 'predecessor_active'
    assert observed['worker_exit'] == 93
    assert observed['duplicate_after_restart'] == {'status': 'duplicate_delivery', 'job_id': job}
    recovered = observed['recovered']
    assert recovered['binding'] == binding(admission)
    assert recovered['state'] == 'acknowledged'
    assert recovered['native_session_id'] == 'observed-native-17'
    assert observed['wrong_cancel'] == {'accepted': False}
    assert observed['cancel'] == {'accepted': True}
    acknowledged = observed['cancel_acknowledged']
    assert acknowledged['cancellation'] == 'acknowledged'
    assert acknowledged['state'] not in ('observed_completed', 'observed_failed', 'observed_cancelled')
    final = observed['terminal']
    assert final['binding'] == binding(admission)
    assert final['native_session_id'] == 'observed-native-17'
    assert final['state'] == 'observed_cancelled'
    assert final['cancellation'] == 'observed_terminal'
    calls = observed['calls']
    allowed = {'verify', 'observe_host', 'launch', 'discover', 'poll', 'cancel'}
    for call in calls:
        assert call['action'] in allowed
        if call['action'] != 'verify':
            assert call['admission'] == admission
        assert call['native_session_id'] in (None, 'observed-native-17')
    actions = [call['action'] for call in calls]
    assert actions.count('launch') == 1
    assert actions.count('cancel') == 1
    assert actions.index('observe_host') < actions.index('launch') < actions.index('discover') < actions.index('cancel')
    assert len(observed['effect_receipts']) == 1
    receipt = observed['effect_receipts'][0]
    assert receipt['binding'] == binding(admission)
    assert receipt['native_session_id'] == 'observed-native-17'
    assert observed['replay']['status'] == 'passed'
    assert observed['calls_after_replay'] == len(calls)
    return {'job_id': job, 'launch_calls': 1, 'cancel_calls': 1,
            'native_session_id': 'observed-native-17', 'terminal': final['state']}


def load_exact_source(path, name):
    import types
    path = pathlib.Path(path)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def verify_core_image(image, root=ROOT):
    """Bind immutable executable bytes to build evidence committed in pinned core."""
    import re
    import tempfile
    import uuid
    core = pathlib.Path(root) / 'components/core'
    evidence_path = core / 'docs/runtime-build.json'
    if not evidence_path.is_file():
        raise Blocked('pinned core build provenance missing')
    evidence = json.loads(evidence_path.read_text())
    if not re.fullmatch('sha256:[a-f0-9]{64}', image) or evidence['image_id'] != image:
        raise Blocked('core image does not match pinned build evidence')
    required = {'Cargo.toml', 'Cargo.lock', 'src/lib.rs', 'src/runtime.rs', 'src/bin/temporal-runtime.rs'}
    if not required.issubset(evidence['source_hashes']):
        raise Blocked('core build provenance lacks runtime source hashes')
    for name, expected in evidence['source_hashes'].items():
        path = (core / name).resolve(strict=True)
        if core.resolve() not in path.parents or sha256(path) != expected:
            raise Blocked('core build source differs: ' + name)
    if evidence['dependency_inventory_sha256'] != sha256(core / 'docs/runtime-dependencies.json'):
        raise Blocked('core dependency inventory differs')
    def docker(*args):
        return subprocess.run(['docker', *args], capture_output=True, text=True, check=True, timeout=30)
    metadata = json.loads(docker('image', 'inspect', image).stdout)[0]
    labels = metadata['Config'].get('Labels') or {}
    if labels.get('org.runspindle.binary_sha256') != evidence['binary_sha256']:
        raise Blocked('core image binary label differs')
    if labels.get('org.runspindle.cargo_lock_sha256') != sha256(core / 'Cargo.lock'):
        raise Blocked('core image lock label differs')
    name = 'runspindle-provenance-' + uuid.uuid4().hex
    try:
        # Creating/copying inspects bytes without executing an unverified image.
        docker('create', '--pull', 'never', '--network', 'none', '--name', name, image)
        with tempfile.TemporaryDirectory(prefix='runspindle-binary-verification-') as directory:
            binary = pathlib.Path(directory) / 'temporal-runtime'
            docker('cp', name + ':/usr/local/bin/temporal-runtime', str(binary))
            if sha256(binary) != evidence['binary_sha256']:
                raise Blocked('core image executable differs from pinned build')
    finally:
        docker('rm', '--force', name)
    return evidence


def run(platform_prepared, core_image):
    import concurrent.futures
    import copy
    import tempfile
    import time
    import uuid

    sources = inventory()
    core_build = verify_core_image(core_image)
    config = json.loads(MANIFEST.read_text())
    platform = ROOT / 'components/platform/tools/temporal_lane.py'
    if not platform.is_file():
        raise Blocked('pinned platform does not implement Temporal lane')
    core_dependencies = ROOT / 'components/core/docs/runtime-dependencies.json'
    if not core_dependencies.is_file():
        raise Blocked('pinned core does not implement Temporal runtime')
    # Execute the exact inventoried source bytes; an untracked .pyc cannot replace them.
    lane_module = load_exact_source(platform, 'runspindle_temporal_lane')
    admission = {'version': 'runspindle.runtime.v1', 'delivery_namespace': 'synthetic',
                 'delivery_id': 'event-17', 'task_id': 'scenario-task-17', 'revision': 1,
                 'operation_id': 'operation-17', 'predecessor_revision': None,
                 'normalized_digest': hashlib.sha256(b'synthetic scenario 17').hexdigest(),
                 'policy_revision': 'policy-17', 'host_id': 'offline-host-17',
                 'workspace_id': 'workspace-17', 'lease_epoch': 1, 'grant_ref': 'synthetic-grant-17'}
    base_script = {'admission': admission, 'authorized': True, 'online': False,
                   'native_session_id': 'observed-native-17', 'launch_lost_reply': True,
                   'crash_after_launch': True, 'terminal': None, 'cancel_acknowledged': True}
    script = [base_script]
    observed = {}
    script_hashes = []
    with tempfile.TemporaryDirectory(prefix='runspindle-synthetic-effects-') as directory:
        effects = pathlib.Path(directory)

        def save_script():
            temporary = effects / 'script.next'
            temporary.write_text(json.dumps(script, sort_keys=True))
            temporary.replace(effects / 'script.json')
            script_hashes.append(sha256(effects / 'script.json'))

        def calls():
            path = effects / 'calls.jsonl'
            return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

        def wait_for(callback, label, seconds=60):
            until = time.monotonic() + seconds
            while time.monotonic() < until:
                result = callback()
                if result:
                    return result
                time.sleep(0.1)
            raise Blocked('scenario deadline: ' + label)

        save_script()
        with lane_module.Lane(platform_prepared) as lane:
            mounts = [{'source': directory, 'target': '/effects', 'read_only': False}]

            def client(command):
                name = 'command-' + uuid.uuid4().hex + '.json'
                (effects / name).write_text(json.dumps(command, sort_keys=True))
                logs = lane.run_client(core_image, ['client', 'http://temporal:7233', '/effects/' + name],
                                       mounts=mounts, deadline=30)
                # Rust runtime diagnostics go to stderr; stdout is the result envelope.
                return json.loads(logs.stdout.strip().splitlines()[-1])

            registry = 'scenario-registry-17'
            worker = lane.spawn_client(core_image, ['worker', 'http://temporal:7233', '/effects'], mounts)
            client({'command': 'start', 'registry_id': registry})
            command = {'command': 'admit', 'registry_id': registry, 'admission': admission}
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                observed['admission_replies'] = list(pool.map(client, [command, command]))
            job = observed['admission_replies'][0]['job_id']
            wait_for(lambda: any(c['action'] == 'observe_host' for c in calls()), 'offline observation')
            observed['offline_launch_count'] = sum(c['action'] == 'launch' for c in calls())
            conflict = dict(admission, policy_revision='conflicting-policy')
            next_revision = dict(admission, delivery_id='event-next-17', revision=2,
                                 operation_id='operation-next-17', predecessor_revision=1)
            script += [dict(base_script, admission=conflict), dict(base_script, admission=next_revision)]
            save_script()
            observed['conflict'] = client(dict(command, admission=conflict))
            observed['active_revision'] = client(dict(command, admission=next_revision))
            base_script['online'] = True
            save_script()
            def worker_exit():
                result = lane_module.docker('inspect', '--format', '{{json .State}}', worker)
                state = json.loads(result.stdout)
                return state['ExitCode'] if not state['Running'] else None
            observed['worker_exit'] = wait_for(worker_exit, 'worker crash after accepted launch')
            base_script['crash_after_launch'] = False
            save_script()
            lane.restart(abrupt=True)
            worker = lane.spawn_client(core_image, ['worker', 'http://temporal:7233', '/effects'], mounts)
            observed['duplicate_after_restart'] = client(command)
            def operation_when(predicate):
                result = client({'command': 'operation', 'job_id': job})
                return result if predicate(result) else None
            observed['recovered'] = wait_for(lambda: operation_when(
                lambda s: s['state'] == 'acknowledged' and s['native_session_id'] is not None),
                'native session reconciliation')
            observed['wrong_cancel'] = client({'command': 'cancel', 'job_id': job,
                                              'binding': dict(binding(admission), lease_epoch=2)})
            observed['cancel'] = client({'command': 'cancel', 'job_id': job, 'binding': binding(admission)})
            observed['cancel_acknowledged'] = wait_for(lambda: operation_when(
                lambda s: s['cancellation'] == 'acknowledged'), 'cancellation acknowledgement')
            base_script['terminal'] = 'cancelled'
            save_script()
            def terminal_registry():
                state = client({'command': 'registry', 'registry_id': registry})
                return state['terminal'].get(job)
            observed['terminal'] = wait_for(terminal_registry, 'observed terminal in registry')
            observed['calls'] = calls()
            observed['effect_receipts'] = [json.loads(p.read_text()) for p in effects.glob('effect-*.json')]
            history = client({'command': 'history', 'workflow_id': job})
            (effects / 'history.json').write_text(json.dumps(history))
            replay = lane.run_client(core_image, ['replay', '/effects/history.json'], mounts=mounts, deadline=30)
            observed['replay'] = json.loads(replay.stdout.strip().splitlines()[-1])
            observed['calls_after_replay'] = len(calls())
            assertions = assert_observations(observed, admission)
            resources = [('container', lane.server), ('network', lane.network), ('volume', lane.volume)]
            resources += [('container', name) for name in sorted(lane.clients)]
            toolchains = {'core_image': core_image, 'temporal_image': lane.image,
                          'platform_prepared': lane.metadata,
                          'core_dependencies_sha256': sha256(core_dependencies),
                          'core_build': core_build}
        for kind, name in resources:
            if lane_module.docker(kind, 'inspect', name, check=False).returncode == 0:
                raise AssertionError('scenario cleanup left resource: ' + kind)
        result = {'schema_version': 'runspindle.scenario-report.v1',
                  'scenario_id': config['scenario_id'], 'evidence_class': 'isolated_integration',
                  'real_core_lane': 'passed', 'aggregate': aggregate('passed', config['required_system_gates']),
                  'system_gates': config['required_system_gates'], 'boundary_matrix': config['boundary_matrix'],
                  'source': sources, 'toolchains': toolchains, 'assertions': assertions,
                  'cleanup': 'independently_absent', 'observations': observed,
                  'script_sha256s': script_hashes}
        normalized = {key: result[key] for key in ('scenario_id', 'boundary_matrix', 'assertions', 'system_gates')}
        result['normalized_outcome_sha256'] = hashlib.sha256(
            json.dumps(normalized, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return result


def exception_status(exc):
    if isinstance(exc, (Blocked, OSError)) or type(exc).__name__ == 'Blocked':
        return 'blocked'
    return 'failed'


def main():
    import argparse
    import datetime
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform-prepared', required=True)
    parser.add_argument('--core-image', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    try:
        result = run(args.platform_prepared, args.core_image)
    except (Blocked, AssertionError, OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        state = exception_status(exc)
        result = {'real_core_lane': state, 'aggregate': state, 'reason': str(exc),
                  'live_acceptance': 'not_run'}
    result['observed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pathlib.Path(args.report).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: result[key] for key in ('real_core_lane', 'aggregate')}))
    raise SystemExit({'passed': 0, 'failed': 1, 'blocked': 78}[result['aggregate']])


if __name__ == '__main__':
    main()
