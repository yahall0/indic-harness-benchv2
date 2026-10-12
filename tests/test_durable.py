import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from bench.durable import Journal
from bench.rotation import classify
from bench.lease import ControllerLease

LIMITS={'attempt_timeout_sec':600,'max_requests':3,'max_input_tokens':10000,'max_output_tokens':1000,'max_response_tokens':500}

class DurabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.path=Path(self.temp.name)/'journal.sqlite3'
        self.j=Journal(self.path); self.j.plan(['001-file'],'abc'); self.run=self.j.runs()[0]['id']; self.j.start(self.run)
    def tearDown(self): self.j.close(); self.temp.cleanup()
    def test_resume_never_reruns_finished_failure(self):
        self.j.finish(self.run,'agent_failed',{'score':0})
        self.j.close(); self.j=Journal(self.path); self.j.plan(['001-file'],'abc'); self.j.recover()
        self.assertEqual(len(self.j.runs()),3); self.assertEqual(self.j.get(self.run)['status'],'agent_failed')
        with self.assertRaises(ValueError): self.j.start(self.run)
    def test_reservation_and_unknown_usage_survive_crash(self):
        self.j.close()
        script='from bench.durable import Journal; import os,sys; j=Journal(sys.argv[1]); j.reserve(sys.argv[2],"a"*32,1200,500,'+repr(LIMITS)+'); os._exit(17)'
        p=subprocess.run([sys.executable,'-c',script,str(self.path),self.run],capture_output=True)
        self.assertEqual(p.returncode,17)
        self.j=Journal(self.path); self.assertEqual(self.j.get(self.run)['output_reserved'],500)
        self.j.recover(); self.assertEqual(self.j.get(self.run)['status'],'interrupted')
        self.assertEqual(self.j.get(self.run)['requests'],1)
    def test_idempotent_reserve_and_settle(self):
        for _ in range(2): self.j.reserve(self.run,'b'*32,1000,500,LIMITS)
        self.assertEqual(self.j.get(self.run)['requests'],1)
        result={'usage':{'prompt_tokens':90,'completion_tokens':100}}
        for _ in range(2): self.j.settle('b'*32,result)
        r=self.j.get(self.run); self.assertEqual(r['output_reserved'],100); self.assertEqual(r['output_actual'],100)
        self.assertEqual(r['input_bound'],90)
    def test_concurrent_journal_events_are_atomic(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda i:self.j.event(self.run,'parallel',{'i':i}),range(80)))
        self.assertEqual(self.j.db.execute("SELECT COUNT(*) FROM events WHERE kind='parallel'").fetchone()[0],80)
    def test_lease_blocks_duplicate_controller_and_releases(self):
        path=Path(self.temp.name)/'controller.lock'
        with ControllerLease(path):
            script='from bench.lease import ControllerLease; import sys; '+"\nwith ControllerLease(sys.argv[1]): pass"
            p=subprocess.run([sys.executable,'-c',script,str(path)],capture_output=True)
            self.assertNotEqual(p.returncode,0)
        with ControllerLease(path): pass
    def test_provider_overshoot_is_flagged(self):
        self.j.reserve(self.run,'f'*32,50,500,LIMITS)
        response={'usage':{'prompt_tokens':51,'completion_tokens':501}}
        for _ in range(2):
            self.assertTrue(self.j.settle('f'*32,response)['budget_violation'])
        self.assertEqual(self.j.get(self.run)['output_actual'],501)
    def test_forward_ack_retry_never_charges_duplicate_transmission(self):
        call='a'*32; nonce='1'*32
        self.j.reserve(self.run,call,1000,500,LIMITS)
        for _ in range(2): self.assertEqual(self.j.forward(call,'slot-1',LIMITS,nonce),1)
        self.assertEqual(self.j.get(self.run)['requests'],1)
        self.assertEqual(self.j.get(self.run)['output_reserved'],500)
        self.assertEqual(self.j.db.execute('SELECT COUNT(*) FROM forwards').fetchone()[0],1)
        with self.assertRaises(ValueError): self.j.forward(call,'slot-2',LIMITS,nonce)
        self.assertEqual(self.j.forward(call,'slot-1',LIMITS,'2'*32),2)
        self.assertEqual(self.j.get(self.run)['requests'],2)
        self.assertEqual(self.j.get(self.run)['output_reserved'],1000)
        with self.assertRaises(ValueError): self.j.forward(call,'slot-1',LIMITS,'3'*32)
    def test_rejected_ack_retry_never_refunds_twice(self):
        call='e'*32
        self.j.reserve(self.run,call,1000,500,LIMITS)
        self.j.forward(call,'slot-1',LIMITS,'1'*32)
        for _ in range(2): self.j.rejected_forward(call)
        row=self.j.get(self.run)
        self.assertEqual((row['input_bound'],row['output_reserved']),(0,0))
        self.j.forward(call,'slot-1',LIMITS,'2'*32)
        row=self.j.get(self.run)
        self.assertEqual((row['requests'],row['input_bound'],row['output_reserved']),(2,1000,500))
    def test_no_output_overspend_and_retry_accounting(self):
        self.j.reserve(self.run,'c'*32,1000,500,LIMITS)
        self.j.forward('c'*32,'slot-1',LIMITS); self.j.forward('c'*32,'slot-1',LIMITS)
        self.assertEqual(self.j.get(self.run)['requests'],2)
        self.assertEqual(self.j.get(self.run)['output_reserved'],1000)
        with self.assertRaises(ValueError): self.j.forward('c'*32,'slot-1',LIMITS)
        with self.assertRaises(ValueError): self.j.reserve(self.run,'d'*32,1000,500,LIMITS)
    def test_slots_stay_exhausted_across_restart(self):
        self.j.slot_init(['slot-1','slot-2','slot-3','slot-4'])
        self.assertEqual(self.j.choose_slot('slot-1'),'slot-1')
        with self.assertRaises(ValueError): self.j.exhaust_slot('slot-1','rate_limited',self.run)
        self.j.exhaust_slot('slot-1','confirmed_quota_exhaustion',self.run)
        self.j.close(); self.j=Journal(self.path); self.j.slot_init(['slot-1','slot-2','slot-3','slot-4'])
        self.assertEqual(self.j.choose_slot('slot-1'),'slot-2')
        for s in ['slot-2','slot-3','slot-4']: self.j.exhaust_slot(s,'confirmed_quota_exhaustion',self.run)
        with self.assertRaises(ValueError): self.j.choose_slot()
    def test_online_backup_preserves_committed_wal(self):
        dest=Path(self.temp.name)/'backup'; self.j.event(self.run,'test',{'committed':True}); self.j.export(dest)
        b=Journal(dest/'journal-backup.sqlite3')
        try: self.assertEqual(b.get(self.run)['status'],'running')
        finally: b.close()
        lines=[json.loads(x) for x in (dest/'events.jsonl').read_text().splitlines()]
        self.assertEqual(lines[-1]['kind'],'test')

class RotationTests(unittest.TestCase):
    def test_rate_limit_is_not_quota_exhaustion(self):
        for body in [{'error':'rate limit exceeded'},{'error':'too many requests'},{'error':{'message':'token rate limit reached'}},{}]:
            self.assertEqual(classify(429,body),'rate_limited')
    def test_explicit_quota_only(self):
        self.assertEqual(classify(429,{'error':{'code':'insufficient_quota'}}),'quota_exhausted')
        self.assertEqual(classify(429,{'error':'weekly usage limit exceeded'}),'quota_exhausted')
        self.assertEqual(classify(401,{'error':'invalid API key'}),'authentication_or_permission')
        self.assertEqual(classify(503,{}),'transient')

if __name__=='__main__': unittest.main()
