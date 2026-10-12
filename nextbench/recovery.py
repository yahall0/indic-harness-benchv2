"""Crash-safe, bounded INFRA recovery for separate future campaign journals.

The caller must supply an audited, campaign-aware Docker attempt implementation.
The frozen baseline attempt function is deliberately rejected. No live CLI exists.
"""
from __future__ import annotations

import hashlib
import json
import time
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path

from bench.controller import campaign_decision
from bench.durable import Journal, atomic_json, encode
from bench.lease import ControllerLease
from bench.metrics import AGENT_OUTCOMES
from nextbench.scope import validate_scope


def _recovery_root(campaign_root, primary_id, relative):
    expected = 'recoveries/' + primary_id + '/attempt-2'
    if relative != expected or len(primary_id) != 24 or any(c not in '0123456789abcdef' for c in primary_id):
        raise ValueError('Unsafe recovery registry path')
    root = (campaign_root / 'results' / relative).resolve()
    if not root.is_relative_to((campaign_root / 'results/recoveries').resolve()):
        raise ValueError('Recovery path escaped its campaign')
    # Resolve against the campaign itself as well, rejecting junction escapes.
    if not root.is_relative_to(campaign_root):
        raise ValueError('Recovery path points outside its campaign')
    return root


@dataclass(frozen=True)
class RecoveryPolicy:
    max_recoveries_per_condition: int = 1
    cooldown_seconds: int = 30
    consecutive_provider_failure_limit: int = 3

    def __post_init__(self):
        if self.max_recoveries_per_condition != 1:
            raise ValueError('This protocol permits exactly one infrastructure recovery')
        if self.cooldown_seconds < 30 or self.consecutive_provider_failure_limit < 3:
            raise ValueError('Provider cooldown and outage controls cannot be weakened')


def recovery_decision(journal, row):
    """Allow only proved recoverable failures after durable accounting and cleanup."""
    decision = campaign_decision(journal, row)
    if row['status'] != 'infrastructure_failed':
        return {**decision, 'recovery_eligible': False}
    if decision['action'] == 'continue':
        return {**decision, 'recovery_eligible': True}
    result = json.loads(row.get('result') or '{}')
    if result.get('integrity') or result.get('cleanup_incomplete') or result.get('error_type'):
        return {**decision, 'recovery_eligible': False}
    # A proved broken delivery after successful settlement is local infrastructure,
    # not an unacknowledged cloud call. A fresh attempt never replays that call ID.
    with journal.lock:
        calls = [dict(r) for r in journal.db.execute(
            'SELECT * FROM calls WHERE run_id=? ORDER BY rowid', (row['id'],))]
        events = [dict(r) for r in journal.db.execute(
            'SELECT kind,payload FROM events WHERE run_id=? ORDER BY seq', (row['id'],))]
        resources = journal.db.execute(
            "SELECT COUNT(*) FROM resources WHERE run_id=? AND status!='removed'", (row['id'],)).fetchone()[0]
    if resources or not calls or any(call['status'] != 'settled' for call in calls):
        return {**decision, 'recovery_eligible': False}
    if any(event['kind'] == 'budget_integrity_violation' for event in events):
        return {**decision, 'recovery_eligible': False}
    response = json.loads(calls[-1]['response'] or '{}')
    pauses = [json.loads(e['payload']) for e in events if e['kind'] == 'provider_pause']
    if (result.get('pause_reason') == 'relay_accounting_gate'
            and response.get('classification') == 'success' and response.get('status') == 200
            and pauses and all(
                p.get('classification') == 'relay_accounting_gate'
                and p.get('call_id') == calls[-1]['id'] and p.get('settled') is True
                and p.get('stage') == 'agent_delivery' and p.get('upstream_status') == 200
                and p.get('error_type') in {'BrokenPipeError', 'ConnectionResetError'} for p in pauses)):
        return {'action': 'continue', 'reason': 'settled_response_delivery_failure',
                'provider_failure': False, 'recovery_eligible': True}
    return {**decision, 'recovery_eligible': False}


def _plan(journal, scope, study_id):
    expected = []
    with journal.lock:
        journal.db.execute('BEGIN IMMEDIATE')
        try:
            journal.db.execute('''CREATE TABLE IF NOT EXISTS recovery_attempts (
                primary_run_id TEXT PRIMARY KEY REFERENCES runs(id),
                retry_run_id TEXT NOT NULL UNIQUE, relative_root TEXT NOT NULL UNIQUE)''')
            for condition in scope['conditions']:
                task, language = condition['task'], condition['language']
                ident = hashlib.sha256(f'{study_id}:{task}:{language}:1'.encode()).hexdigest()[:24]
                expected.append((ident, task, language, study_id))
            actual = [tuple(r) for r in journal.db.execute(
                'SELECT id,task,language,dataset_hash FROM runs ORDER BY rowid')]
            if actual and actual != expected:
                raise ValueError('Existing campaign does not match the exact report scope/order')
            if not actual:
                journal.db.executemany('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)', expected)
                journal._event(None, 'report_matched_scope_planned', {'selection_id': scope['selection_id'],
                                                                      'conditions': len(expected)})
            journal.db.execute('COMMIT')
        except BaseException:
            journal.db.execute('ROLLBACK')
            raise


def _schedule_recovery(primary, row):
    ident = hashlib.sha256((row['dataset_hash'] + ':' + row['id'] + ':infra-recovery:2').encode()).hexdigest()[:24]
    relative = 'recoveries/' + row['id'] + '/attempt-2'
    with primary.lock:
        primary.db.execute('BEGIN IMMEDIATE')
        try:
            prior = primary.db.execute('SELECT * FROM recovery_attempts WHERE primary_run_id=?', (row['id'],)).fetchone()
            if not prior:
                primary.db.execute('INSERT INTO recovery_attempts VALUES(?,?,?)', (row['id'], ident, relative))
                primary._event(row['id'], 'infrastructure_recovery_scheduled', {
                    'retry_run_id': ident, 'attempt_number': 2,
                    'authorization': 'User requested one infrastructure recovery for future campaigns',
                    'fresh_agent_state': True, 'primary_preserved': True})
            elif (prior['retry_run_id'], prior['relative_root']) != (ident, relative):
                raise ValueError('Recovery identity conflict')
            primary.db.execute('COMMIT')
        except BaseException:
            primary.db.execute('ROLLBACK')
            raise
    return ident, relative


def _open_recovery(primary, row, campaign_root):
    ident, relative = _schedule_recovery(primary, row)
    root = _recovery_root(campaign_root, row['id'], relative)
    journal = Journal(root / 'journal.sqlite3')
    with journal.lock:
        prior = journal.runs()
        if not prior:
            journal.db.execute('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',
                               (ident, row['task'], row['language'], row['dataset_hash']))
            journal.event(ident, 'separate_infrastructure_recovery', {
                'primary_run_id': row['id'], 'attempt_number': 2})
        elif len(prior) != 1 or tuple(prior[0][k] for k in ('id', 'task', 'language', 'dataset_hash')) != (
                ident, row['task'], row['language'], row['dataset_hash']):
            journal.close()
            raise ValueError('Recovery journal identity conflict')
    _sync_slots(primary, journal)
    return journal, root, ident


def _sync_slots(primary, recovery):
    """Persist the union of exhausted slots; a crash cannot reset eligibility."""
    primary.slot_init([s['id'] for s in recovery.slot_state()])
    recovery.slot_init([s['id'] for s in primary.slot_state()])
    for source, destination in ((recovery, primary), (primary, recovery)):
        existing = {s['id']: s for s in destination.slot_state()}
        for slot in source.slot_state():
            if slot['state'] == 'exhausted' and existing[slot['id']]['state'] != 'exhausted':
                destination.exhaust_slot(slot['id'], 'confirmed_quota_exhaustion', None)


def _resume_safely(journal, cleanup):
    if journal.resources() or any(row['status'] == 'running' for row in journal.runs()):
        cleanup(journal)
        if journal.resources():
            raise ValueError('Recorded resource cleanup is incomplete')
        journal.recover()


def _exports(primary, campaign_root):
    primary.export(campaign_root / 'results/checkpoints/latest')
    primary_rows, recovered_rows = [], []
    accounting = {'physical_transmissions': 0, 'known_input_tokens': 0, 'known_output_tokens': 0,
                  'charged_input': 0, 'charged_output': 0, 'usage_missing_calls': 0}
    def account(journal):
        accounting['physical_transmissions'] += journal.db.execute('SELECT COUNT(*) FROM forwards').fetchone()[0]
        for r in journal.runs():
            for field, source in (('known_input_tokens', 'input_actual'), ('known_output_tokens', 'output_actual'),
                                  ('charged_input', 'input_bound'), ('charged_output', 'output_reserved'),
                                  ('usage_missing_calls', 'usage_missing')):
                accounting[field] += r[source]
    account(primary)
    registries = {r['primary_run_id']: dict(r) for r in primary.db.execute('SELECT * FROM recovery_attempts')}
    for row in primary.runs():
        original = {**row, 'attempt_number': 1, 'primary_run_id': row['id']}
        chosen = original
        entry = registries.get(row['id'])
        if entry:
            path = _recovery_root(campaign_root, row['id'], entry['relative_root']) / 'journal.sqlite3'
            if path.exists():
                with closing(Journal(path)) as retry:
                    retry_row = retry.get(entry['retry_run_id'])
                    account(retry)
                    retry.export(path.parent / 'checkpoints/latest')
                    if retry_row['status'] in AGENT_OUTCOMES:
                        chosen = {**retry_row, 'attempt_number': 2, 'primary_run_id': row['id']}
        primary_rows.append(original)
        recovered_rows.append(chosen)
    atomic_json(campaign_root / 'results/exports/primary_outcomes.json', primary_rows)
    atomic_json(campaign_root / 'results/exports/outcomes_with_recovery.json', recovered_rows)
    atomic_json(campaign_root / 'results/exports/accounting_all_attempts.json', accounting)


def run_pending(baseline_root, campaign_root, scope, study_id, attempt, cleanup,
                *, policy=RecoveryPolicy(), preferred=None, sleep=time.sleep, exporter=None, on_acquired=None):
    """Evaluate only planned attempts; recover once, save all costs, and continue.

    attempt(journal, row, preferred, destination_root=..., checkpoint=...) must
    use fresh hardened Docker state, finish transactionally, and return a slot ID.
    cleanup(journal) must stop/retire only that journal's recorded owned resources.
    Caller is responsible for the model freeze, launch authorization and total
    budget admission gates. This module is a tested foundation, not a live runner.
    """
    baseline_root, campaign_root = Path(baseline_root).resolve(), Path(campaign_root).resolve()
    campaigns = baseline_root / 'campaigns'
    if (not campaign_root.is_relative_to(campaigns) or campaign_root in {campaigns, campaigns / 'shared'}
            or campaign_root.is_relative_to(campaigns / 'shared')):
        raise ValueError('A separate model campaign namespace is required')
    if not study_id or study_id == scope['baseline_study_id']:
        raise ValueError('A distinct future study ID is required')
    if getattr(attempt, '__module__', '') == 'bench.controller':
        raise ValueError('The frozen baseline attempt uses baseline paths and cannot run a future campaign')
    validate_scope(baseline_root, scope)
    decisions = []
    with ControllerLease(baseline_root / 'results/controller.lock'), \
            ControllerLease(campaign_root / 'results/controller.lock'), \
            closing(Journal(campaign_root / 'results/journal.sqlite3')) as primary:
        _plan(primary, scope, study_id)
        if on_acquired:
            on_acquired()
        _resume_safely(primary, cleanup)
        # Reconcile all recovery slots before any new primary admission.
        for entry in primary.db.execute('SELECT * FROM recovery_attempts').fetchall():
            with closing(_open_recovery(primary, primary.get(entry['primary_run_id']), campaign_root)[0]) as retry:
                _sync_slots(primary, retry)
                _resume_safely(retry, cleanup)
        failures = 0
        primary.event(None, 'future_campaign_session_started', asdict(policy))
        try:
            for row in primary.runs():
                ran_primary = row['status'] == 'planned'
                if ran_primary:
                    preferred = attempt(primary, row, preferred, destination_root=campaign_root / 'results/runs',
                                        checkpoint=campaign_root / 'results/checkpoints/latest')
                row = primary.get(row['id'])
                decision = recovery_decision(primary, row)
                if ran_primary:
                    failures = failures + 1 if decision.get('provider_failure') else 0
                retry_entry = primary.db.execute('SELECT * FROM recovery_attempts WHERE primary_run_id=?', (row['id'],)).fetchone()
                if decision.get('recovery_eligible'):
                    _schedule_recovery(primary, row)
                    if failures >= policy.consecutive_provider_failure_limit:
                        decision = {'action': 'pause', 'reason': 'three_consecutive_provider_failures'}
                    elif decision['action'] == 'continue':
                        with closing(_open_recovery(primary, row, campaign_root)[0]) as retry:
                            retry_root = campaign_root / 'results/recoveries' / row['id'] / 'attempt-2'
                            _resume_safely(retry, cleanup)
                            recovered = retry.runs()[0]
                            if recovered['status'] == 'planned':
                                primary.event(row['id'], 'infrastructure_recovery_cooldown', {'seconds': policy.cooldown_seconds})
                                _exports(primary, campaign_root)
                                sleep(policy.cooldown_seconds)
                                preferred = attempt(retry, recovered, preferred, destination_root=retry_root / 'runs',
                                                    checkpoint=retry_root / 'checkpoints/latest')
                                _sync_slots(primary, retry)
                                recovered = retry.get(recovered['id'])
                                decision = recovery_decision(retry, recovered)
                                failures = failures + 1 if decision.get('provider_failure') else 0
                                # No third attempt, even if the recovery also has INFRA.
                                decision['recovery_eligible'] = False
                            else:
                                decision = recovery_decision(retry, recovered)
                elif not ran_primary and not retry_entry:
                    # Never replay old agent outcomes. Unknown/unsafe INFRA still pauses.
                    if row['status'] in AGENT_OUTCOMES:
                        continue
                if failures >= policy.consecutive_provider_failure_limit:
                    decision = {'action': 'pause', 'reason': 'three_consecutive_provider_failures'}
                payload = {'primary_run_id': row['id'], 'task': row['task'], 'language': row['language'],
                           'consecutive_provider_failures': failures, **decision}
                primary.event(row['id'], 'future_campaign_paused' if decision['action'] == 'pause' else 'future_campaign_continuing', payload)
                decisions.append(payload)
                _exports(primary, campaign_root)
                if exporter:
                    exporter(primary)
                if decision['action'] == 'pause':
                    break
                if decision.get('provider_failure'):
                    sleep(policy.cooldown_seconds)
        finally:
            _exports(primary, campaign_root)
            if exporter:
                exporter(primary)
    return decisions
