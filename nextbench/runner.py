"""Frozen separate-campaign launch gates. No benchmark starts during preparation."""
import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from bench.credentials import load_keys
from bench.durable import Journal, atomic_json, encode
from bench.lease import ControllerLease
from bench.security import docker, remove_owned, SecurityError
from bench.containers import emergency_stop
from nextbench.scope import validate_scope
from nextbench.recovery import run_pending, _plan, _sync_slots, _exports
from nextbench.attempt import attempt
from nextbench.analysis import export
from nextbench.prepare import metadata

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ('report_scope.json','provider_metadata.json','model_profile.json','protocol.json',
           'probe_budget.json','analysis_plan.json','user_decisions.json','images.json')
EVIDENCE = ('checks/unit_tests.json','checks/relay-accounting/latest.json',
            'checks/production-attempt/report.json','checks/fake-runtime/latest.json',
            'probes/compatibility/report.json','probes/compatibility/checkpoints/latest/journal-backup.sqlite3',
            'preservation/verification.json')


def campaign_path(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT / 'campaigns') or path in {ROOT / 'campaigns', ROOT / 'campaigns/shared'}:
        raise ValueError('An isolated model campaign path is required')
    return path


def current_hashes(campaign):
    values = {}
    for p in sorted(p for p in (ROOT / 'nextbench').rglob('*') if p.suffix in {'.py','.ps1'}):
        values['project/' + p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((ROOT / 'tests_nextbench').rglob('*.py')):
        values['project/' + p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    for name in CONFIGS:
        values['campaign/config/' + name] = hashlib.sha256((campaign / 'config' / name).read_bytes()).hexdigest()
    for name in EVIDENCE:
        values['campaign/' + name] = hashlib.sha256((campaign / name).read_bytes()).hexdigest()
    latest = json.loads((campaign / 'checks/fake-runtime/latest.json').read_text())
    path = Path(latest['report']).resolve()
    if not path.is_relative_to(campaign / 'checks/fake-runtime'):
        raise ValueError('Fake evidence path escaped its campaign')
    values['campaign/' + path.relative_to(campaign).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def hash_sources():
    return {'project/' + p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('nextbench','tests_nextbench')
            for p in sorted((ROOT / folder).rglob('*')) if p.suffix in {'.py','.ps1'}}


def evidence_current(report, field):
    values = report.get(field, {})
    return bool(values) and all((ROOT / name).is_file() and
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in values.items())


def ready(campaign, *, require_freeze=True):
    campaign = campaign_path(campaign)
    scope = json.loads((campaign / 'config/report_scope.json').read_text())
    gates = {'report_scope': bool(validate_scope(ROOT, scope)), 'baseline_frozen_files_unchanged': True}
    old = json.loads((ROOT / 'dataset/freeze.json').read_text())
    gates['baseline_frozen_files_unchanged'] = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == wanted
                                                 for name, wanted in old['file_hashes'].items())
    images = json.loads((campaign / 'config/images.json').read_text())
    gates['image_pins_available'] = all(json.loads(docker(['image','inspect', image['id']]))[0]['Id'] == image['id'] for image in images.values())
    for key, path in [('unit_checks','checks/unit_tests.json'), ('relay_accounting','checks/relay-accounting/latest.json'),
                      ('cloud_compatibility','probes/compatibility/report.json'), ('production_attempt','checks/production-attempt/report.json')]:
        p = campaign / path
        report = json.loads(p.read_text()) if p.exists() else {}
        gates[key] = report.get('passed') is True
        if key == 'unit_checks':
            gates['unit_sources_current'] = report.get('source_hashes') == hash_sources()
        elif key == 'relay_accounting':
            gates['relay_sources_current'] = evidence_current(report, 'tested_runtime_sources') and report.get('relay_image') == images['relay']['id']
        else:
            gates[key + '_sources_current'] = evidence_current(report, 'runtime_sources_sha256')
            gates[key + '_images_current'] = report.get('images') == images
    latest = campaign / 'checks/fake-runtime/latest.json'
    fake = json.loads(latest.read_text()) if latest.exists() else {}
    gates['contained_fake_harness'] = bool(fake.get('passed'))
    report_path = Path(fake.get('report',''))
    if fake and report_path.is_file():
        report = json.loads(report_path.read_text())
        gates['fake_images_current'] = report.get('images') == images
        gates['fake_sources_current'] = evidence_current(report, 'runtime_sources_sha256')
    else:
        gates['fake_images_current'] = False
        gates['fake_sources_current'] = False
    probe_path = campaign / 'probes/compatibility/report.json'
    if probe_path.exists():
        probe = json.loads(probe_path.read_text())
        limits = json.loads((campaign / 'config/probe_budget.json').read_text())
        gates['probe_caps_preserved'] = (probe.get('physical_transmissions', 999) <= limits['max_requests']
            and probe.get('conservative_input_charge', 9999999) <= limits['max_input_tokens']
            and probe.get('conservative_output_charge', 9999999) <= limits['max_output_tokens'])
        gates['probe_images_current'] = probe.get('images') == images
    else:
        gates['probe_caps_preserved'] = gates['probe_images_current'] = False
    gates['launch_stop_not_requested'] = not (campaign / 'results/STOP_REQUESTED').exists()
    p = campaign / 'preservation/verification.json'
    preservation = json.loads(p.read_text()) if p.exists() else {}
    gates['baseline_preservation_verified'] = preservation.get('passed') is True
    if require_freeze:
        p = campaign / 'config/freeze.json'
        freeze = json.loads(p.read_text()) if p.exists() else {}
        hashes = current_hashes(campaign)
        digest = hashlib.sha256(encode(hashes).encode()).hexdigest()
        gates['campaign_frozen'] = (freeze.get('file_hashes') == hashes and freeze.get('study_id') == digest
                                    and freeze.get('runtime_freeze_hash') == digest
                                    and freeze.get('scope_selection_id') == scope['selection_id'])
        expected = [(hashlib.sha256(f"{digest}:{c['task']}:{c['language']}:1".encode()).hexdigest()[:24],
                     c['task'],c['language'],digest) for c in scope['conditions']]
        path = campaign / 'results/journal.sqlite3'
        if path.is_file():
            with closing(sqlite3.connect(path.as_uri() + '?mode=ro',uri=True)) as db:
                actual = db.execute('SELECT id,task,language,dataset_hash FROM runs ORDER BY rowid').fetchall()
            gates['campaign_plan_exact'] = actual == expected
        else:
            gates['campaign_plan_exact'] = False
    result = {'state': 'READY_TO_START' if all(gates.values()) else 'PREPARING', 'ready': all(gates.values()),
              'checks': gates, 'blocking_gates': [k for k,v in gates.items() if not v],
              'benchmark_inference_calls_by_readiness': 0, 'benchmark_launch_authorized': False}
    atomic_json(campaign / 'checks/readiness.json', result)
    return result


def freeze(campaign):
    campaign = campaign_path(campaign)
    with ControllerLease(ROOT / 'results/controller.lock'), ControllerLease(campaign / 'results/controller.lock'):
        gate = ready(campaign, require_freeze=False)
        if not gate['ready']: raise ValueError('Freeze blocked: ' + ', '.join(gate['blocking_gates']))
        hashes = current_hashes(campaign); digest = hashlib.sha256(encode(hashes).encode()).hexdigest()
        scope = json.loads((campaign / 'config/report_scope.json').read_text())
        if digest == scope['baseline_study_id']: raise ValueError('Study identity must differ from baseline')
        p = campaign / 'config/freeze.json'
        if p.exists() and json.loads(p.read_text()).get('file_hashes') != hashes:
            raise ValueError('Refusing to overwrite an existing different campaign freeze')
        if not p.exists():
            atomic_json(p, {'study_id': digest, 'runtime_freeze_hash': digest, 'file_hashes': hashes,
                'created_utc': datetime.now(timezone.utc).isoformat(), 'task_count': 46,
                'planned_primary_conditions': 138, 'max_total_attempts': 276,
                'scope_selection_id': scope['selection_id'], 'benchmark_started': False})
        with closing(Journal(campaign / 'results/journal.sqlite3')) as primary:
            _plan(primary, scope, digest)
            probe_path = campaign / 'probes/compatibility/journal.sqlite3'
            with closing(Journal(probe_path)) as probe:
                _sync_slots(primary, probe)
            _exports(primary, campaign)
            export(primary, campaign, json.loads((ROOT / 'dataset/task_manifest.json').read_text()))
    return ready(campaign)


def cleanup(journal):
    emergency_stop(journal)
    order = {'container': 0, 'volume': 1, 'network': 2}
    for resource in sorted(journal.resources(), key=lambda r: order[r['kind']]):
        try:
            remove_owned(resource['kind'], resource['id'], expected_id=resource.get('object_id'))
        except SecurityError:
            existing = docker([resource['kind'], 'ls', '--format', '{{json .}}'])
            if resource['id'].encode() in existing: raise
        journal.resource_removed(resource['kind'], resource['id'])


def start(campaign, *, launch_authorized=False):
    if not launch_authorized: raise ValueError('Explicit benchmark launch authorization is required')
    campaign = campaign_path(campaign)
    gate = ready(campaign)
    if not gate['ready']: raise ValueError('Launch blocked: ' + ', '.join(gate['blocking_gates']))
    freeze_info = json.loads((campaign / 'config/freeze.json').read_text())
    profile = json.loads((campaign / 'config/model_profile.json').read_text())
    live = metadata()
    advertised = next(m['digest'] for m in live['tags'] if m['name'] == profile['model'])
    if advertised != profile['provider_advertised_digest']:
        raise ValueError('Advertised cloud model changed since preparation; revalidation required')
    show = live['show'][profile['model']]
    contexts = [v for k,v in show['model_info'].items() if k.endswith('.context_length')]
    if (show['thinking'] != {'values':[False,True],'default':True}
            or not {'completion','tools','thinking'} <= set(show['capabilities'])
            or contexts != [profile['provider_context_window']]):
        raise ValueError('Cloud capability metadata changed; revalidation required')
    images = json.loads((campaign / 'config/images.json').read_text())
    limits = json.loads((campaign / 'config/protocol.json').read_text())
    scope = json.loads((campaign / 'config/report_scope.json').read_text())
    manifest = json.loads((ROOT / 'dataset/task_manifest.json').read_text())
    keys = load_keys()
    def record_controller():
        atomic_json(campaign / 'results/controller_process.json', {'pid': os.getpid(), 'module': 'nextbench.runner',
                   'started_utc': datetime.now(timezone.utc).isoformat(), 'study_id': freeze_info['study_id']})
    def execute(journal, row, preferred, *, destination_root, checkpoint):
        if (campaign / 'results/STOP_REQUESTED').exists(): raise RuntimeError('Operator stop requested')
        if current_hashes(campaign) != freeze_info['file_hashes']: raise ValueError('Frozen implementation/configuration changed')
        validate_scope(ROOT, scope)
        baseline = json.loads((ROOT / 'dataset/freeze.json').read_text())
        if not all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                   for name,digest in baseline['file_hashes'].items()):
            raise ValueError('Frozen baseline/shared implementation changed')
        status, slot = attempt(journal, row, keys, preferred, baseline_root=ROOT, campaign_root=campaign,
            profile=profile, limits=limits, images=images, runtime_freeze_hash=freeze_info['runtime_freeze_hash'],
            destination_root=destination_root, checkpoint=checkpoint)
        print(json.dumps({'task': row['task'], 'language': row['language'], 'status': status}), flush=True)
        return slot
    return run_pending(ROOT, campaign, scope, freeze_info['study_id'], execute, cleanup,
                       exporter=lambda primary: export(primary, campaign, manifest), on_acquired=record_controller)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=('ready','freeze','start'))
    parser.add_argument('campaign', type=Path); parser.add_argument('--launch-authorized', action='store_true')
    args = parser.parse_args()
    value = start(args.campaign, launch_authorized=args.launch_authorized) if args.command == 'start' else freeze(args.campaign) if args.command == 'freeze' else ready(args.campaign)
    print(json.dumps(value), flush=True)


if __name__ == '__main__': main()
