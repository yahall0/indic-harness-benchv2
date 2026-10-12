import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from bench.durable import Journal
from bench.lease import ControllerLease
from nextbench.recovery import run_pending

LIMITS = {'attempt_timeout_sec': 600, 'max_requests': 30, 'max_input_tokens': 200000,
          'max_output_tokens': 16000, 'max_response_tokens': 4096}


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.test_parent = Path(__file__).resolve().parents[1] / 'tmp/nextbench-tests'
        self.test_parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='case-', dir=self.test_parent)
        self.root = Path(self.temp.name)
        self.campaign = self.root / 'campaigns/fake-model'
        self.scope = {'baseline_study_id': 'baseline', 'selection_id': 'report-selection',
                      'conditions': [{'task': 'example', 'language': l} for l in ('hi', 'en', 'hinglish')]}
        self.validation = patch('nextbench.recovery.validate_scope', return_value={})
        self.validation.start()
        self.visited, self.sleeps = [], []

    def tearDown(self):
        self.validation.stop()
        self.assertTrue(self.root.resolve().is_relative_to(self.test_parent.resolve()))
        self.temp.cleanup()

    def finish(self, journal, row, *, status='completed', score=0, error=None, slot=None):
        journal.start(row['id'])
        journal.slot_init(['slot-1', 'slot-2'])
        call = 'a' + row['id']
        if error:
            journal.reserve(row['id'], call, 1000, 4096, LIMITS)
            journal.forward(call, 'slot-1', LIMITS)
            classification, upstream, stage = error
            settled = stage != 'settlement'
            if settled:
                journal.settle(call, {'classification': classification, 'status': upstream, 'usage': None})
            payload = {'classification': classification, 'status': upstream, 'call_id': call}
            if stage in {'settlement', 'agent_delivery'}:
                payload.update(classification='relay_accounting_gate', settled=settled,
                               stage=stage, upstream_status=upstream, error_type='BrokenPipeError')
            journal.event(row['id'], 'provider_pause', payload)
            result = {'pause_reason': payload['classification'], 'integrity': []}
        else:
            result = {'integrity': [], 'oracle': {'outcome_score': score, 'checks': []}}
        if slot:
            journal.exhaust_slot(slot, 'confirmed_quota_exhaustion', row['id'])
        journal.finish(row['id'], status, result)

    def run_campaign(self, attempt, **options):
        return run_pending(self.root, self.campaign, self.scope, 'new-study', attempt,
                           lambda journal: None, sleep=self.sleeps.append, **options)

    def rows(self):
        with closing(sqlite3.connect(self.campaign / 'results/journal.sqlite3')) as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute('SELECT * FROM runs ORDER BY rowid')]

    def test_exact_language_order_and_no_retry_of_agent_outcomes(self):
        states = ['budget_exhausted', 'agent_failed', 'completed']
        def attempt(journal, row, preferred, **paths):
            self.visited.append((row['language'], str(journal.path), paths))
            self.finish(journal, row, status=states[len(self.visited) - 1])
            return 'slot-1'
        self.run_campaign(attempt)
        self.assertEqual([v[0] for v in self.visited], ['hi', 'en', 'hinglish'])
        self.assertEqual(len(self.visited), 3)
        before = self.rows()
        self.run_campaign(attempt)
        self.assertEqual(self.rows(), before)
        self.assertEqual(len(self.visited), 3)
        self.assertEqual(self.sleeps, [])

    def test_one_fresh_recovery_preserves_primary_unknown_usage_and_zero_score(self):
        source = []
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            if len(self.visited) == 1:
                self.finish(journal, row, status='infrastructure_failed', error=('ambiguous_transport', 0, 'upstream_transport'))
                source.append(journal.get(row['id']))
            else:
                self.finish(journal, row, score=0)
            return 'slot-1'
        self.run_campaign(attempt)
        self.assertEqual(len(self.visited), 4)
        self.assertEqual(self.rows()[0], source[0])
        self.assertEqual(source[0]['input_bound'], 1000)
        self.assertEqual(source[0]['output_reserved'], 4096)
        self.assertEqual(source[0]['usage_missing'], 1)
        chosen = json.loads((self.campaign / 'results/exports/outcomes_with_recovery.json').read_text())
        self.assertEqual(chosen[0]['attempt_number'], 2)
        self.assertEqual(json.loads(chosen[0]['result'])['oracle']['outcome_score'], 0)
        accounting = json.loads((self.campaign / 'results/exports/accounting_all_attempts.json').read_text())
        self.assertEqual(accounting['charged_input'], 1000)
        self.assertEqual(accounting['charged_output'], 4096)
        self.assertEqual(accounting['physical_transmissions'], 1)
        self.assertEqual(self.sleeps, [30])
        self.run_campaign(attempt)
        self.assertEqual(len(self.visited), 4)
        self.assertEqual(len(list((self.campaign / 'results/recoveries').glob('*/attempt-2/journal.sqlite3'))), 1)

    def test_failed_recovery_does_not_block_next_condition_or_trigger_third_attempt(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            if len(self.visited) <= 2:
                self.finish(journal, row, status='infrastructure_failed', error=('transient', 500, 'upstream_transport'))
            else:
                self.finish(journal, row)
            return 'slot-1'
        decisions = self.run_campaign(attempt)
        self.assertEqual(len(self.visited), 4)
        self.assertTrue(all(d['action'] == 'continue' for d in decisions))
        self.assertEqual([row['status'] for row in self.rows()], ['infrastructure_failed', 'completed', 'completed'])
        self.assertEqual(self.sleeps, [30, 30])

    def test_settled_delivery_failure_gets_recovery_but_unsettled_accounting_pauses(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            if len(self.visited) == 1:
                self.finish(journal, row, status='infrastructure_failed', error=('success', 200, 'agent_delivery'))
            elif len(self.visited) == 3:
                self.finish(journal, row, status='infrastructure_failed', error=('success', 200, 'settlement'))
            else:
                self.finish(journal, row)
            return 'slot-1'
        decisions = self.run_campaign(attempt)
        self.assertEqual(len(self.visited), 3)
        self.assertEqual(decisions[-1]['action'], 'pause')
        self.assertEqual(self.rows()[-1]['status'], 'planned')

    def test_three_provider_failures_pause_with_recovery_durably_scheduled(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            self.finish(journal, row, status='infrastructure_failed', error=('transient', 503, 'upstream_transport'))
            return 'slot-1'
        decisions = self.run_campaign(attempt)
        self.assertEqual(len(self.visited), 3)
        self.assertEqual(decisions[-1]['reason'], 'three_consecutive_provider_failures')
        with closing(sqlite3.connect(self.campaign / 'results/journal.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM recovery_attempts').fetchone()[0], 2)

    def test_credential_exhaustion_in_recovery_survives_restart(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            if len(self.visited) == 1:
                self.finish(journal, row, status='infrastructure_failed', error=('rate_limited', 429, 'upstream_transport'))
            else:
                if len(self.visited) >= 3:
                    self.assertEqual(journal.choose_slot(preferred), 'slot-2')
                self.finish(journal, row, slot='slot-1' if len(self.visited) == 2 else None)
            return 'slot-2' if len(self.visited) >= 2 else 'slot-1'
        self.run_campaign(attempt)
        self.run_campaign(attempt)
        with closing(sqlite3.connect(self.campaign / 'results/journal.sqlite3')) as db:
            self.assertEqual(db.execute("SELECT state FROM slots WHERE id='slot-1'").fetchone()[0], 'exhausted')
            self.assertEqual(db.execute("SELECT state FROM slots WHERE id='slot-2'").fetchone()[0], 'eligible')

    def test_duplicate_controller_and_baseline_namespace_are_rejected(self):
        def attempt(*args, **kwargs):
            self.fail('No inference should be admitted')
        with ControllerLease(self.root / 'results/controller.lock'):
            with self.assertRaises(RuntimeError):
                self.run_campaign(attempt)
        with self.assertRaises(ValueError):
            run_pending(self.root, self.root, self.scope, 'new-study', attempt, lambda j: None)
        with self.assertRaises(ValueError):
            run_pending(self.root, self.campaign, self.scope, 'baseline', attempt, lambda j: None)

    def test_crash_during_recovery_is_not_replayed(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            if len(self.visited) == 1:
                self.finish(journal, row, status='infrastructure_failed', error=('transient', 500, 'upstream_transport'))
                return 'slot-1'
            journal.start(row['id'])
            raise RuntimeError('Simulated controller crash')
        with self.assertRaises(RuntimeError):
            self.run_campaign(attempt)
        def resumed(journal, row, preferred, **paths):
            self.fail('Interrupted recovery must not be replayed')
        decisions = self.run_campaign(resumed)
        self.assertEqual(len(self.visited), 2)
        self.assertEqual(decisions[-1]['action'], 'pause')
        recovery = next((self.campaign / 'results/recoveries').glob('*/attempt-2/journal.sqlite3'))
        with closing(sqlite3.connect(recovery)) as db:
            self.assertEqual(db.execute('SELECT status FROM runs').fetchone()[0], 'interrupted')

    def test_authentication_failure_pauses_without_retry_or_rotation(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            self.finish(journal, row, status='infrastructure_failed',
                        error=('authentication_or_permission', 401, 'upstream_transport'))
            return 'slot-1'
        decisions = self.run_campaign(attempt)
        self.assertEqual(len(self.visited), 1)
        self.assertEqual(decisions[-1]['action'], 'pause')
        self.assertEqual(self.sleeps, [])
        with closing(sqlite3.connect(self.campaign / 'results/journal.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM recovery_attempts').fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT count(*) FROM slots WHERE state!='eligible'").fetchone()[0], 0)

    def test_both_attempts_are_charged_and_recovery_budget_exhaustion_is_selected(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            if len(self.visited) == 1:
                self.finish(journal, row, status='infrastructure_failed', error=('transient', 500, 'upstream_transport'))
            elif len(self.visited) == 2:
                journal.start(row['id'])
                journal.reserve(row['id'], 'b' + row['id'], 2000, 4096, LIMITS)
                journal.forward('b' + row['id'], 'slot-1', LIMITS)
                journal.settle('b' + row['id'], {'classification': 'success', 'status': 200,
                                              'usage': {'prompt_tokens': 30, 'completion_tokens': 10}})
                journal.finish(row['id'], 'budget_exhausted', {'integrity': [], 'oracle': {'outcome_score': .25}})
            else:
                self.finish(journal, row)
            return 'slot-1'
        self.run_campaign(attempt)
        accounting = json.loads((self.campaign / 'results/exports/accounting_all_attempts.json').read_text())
        self.assertEqual(accounting, {'physical_transmissions': 2, 'known_input_tokens': 30,
                                    'known_output_tokens': 10, 'charged_input': 1030,
                                    'charged_output': 4106, 'usage_missing_calls': 1})
        chosen = json.loads((self.campaign / 'results/exports/outcomes_with_recovery.json').read_text())
        self.assertEqual(chosen[0]['status'], 'budget_exhausted')
        self.assertEqual(chosen[0]['attempt_number'], 2)

    def test_crash_before_recovery_starts_resumes_only_that_planned_recovery(self):
        def attempt(journal, row, preferred, **paths):
            self.visited.append(row['id'])
            if len(self.visited) == 1:
                self.finish(journal, row, status='infrastructure_failed', error=('transient', 500, 'upstream_transport'))
            else:
                self.finish(journal, row)
            return 'slot-1'
        with self.assertRaises(RuntimeError):
            run_pending(self.root, self.campaign, self.scope, 'new-study', attempt, lambda j: None,
                        sleep=lambda seconds: (_ for _ in ()).throw(RuntimeError('Crash during cooldown')))
        self.assertEqual(len(self.visited), 1)
        primary = self.rows()[0]
        self.run_campaign(attempt)
        self.assertEqual(len(self.visited), 4)
        self.assertEqual(self.rows()[0], primary)
        self.assertNotIn(primary['id'], self.visited[1:])


if __name__ == '__main__':
    unittest.main()
