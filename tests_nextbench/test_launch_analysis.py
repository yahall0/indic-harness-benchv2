import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from bench.durable import Journal
from bench.lease import ControllerLease
from nextbench import runner
from nextbench.analysis import export, paired_baseline
from nextbench.monitor import snapshot
from nextbench.recovery import _plan, _open_recovery
from nextbench.stop import stop


class LaunchAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.parent = Path(__file__).resolve().parents[1] / 'tmp/nextbench-tests'
        self.parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='launch-', dir=self.parent)
        self.root = Path(self.temp.name)
        self.campaign = self.root / 'campaigns/test'
        self.scope = {'selection_id':'selected', 'baseline_study_id':'old',
                      'conditions':[{'task':'001-file','language':l} for l in ('en','hi','hinglish')]}

    def tearDown(self):
        self.assertTrue(self.root.resolve().is_relative_to(self.parent.resolve()))
        self.temp.cleanup()

    def test_launch_without_authorization_never_reads_credentials_or_calls_provider(self):
        with patch('nextbench.runner.load_keys') as keys, patch('nextbench.runner.metadata') as metadata:
            with self.assertRaisesRegex(ValueError, 'authorization'):
                runner.start(self.campaign)
            keys.assert_not_called(); metadata.assert_not_called()

    def test_recovery_export_selects_zero_or_budget_and_retains_whole_task_attrition(self):
        with closing(Journal(self.campaign / 'results/journal.sqlite3')) as primary:
            _plan(primary, self.scope, 'new-study')
            rows = primary.runs()
            primary.start(rows[0]['id']); primary.finish(rows[0]['id'], 'infrastructure_failed', {'integrity':[]})
            with closing(_open_recovery(primary, primary.get(rows[0]['id']), self.campaign)[0]) as recovery:
                row = recovery.runs()[0]; recovery.start(row['id'])
                recovery.finish(row['id'], 'budget_exhausted', {'oracle':{'outcome_score':0},'integrity':[]})
            for row in rows[1:]:
                primary.start(row['id']); primary.finish(row['id'],'completed',{'oracle':{'outcome_score':1},'integrity':[]})
            export(primary, self.campaign, [{'task_id':'001-file','category':'test'}])
        dest = self.campaign / 'results/exports'
        chosen = json.loads((dest / 'recovery_inclusive_metrics.json').read_text())
        self.assertEqual(chosen[0]['original_score'],0)
        self.assertEqual(chosen[0]['status'],'budget_exhausted')
        self.assertEqual(chosen[0]['attempt_number'],2)
        self.assertEqual(len(json.loads((dest / 'all_attempt_metrics.json').read_text())),4)
        self.assertEqual(json.loads((dest / 'primary_analysis.json').read_text())['complete_triplets'],0)
        self.assertEqual(json.loads((dest / 'recovery_inclusive_analysis.json').read_text())['complete_triplets'],1)
        self.assertEqual(json.loads((dest / 'primary_analysis_vs_baseline.json').read_text())['paired_task_triplets'],0)

    def test_cross_model_pairing_excludes_entire_task_and_preserves_signed_differences(self):
        baseline = [{'task_id':task,'language':lang,'original_score':'0.25','full_completion':'0'}
                    for task in ('a','b') for lang in ('en','hi','hinglish')]
        future = [{**r,'original_score':.5,'full_completion':0,'score_available_for_analysis':True,'agent_outcome':True} for r in baseline]
        future[3]['agent_outcome'] = False
        value = paired_baseline(future, baseline)
        self.assertEqual(value['paired_task_ids'],['a'])
        self.assertEqual(value['excluded_future_task_ids'],['b'])
        self.assertEqual([e['score_difference_pp'] for e in value['estimates']],[25,25,25])

    def test_monitor_is_read_only_and_handles_recovery_without_changing_journals(self):
        with closing(Journal(self.campaign / 'results/journal.sqlite3')) as primary:
            _plan(primary,self.scope,'new-study')
            row = primary.runs()[0]
            with closing(_open_recovery(primary,row,self.campaign)[0]): pass
        paths = list(self.campaign.rglob('journal.sqlite3'))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        value = snapshot(self.campaign)
        self.assertEqual(len(value['primary']),3)
        self.assertEqual(len(value['recovery']),1)
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_emergency_stop_visits_only_registered_campaign_journals(self):
        with closing(Journal(self.campaign / 'results/journal.sqlite3')) as primary:
            _plan(primary,self.scope,'new-study')
            with closing(_open_recovery(primary,primary.runs()[0],self.campaign)[0]): pass
        visited = []
        with patch('nextbench.stop.campaign_path',return_value=self.campaign), patch('nextbench.stop.emergency_stop',side_effect=lambda j: visited.append(j.path) or []):
            result = stop(self.campaign)
        self.assertTrue(result['further_admission_blocked'])
        self.assertEqual(len(visited),2)
        self.assertTrue(all(p.is_relative_to(self.campaign) for p in visited))
        self.assertTrue((self.campaign / 'results/STOP_REQUESTED').exists())

    def test_evidence_source_fingerprint_detects_edit(self):
        path = self.root / 'evidence.py'; path.write_text('before')
        field = {path.relative_to(runner.ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}
        self.assertTrue(runner.evidence_current({'hashes':field},'hashes'))
        path.write_text('after')
        self.assertFalse(runner.evidence_current({'hashes':field},'hashes'))


if __name__ == '__main__': unittest.main()
