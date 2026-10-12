import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bench.controller import campaign_decision,_run_pending
from bench.durable import Journal

LIMITS={'attempt_timeout_sec':600,'max_requests':30,'max_input_tokens':200000,
        'max_output_tokens':16000,'max_response_tokens':4096}


class CampaignPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.j=Journal(Path(self.temp.name)/'journal.sqlite3')
        self.j.plan(['test-task'],'test-study')

    def tearDown(self):
        self.j.close(); self.temp.cleanup()

    def provider_failure(self,row,classification='ambiguous_transport',status=0,*,settle=True,secondary=False):
        self.j.start(row['id'])
        call='a'+row['id']
        self.j.reserve(row['id'],call,10000,4096,LIMITS)
        self.j.forward(call,'slot-1',LIMITS)
        if settle:
            self.j.settle(call,{'classification':classification,'status':status,'usage':None,'slot':'slot-1'})
        self.j.event(row['id'],'provider_pause',{'classification':classification,'status':status,'call_id':call})
        if secondary:
            self.j.event(row['id'],'provider_pause',{'classification':'relay_accounting_gate','call_id':call,
                'settled':True,'stage':'upstream_transport','upstream_status':status,'error_type':'BrokenPipeError'})
        self.j.finish(row['id'],'infrastructure_failed',{'pause_reason':classification,'integrity':[]})
        return self.j.get(row['id'])

    def test_confirmed_timeout_continues_without_releasing_unknown_usage(self):
        row=self.provider_failure(self.j.runs()[0],secondary=True)
        self.assertEqual(campaign_decision(self.j,row)['action'],'continue')
        self.assertEqual(row['output_reserved'],4096)
        self.assertEqual(row['input_bound'],10000)
        self.assertEqual(row['usage_missing'],1)

    def test_http_500_and_rate_limit_continue(self):
        for row,classification,status in zip(self.j.runs(),['transient','rate_limited','transient'],[500,429,503]):
            saved=self.provider_failure(row,classification,status)
            self.assertTrue(campaign_decision(self.j,saved)['provider_failure'])

    def test_unsettled_call_stops(self):
        saved=self.provider_failure(self.j.runs()[0],settle=False)
        self.assertEqual(campaign_decision(self.j,saved)['action'],'pause')

    def test_authentication_or_unknown_http_error_stops(self):
        for row,classification,status in zip(self.j.runs(),['authentication_or_permission','provider_error','transient'],[401,400,401]):
            saved=self.provider_failure(row,classification,status)
            self.assertEqual(campaign_decision(self.j,saved)['action'],'pause')

    def test_integrity_cleanup_and_runtime_errors_stop(self):
        saved=self.provider_failure(self.j.runs()[0])
        for additions in [{'integrity':['runtime_or_export_gate']},{'cleanup_incomplete':True},{'error_type':'SecurityError'}]:
            row={**saved,'result':json.dumps({**json.loads(saved['result']),**additions})}
            self.assertEqual(campaign_decision(self.j,row)['action'],'pause')
        self.j.resource('container','owned-canary',saved['id'])
        self.assertEqual(campaign_decision(self.j,saved)['action'],'pause')

    def test_genuine_accounting_error_stops_even_after_provider_error(self):
        saved=self.provider_failure(self.j.runs()[0])
        self.j.event(saved['id'],'provider_pause',{'classification':'relay_accounting_gate',
            'call_id':'a'+saved['id'],'stage':'settlement','error_type':'URLError','settled':False})
        self.assertEqual(campaign_decision(self.j,saved)['action'],'pause')

    def test_budget_integrity_event_stops(self):
        saved=self.provider_failure(self.j.runs()[0])
        self.j.event(saved['id'],'budget_integrity_violation',{'call_id':'a'+saved['id']})
        self.assertEqual(campaign_decision(self.j,saved)['action'],'pause')

    def test_plain_infra_without_evidence_stops(self):
        row=self.j.runs()[0]; self.j.start(row['id']); self.j.finish(row['id'],'infrastructure_failed',{})
        self.assertEqual(campaign_decision(self.j,self.j.get(row['id']))['action'],'pause')

    def test_single_failure_then_next_task_is_processed_without_retry_or_key_switch(self):
        original=self.provider_failure(self.j.runs()[0]); visited=[]; sleeps=[]
        def fake_attempt(j,row,keys,preferred):
            visited.append((row['id'],preferred))
            if len(visited)==1: self.provider_failure(row,'transient',500)
            else: j.start(row['id']); j.finish(row['id'],'completed',{'integrity':[]})
            return j.get(row['id'])['status'],'slot-1'
        with patch('bench.controller.attempt',side_effect=fake_attempt):
            _run_pending(self.j,{'slot-1':'fake'},'slot-1',sleep=sleeps.append,
                         checkpoint=Path(self.temp.name)/'checkpoint')
        self.assertEqual(len(visited),2)
        self.assertNotIn(original['id'],[r[0] for r in visited])
        self.assertEqual(self.j.get(original['id']),original)
        self.assertEqual([r[1] for r in visited],['slot-1','slot-1'])
        self.assertEqual(sleeps,[30])
        self.assertEqual(sum(r['status']=='completed' for r in self.j.runs()),1)
        backup=Journal(Path(self.temp.name)/'checkpoint/journal-backup.sqlite3')
        try: self.assertEqual(backup.get(original['id']),original)
        finally: backup.close()

    def test_three_consecutive_provider_failures_pause_and_explicit_resume_skips_failed_attempts(self):
        self.j.plan(['unstarted-task'],'test-study'); visited=[]; sleeps=[]
        def fake_attempt(j,row,keys,preferred):
            visited.append(row['id']); self.provider_failure(row)
            return 'infrastructure_failed','slot-1'
        with patch('bench.controller.attempt',side_effect=fake_attempt):
            _run_pending(self.j,{'slot-1':'fake'},sleep=sleeps.append)
        self.assertEqual(len(visited),3); self.assertEqual(sleeps,[30,30])
        self.assertEqual(sum(r['status']=='planned' for r in self.j.runs()),3)
        self.j.close(); self.j=Journal(Path(self.temp.name)/'journal.sqlite3')
        failed_ids=set(visited)
        def successful_attempt(j,row,keys,preferred):
            self.assertNotIn(row['id'],failed_ids)
            j.start(row['id']); j.finish(row['id'],'completed',{'integrity':[]})
            return 'completed','slot-1'
        with patch('bench.controller.attempt',side_effect=successful_attempt) as attempt:
            _run_pending(self.j,{'slot-1':'fake'},sleep=sleeps.append)
            self.assertEqual(attempt.call_count,3)
        self.assertEqual(sum(r['status']=='infrastructure_failed' for r in self.j.runs()),3)
        self.assertEqual(sum(r['status']=='completed' for r in self.j.runs()),3)

    def test_success_resets_failure_streak(self):
        self.j.plan(['second-task'],'test-study'); visited=[]
        def fake_attempt(j,row,keys,preferred):
            visited.append(row['id'])
            if len(visited) in (1,3,4): self.provider_failure(row)
            else: j.start(row['id']); j.finish(row['id'],'completed',{'integrity':[]})
            return j.get(row['id'])['status'],'slot-1'
        with patch('bench.controller.attempt',side_effect=fake_attempt):
            _run_pending(self.j,{'slot-1':'fake'},sleep=lambda seconds:None)
        self.assertEqual(len(visited),6)

    def test_fatal_failure_leaves_later_attempts_unstarted(self):
        visited=[]
        def fake_attempt(j,row,keys,preferred):
            visited.append(row['id']); self.provider_failure(row,'authentication_or_permission',401)
            return 'infrastructure_failed','slot-1'
        with patch('bench.controller.attempt',side_effect=fake_attempt):
            _run_pending(self.j,{'slot-1':'fake'},sleep=lambda seconds:None)
        self.assertEqual(len(visited),1)
        self.assertEqual(sum(r['status']=='planned' for r in self.j.runs()),2)


if __name__=='__main__': unittest.main()
