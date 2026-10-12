"""Trusted controller safeguards; no model calls or task code on the host."""
import copy
import hashlib
import json
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from unittest.mock import patch

from bench.durable import Journal,atomic_json
from nextbench_repair.collector import Collector
from nextbench_repair.runner import baseline_unchanged,clear_repair_hold,start,validate_metadata
from nextbench_repair.openclaw_config import configuration

ROOT=Path(__file__).resolve().parents[1]


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.folder=ROOT/'tmp/nextbench-tests'/('repair-'+uuid.uuid4().hex)
        self.folder.mkdir(parents=True)

    def tearDown(self):
        # Remove only files created by this test, then empty directories. No
        # recursive deletion, shell crossing, or computed external target.
        assert self.folder.resolve().is_relative_to((ROOT/'tmp/nextbench-tests').resolve())
        entries=sorted(self.folder.rglob('*'),key=lambda p:len(p.parts),reverse=True)
        for p in entries:
            assert p.resolve().is_relative_to(self.folder.resolve())
            p.rmdir() if p.is_dir() else p.unlink()
        self.folder.rmdir()

    def test_resume_without_authorization_never_loads_keys(self):
        with patch('nextbench_repair.runner.load_keys') as keys:
            with self.assertRaises(ValueError): start(self.folder)
            keys.assert_not_called()

    def test_only_owned_repair_hold_can_be_cleared(self):
        revision=self.folder/'revision'; stop=self.folder/'results/STOP_REQUESTED'
        for hold in ({},{'admission_hold':True,'created_by':'operator'}):
            atomic_json(stop,hold)
            with self.assertRaises(ValueError): clear_repair_hold(self.folder,revision)
            self.assertTrue(stop.exists())
        own={'admission_hold':True,'created_by':'trusted monitoring controller in this chat','finish_current_attempt':True}
        atomic_json(stop,own);clear_repair_hold(self.folder,revision)
        self.assertFalse(stop.exists())
        self.assertEqual(json.loads((revision/'checks/hold-cleared-on-authorized-resume.json').read_text()),own)

    def test_capability_digest_thinking_and_context_changes_block(self):
        profile={'model':'nemotron-3-super','provider_advertised_digest':'expected','provider_context_window':262144}
        live={'tags':[{'name':profile['model'],'digest':'expected'}],
              'show':{profile['model']:{'thinking':{'values':[False,True],'default':True},
                      'capabilities':['completion','tools','thinking'],'model_info':{'x.context_length':262144}}}}
        validate_metadata(live,profile)
        for change in ('digest','thinking','tools','context'):
            bad=copy.deepcopy(live);show=bad['show'][profile['model']]
            if change=='digest': bad['tags'][0]['digest']='changed'
            elif change=='thinking': show['thinking']['default']=False
            elif change=='tools': show['capabilities'].remove('tools')
            else: show['model_info']['x.context_length']=65536
            with self.assertRaises(ValueError): validate_metadata(bad,profile)

    def test_baseline_shared_file_change_blocks(self):
        file=self.folder/'trusted.txt';file.write_text('original')
        atomic_json(self.folder/'dataset/freeze.json',{'file_hashes':{'trusted.txt':hashlib.sha256(file.read_bytes()).hexdigest()}})
        self.assertTrue(baseline_unchanged(self.folder));file.write_text('changed')
        self.assertFalse(baseline_unchanged(self.folder))

    def test_provider_timeout_changes_only_transport_and_remains_bounded(self):
        from nextbench.openclaw_config import configuration as original
        profile=json.loads((ROOT/'campaigns/nemotron-3-super-20261001/config/model_profile.json').read_text())
        limits=json.loads((ROOT/'campaigns/nemotron-3-super-20261001/config/protocol.json').read_text())
        before=original('FAKE_ATTEMPT_TOKEN',profile,limits)
        after=configuration('FAKE_ATTEMPT_TOKEN',profile,limits)
        self.assertEqual(after['models']['providers']['ihb'].pop('timeoutSeconds'),210)
        self.assertEqual(after,before)
        short=configuration('FAKE_ATTEMPT_TOKEN',profile,dict(limits,attempt_timeout_sec=60))
        self.assertEqual(short['models']['providers']['ihb']['timeoutSeconds'],60)

    def test_failed_request_trace_and_response_are_independently_idempotent(self):
        journal=Journal(self.folder/'journal.sqlite3');ident='a'*24
        journal.db.execute('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',(ident,'trusted-test','hi','test'))
        journal.start(ident)
        collector=Collector(journal,ident,{'max_requests':6,'max_input_tokens':200000,'max_output_tokens':16384},['slot-1'],trace_dir=self.folder/'traces')
        collector.start()
        def post(payload):
            request=urllib.request.Request('http://127.0.0.1:'+str(collector.server.server_port)+'/trace',
                json.dumps(payload).encode(),{'Authorization':'Bearer '+collector.token,'Content-Type':'application/json'})
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=5) as response:
                return response.status
        try:
            for phase in ('request','error','response'):
                payload={'call_id':ident,'phase':phase,'request':{'model':'nemotron-3-super'}}
                if phase!='request': payload['response']={'stage':phase}
                self.assertEqual(post(payload),200);self.assertEqual(post(payload),200)
            self.assertIsNone(collector.paused)
            self.assertEqual(len(list((self.folder/'traces').glob('*.json'))),3)
            with self.assertRaises(urllib.error.HTTPError):
                post({'call_id':ident,'phase':'response','response':{'changed':True}})
            self.assertEqual(collector.paused,'Conflicting inference trace')
        finally:
            collector.close();journal.close()


if __name__=='__main__': unittest.main()
