"""One explicitly authorized recovery attempt, without overwriting primary evidence."""
import argparse,csv,hashlib,json,sys
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bench.controller import attempt,campaign_decision,_run_pending
from bench.credentials import load_keys
from bench.durable import Journal,atomic_json,encode
from bench.extension import check_extension
from bench.lease import ControllerLease
from bench.metrics import AGENT_OUTCOMES,attempt_metrics,compare,export
from bench.readiness import readiness


def eligible(source,selected,active):
    if active or source['status']!='infrastructure_failed' or source['task'] not in selected:
        raise ValueError('Recovery requires a stopped campaign and an added-task infrastructure failure')
    result=json.loads(source['result'])
    if result.get('integrity') or result.get('cleanup_incomplete') or result.get('error_type'):
        raise ValueError('Investigate integrity, cleanup or runtime failures before recovery')


def recovery_exports(primary,retry,registry,manifest):
    """Keep primary analysis and provide a transparently labeled recovery sensitivity analysis."""
    export(primary,ROOT/'results/exports',manifest)
    dest=ROOT/'results/exports/infrastructure-recovery';dest.mkdir(parents=True,exist_ok=True)
    categories={t['task_id']:t['category'] for t in manifest}
    rows=[attempt_metrics(primary,r,categories.get(r['task'],'unknown')) for r in primary.runs()]
    retry_row=retry.get(registry['retry_run_id'])
    metric=attempt_metrics(retry,retry_row,categories.get(retry_row['task'],'unknown'))
    metric.update(attempt_number=2,retry_of=registry['source_run_id'],operator_authorized=True)
    atomic_json(dest/'retry_metrics.json',metric)
    repaired=[dict(r) for r in rows]
    if retry_row['status'] in AGENT_OUTCOMES:
        repaired=[dict(metric) if r['run_id']==registry['source_run_id'] else r for r in repaired]
    sensitivity=compare(repaired)
    sensitivity.update(analysis_type='Sensitivity analysis using one operator-authorized infrastructure recovery; primary records unchanged',
        recovery_source_run=registry['source_run_id'],recovery_run=registry['retry_run_id'],
        recovery_used=retry_row['status'] in AGENT_OUTCOMES,
        recovery_policy='Use this sole authorized recovery if it yields any agent outcome, regardless of score; retain primary infrastructure outcome and both costs.',
        attempt_policy_deviation='One manual infrastructure retry was authorized after observing a delivery failure; disclose alongside the single-attempt primary analysis.')
    atomic_json(dest/'analysis_with_recovery.json',sensitivity)
    with (dest/'condition_metrics_with_recovery.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
        for row in repaired:stream.write(encode(row)+'\n')


def run(source_id):
    with ControllerLease(ROOT/'results/controller.lock'),closing(Journal(ROOT/'results/journal.sqlite3')) as primary:
        gate=readiness()
        if not gate['ready']:raise ValueError('Recovery blocked: '+','.join(gate['blocking_gates']))
        selection=json.loads((ROOT/'dataset/extension_selection.json').read_text(encoding='utf-8'))
        source=primary.get(source_id)
        eligible(source,selection['selected_task_ids'],any(r['status']=='running' for r in primary.runs()))
        if primary.resources():raise ValueError('Cleanup must finish before retrying')
        if primary.db.execute("SELECT 1 FROM calls WHERE run_id=? AND status!='settled'",(source_id,)).fetchone():
            raise ValueError('Unsettled inference accounting requires investigation')
        registry_path=ROOT/'results/infrastructure_retries.json'
        if registry_path.exists():raise ValueError('An authorized recovery already exists; refusing duplicate inference')
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        primary.export(ROOT/'results/checkpoints'/('before-infrastructure-retry-'+stamp))
        dest=ROOT/'results/infrastructure-retries'/source_id/'attempt-2'
        dest.mkdir(parents=True,exist_ok=False)
        retry_id=hashlib.sha256((source['dataset_hash']+':'+source_id+':operator-infrastructure-retry:2').encode()).hexdigest()[:24]
        source_artifact=ROOT/'results/runs'/source_id/'run.json'
        digest=hashlib.sha256(source_artifact.read_bytes()).hexdigest()
        registry={'source_run_id':source_id,'retry_run_id':retry_id,'task':source['task'],'language':source['language'],
            'attempt_number':2,'authorization':'User explicitly requested checking the infrastructure error and retrying this condition',
            'authorized_at_utc':datetime.now(timezone.utc).isoformat(),'journal':str(dest/'journal.sqlite3'),
            'status':'preparing','primary_preserved':True,'same_protocol':True,'automatic_retries':False}
        atomic_json(registry_path,registry)
        keys=load_keys();preferred=json.loads(source['result']).get('credential_slot')
        manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text(encoding='utf-8'))
        with closing(Journal(dest/'journal.sqlite3')) as retry:
            retry.db.execute('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',
                             (retry_id,source['task'],source['language'],source['dataset_hash']))
            for slot in primary.slot_state():
                retry.db.execute('INSERT OR REPLACE INTO slots(id,state,reason,changed) VALUES(?,?,?,?)',
                                 tuple(slot[k] for k in ('id','state','reason','changed')))
            retry.event(retry_id,'operator_authorized_infrastructure_retry',registry)
            primary.event(source_id,'operator_authorized_infrastructure_retry',registry)
            registry['status']='running';atomic_json(registry_path,registry)
            print(json.dumps({'recovery':'started','task':source['task'],'language':source['language'],'retry_id':retry_id}),flush=True)
            status,preferred=attempt(retry,retry.get(retry_id),keys,preferred,destination_root=dest/'runs')
            for slot in retry.slot_state():
                if slot['state']=='exhausted' and any(s['id']==slot['id'] and s['state']!='exhausted' for s in primary.slot_state()):
                    primary.exhaust_slot(slot['id'],'confirmed_quota_exhaustion',None)
            assert primary.get(source_id)==source,'Original primary attempt changed'
            assert hashlib.sha256(source_artifact.read_bytes()).hexdigest()==digest,'Original saved outcome changed'
            check_extension()
            saved=retry.get(retry_id);result=json.loads(saved['result'])
            registry.update(status=status,finished_utc=datetime.now(timezone.utc).isoformat(),score=result.get('oracle',{}).get('outcome_score'))
            atomic_json(registry_path,registry)
            primary.event(source_id,'operator_infrastructure_retry_finished',registry)
            recovery_exports(primary,retry,registry,manifest)
            decision=campaign_decision(retry,saved)
            print(json.dumps({'recovery':'finished','status':status,'score':registry['score'],'primary_preserved':True,'action':decision['action']}),flush=True)
            if decision['action']=='continue':
                print(json.dumps({'campaign':'resuming_unstarted_conditions_only'}),flush=True)
                _run_pending(primary,keys,preferred,checkpoint=ROOT/'results/checkpoints/latest')
                recovery_exports(primary,retry,registry,manifest)
            primary.export(ROOT/'results/checkpoints/latest')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    run(parser.parse_args().run)
