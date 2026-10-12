"""Repair fake checks then one capped real Hindi/Hinglish canary gate."""
import hashlib
import io
import json
import sys
import unittest
import uuid
from contextlib import closing
from pathlib import Path

from bench.credentials import load_keys
from bench.durable import Journal,atomic_json
from bench.lease import ControllerLease
from bench.security import docker,workspace_archive,safe_export
from nextbench.compatibility import _relay,_retire
from nextbench.containers import CampaignContainers
from nextbench_repair.openclaw_config import configuration
from nextbench_repair.collector import Collector

ROOT=Path(__file__).resolve().parents[1]


def sources():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ('nextbench_repair','tests_nextbench_repair') for p in sorted((ROOT/folder).rglob('*.py'))}


def fake(campaign):
    campaign=Path(campaign).resolve();revision=campaign/'revisions/transport-v2'
    log=io.StringIO(); suite=unittest.defaultTestLoader.discover(str(ROOT/'tests_nextbench_repair'))
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (revision/'checks').mkdir(parents=True,exist_ok=True);(revision/'checks/unit-tests.log').write_text(log.getvalue(),encoding='utf-8')
    if not result.wasSuccessful(): raise ValueError('Streaming unit checks failed')
    import nextbench_repair.compatibility as compatibility
    compatibility.Collector=Collector
    report=compatibility.check(revision,'fake')
    import nextbench.relay_check as rotation
    rotation.ROOT=revision; rotation.Collector=Collector
    with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(campaign/'results/controller.lock'):
        accounting=rotation.check_relay()
    accounting['tested_runtime_sources']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        for name in ('nextbench_repair/runtime/relay.py','nextbench_repair/upstream.py','nextbench/contract.py','nextbench_repair/collector.py')}
    atomic_json(revision/'checks/relay-accounting/latest.json',accounting)
    value={'passed':report['passed'] and accounting['passed'],'unit_tests_run':result.testsRun,
           'fake_harness':report['checks'],'relay_accounting':accounting['checks'],
           'accounting_tested_runtime_sources':accounting['tested_runtime_sources'],
           'repair_sources':sources(),'images':json.loads((revision/'config/images.json').read_text()),
           'actual_cloud_transmissions':0}
    atomic_json(revision/'checks/fake-verification.json',value); return value


def cloud(campaign):
    campaign=Path(campaign).resolve();revision=campaign/'revisions/transport-v2'
    fake_report=json.loads((revision/'checks/fake-verification.json').read_text())
    if not fake_report['passed'] or fake_report['repair_sources']!=sources(): raise ValueError('Repair fake gate/source mismatch')
    dest=revision/'probes/hindi-hinglish'
    if (dest/'journal.sqlite3').exists(): raise ValueError('Never automatically replay canary spending')
    images=json.loads((revision/'config/images.json').read_text()); profile=json.loads((revision/'config/model_profile.json').read_text())
    limits=json.loads((revision/'config/probe_budget.json').read_text()); protocol=json.loads((revision/'config/protocol.json').read_text())
    report={'passed':False,'benchmark_attempts':0,'languages':{},'budget':limits,'repair_sources':sources(),'images':images}
    keys=load_keys()
    with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(campaign/'results/controller.lock'),closing(Journal(dest/'journal.sqlite3')) as journal:
        ident=hashlib.sha256(b'transport-v2-hindi-hinglish-canary').hexdigest()[:24]
        journal.db.execute('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',(ident,'independent-receipt-canary','hi-hinglish','transport-v2-separate-probe'))
        journal.start(ident);collector=Collector(journal,ident,limits,list(keys),trace_dir=dest/'inference');collector.start()
        try:
            for language in ('hi','hinglish'):
                box=CampaignContainers(journal,ident,images);proc=None
                try:
                    net,volume=box.internal(),box.workspace();keeper=box.create('helper',volume=volume)
                    agent=box.create('agent',network=net,volume=volume)
                    expected=language+'_verified'; original=expected+'\nनमस्ते — independent fixture\n'
                    fixture="from pathlib import Path; p=Path('/workspace'); (p/'in').mkdir(exist_ok=True); (p/'out').mkdir(exist_ok=True); (p/'in/diagnostic.txt').write_text("+repr(original)+",encoding='utf-8')"
                    docker(['exec',keeper,'python','-c',fixture])
                    proc,token=_relay(box,net,collector,keys,profile,4096,())
                    box.invoke(agent,{'action':'configure','config':configuration(token,profile,protocol)},program='/opt/ihb/agent.py')
                    prompt= ('कार्यशील डायरेक्टरी /workspace है। in/diagnostic.txt पढ़ें। उसकी पहली पंक्ति बिना बदलाव out/receipt.txt में लिखें। इनपुट फ़ाइल को न बदलें। काम पूरा होने पर CHECK_OK लिखें।' if language=='hi' else
                             'Working directory /workspace hai. in/diagnostic.txt padho. Uski pehli line bina badle out/receipt.txt mein likho. Input file ko mat badlo. Kaam poora hone par CHECK_OK bolo.')
                    round_result=box.invoke(agent,{'action':'round','session':'repair-canary-'+language,'round':1,'timeout':240,'thinking':'high','prompt':prompt},timeout=255,program='/opt/ihb/agent.py')
                    atomic_json(dest/language/'round.json',round_result)
                    docker(['kill',agent]); data=workspace_archive(keeper); safe_export(data,dest/language/'artifacts')
                    grader=box.create('grader');box.import_archive(grader,data)
                    code="from pathlib import Path; import json; p=Path('/workspace'); print(json.dumps({'receipt_correct':(p/'out/receipt.txt').is_file() and (p/'out/receipt.txt').read_text(encoding='utf-8').strip()=="+repr(expected)+",'input_preserved':(p/'in/diagnostic.txt').read_text(encoding='utf-8')=="+repr(original)+"}))"
                    checked=json.loads(docker(['exec',grader,'python','-c',code]))
                    value={'passed':all(checked.values()) and round_result['returncode']==0 and collector.paused is None,
                           'checks':checked,'returncode':round_result['returncode'],'collector_pause':collector.paused}
                    report['languages'][language]=value
                    if not value['passed']: break
                finally: _retire(box,proc)
        except Exception as error: report['error_type']=type(error).__name__
        finally:
            collector.close()
            # All owned containers are already retired. Finalize any request
            # killed during a wall/SDK timeout with its full charge retained.
            for call in journal.db.execute("SELECT id FROM calls WHERE run_id=? AND status='reserved'",(ident,)).fetchall():
                journal.settle(call['id'],{'usage':None,'classification':'controller_retired_unsettled_transport','status':0})
            row=journal.get(ident)
            report.update(physical_transmissions=journal.db.execute('SELECT count(*) FROM forwards').fetchone()[0],
                          known_input_tokens=row['input_actual'],known_output_tokens=row['output_actual'],
                          charged_input=row['input_bound'],charged_output=row['output_reserved'],usage_missing_calls=row['usage_missing'],
                          all_owned_resources_removed=not journal.resources())
            report['passed']=set(report['languages'])=={'hi','hinglish'} and all(v['passed'] for v in report['languages'].values()) and report['all_owned_resources_removed'] and row['usage_missing']==0
            journal.finish(ident,'completed' if report['passed'] else 'infrastructure_failed',report)
            journal.export(dest/'checkpoint');atomic_json(dest/'report.json',report)
    return report


if __name__=='__main__':
    value=fake(sys.argv[2]) if sys.argv[1]=='fake' else cloud(sys.argv[2]);print(json.dumps(value,ensure_ascii=False))
    raise SystemExit(0 if value['passed'] else 1)
