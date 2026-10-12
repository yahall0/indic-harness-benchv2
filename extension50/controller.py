"""Serial continuation: exactly 24 primaries; bounded INFRA-only fresh attempts.

Old journals are read-only. Resumes never replay an already-started attempt.
"""
import argparse, hashlib, os, sys, time
from contextlib import ExitStack, closing
from datetime import datetime,timezone
from bench.credentials import load_keys
from bench.durable import Journal, atomic_json, encode
from bench.lease import ControllerLease
from bench.metrics import attempt_metrics, AGENT_OUTCOMES
from bench.security import docker, SecurityError
from bench.containers import emergency_stop
from nextbench.runner import cleanup
from nextbench_repair.retired_accounting import settle_retired_requests
from extension50.attempt import attempt
from extension50.common import *

def now(): return datetime.now(timezone.utc).isoformat()
def batches(): return {k:v/'results'/LABEL for k,v in MODELS.items()}
def frozen():
    info=read(SHARED/'config/freeze.json')
    return source_hashes()==info['file_hashes'] and all(sha(p)==d for p,d in info['protected_runtime_hashes'].items())
def sync_slots(journal, keys):
    journal.slot_init(list(keys))
    # Read all old/extension ledger states, never clear an exhaustion implicitly.
    paths=[Path(p) for p in read(SHARED/'preservation/before.json')['journals']]
    paths+=list(SHARED.glob('checks/**/journal.sqlite3'))
    for batch in batches().values(): paths+=list(batch.rglob('journal.sqlite3'))
    for p in paths:
        with closing(readonly(p)) as db:
            for slot in db.execute("SELECT * FROM slots WHERE state='exhausted'"):
                if slot['id'] in keys and slot['reason']=='confirmed_quota_exhaustion': journal.exhaust_slot(slot['id'],slot['reason'],None)

def export_all():
    categories={t['task_id']:t['category'] for t in read(SHARED/'input/dataset/task_manifest.json')}
    models={}; counts={'primary_terminal':0,'resolved_conditions':0,'total_attempts':0,'running':0,'planned':0}; totals={'transmissions':0,'known_input':0,'known_output':0,'charged_input':0,'charged_output':0,'unknown_usage_calls':0}
    for model,batch in batches().items():
        attempts=[]
        for p in [batch/'journal.sqlite3']+sorted((batch/'recoveries').glob('*/attempt-*/journal.sqlite3')):
            if not p.exists(): continue
            with closing(readonly(p)) as db:
                # Metrics use read-only SQL; do not instantiate a writable legacy journal.
                class View: pass
                j=View();j.db=db
                for raw in db.execute('SELECT * FROM runs ORDER BY rowid'):
                    row=dict(raw); m=attempt_metrics(j,row,categories[row['task']]);m.update(model=model,journal=str(p),attempt_number=1 if p.parent==batch else int(p.parent.name.split('-')[-1]));attempts.append(m)
                    for k,f in [('transmissions','requests'),('known_input','input_actual'),('known_output','output_actual'),('charged_input','input_bound'),('charged_output','output_reserved'),('unknown_usage_calls','usage_missing')]: totals[k]+=row[f]
        chosen=[]
        for tid in TASKS:
            for lang in ['en','hi','hinglish']:
                group=sorted([a for a in attempts if a['task_id']==tid and a['language']==lang],key=lambda a:a['attempt_number'])
                eligible=[a for a in group if a['score_available_for_analysis']]
                value=eligible[0] if eligible else group[-1] if group else None
                if value: chosen.append(value)
        models[model]={'all_attempts':attempts,'resolved':chosen}
        counts['primary_terminal']+=sum(a['attempt_number']==1 and a['status'] not in ['planned','running'] for a in attempts)
        counts['resolved_conditions']+=sum(a['score_available_for_analysis'] for a in chosen)
        counts['total_attempts']+=sum(a['status']!='planned' for a in attempts)
        counts['running']+=sum(a['status']=='running' for a in attempts);counts['planned']+=sum(a['status']=='planned' for a in attempts)
    value={'updated_utc':now(),'logical_task_count':50,'expected_new_primary_conditions':24,'only_new_task_ids':TASKS,'models':models,'counts':counts,'accounting':totals}
    atomic_json(SHARED/'results/progress.json',value)
    return value

def validate_admission():
    if not frozen(): raise ValueError('Frozen extension/dependency sources changed; admission blocked')
    if not verify_preserved(): raise ValueError('Original results/reference preservation failed')
    if (SHARED/'results/STOP_REQUESTED').exists(): raise RuntimeError('Admission hold requested')

def run(authorized):
    if not authorized: raise ValueError('Explicit user launch authorization required')
    keys=load_keys();profiles=read(SHARED/'config/profiles.json');limits=read(SHARED/'config/limits.json');images=read(SHARED/'config/images.json');info=read(SHARED/'config/freeze.json');sel=read(SHARED/'config/selection.json')
    with ExitStack() as stack:
        for path in [ROOT/'results/controller.lock',NEM/'results/controller.lock',SHARED/'results/controller.lock']: stack.enter_context(ControllerLease(path))
        validate_admission()
        record={'pid':os.getpid(),'module':'extension50.controller','started_utc':now(),'freeze_hash':info['runtime_freeze_hash'],'only_24_new_primaries':True,'parent_study_ids':sel['parent_study_ids']}
        atomic_json(SHARED/'results/controller_process.json',record)
        primary={}
        for model,batch in batches().items():
            j=stack.enter_context(closing(Journal(batch/'journal.sqlite3')));primary[model]=j
            cleanup(j)
            for row in j.runs():
                if row['status']=='running':
                    settle_retired_requests(j,row['id']);j.finish(row['id'],'interrupted',{'cause':'controller_restart','automatic_replay':False})
            j.plan(TASKS,sel['parent_study_ids'][model]);sync_slots(j,keys)
            j.export(batch/'checkpoints/latest')
        preferred=None;failures={'oss':0,'nemotron':0};export_all()
        for i,tid in enumerate(TASKS):
            langs=['en','hi','hinglish'];offset=(46+i)%3;langs=langs[offset:]+langs[:offset]
            models=['oss','nemotron'] if i%2==0 else ['nemotron','oss']
            for model in models:
                for lang in langs:
                    batch=batches()[model];j=primary[model];row=next(r for r in j.runs() if r['task']==tid and r['language']==lang)
                    for number in [1,2,3]:
                        if number>1:
                            previous=primary[model].get(row['id']) if number==2 else read(batch/'recoveries'/row['id']/'attempt-2/checkpoints/latest/runs.json')[0]
                            if previous['status']!='infrastructure_failed': break
                            oldresult=__import__('json').loads(previous['result'])
                            if oldresult.get('cleanup_incomplete') or oldresult.get('integrity'): raise SecurityError('Critical runtime/cleanup failure: hold admissions')
                            dest=batch/'recoveries'/row['id']/f'attempt-{number}'
                            recovery=Journal(dest/'journal.sqlite3')
                            ident=hashlib.sha256(f"{row['dataset_hash']}:{tid}:{lang}:{number}".encode()).hexdigest()[:24]
                            recovery.db.execute('INSERT OR IGNORE INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',(ident,tid,lang,row['dataset_hash']))
                            recovery.event(None,'authorized_infrastructure_recovery',{'primary_run_id':row['id'],'attempt_number':number,'no_score_seeking':True})
                            use=recovery;current=recovery.get(ident)
                        else: use=j;current=row;dest=batch
                        try:
                            if current['status']=='running':
                                cleanup(use);settle_retired_requests(use,current['id']);use.finish(current['id'],'interrupted',{'cause':'controller_restart','automatic_replay':False});current=use.get(current['id'])
                            if current['status']=='planned':
                                validate_admission();sync_slots(use,keys)
                                preferred=use.choose_slot(preferred,allowed=list(keys))
                                active={'model':model,'task':tid,'language':lang,'attempt_number':number,'run_id':current['id'],'started_utc':now()}
                                atomic_json(SHARED/'results/active.json',active)
                                config=dict(limits,model=profiles[model]['model'])
                                status,preferred=attempt(use,current,keys,preferred,baseline_root=SHARED/'input',campaign_root=MODELS[model],profile=profiles[model],limits=config,images=images,runtime_freeze_hash=info['runtime_freeze_hash'],destination_root=dest/'runs',checkpoint=dest/'checkpoints/latest')
                                value=use.get(current['id']);r=__import__('json').loads(value['result']); score=r.get('oracle',{}).get('outcome_score')
                                print(encode({**active,'status':status,'score':score,'usage_missing':value['usage_missing'],'finished_utc':now()}),flush=True)
                                use.export(dest/'checkpoints/latest');export_all()
                                if use.resources() or use.db.execute("SELECT 1 FROM calls WHERE status='reserved'").fetchone(): raise SecurityError('Cleanup/accounting unsettled; hold admissions')
                                if status=='quota_paused': raise RuntimeError('All confirmed eligible credential allowances exhausted')
                                if r.get('cleanup_incomplete') or 'runtime_or_export_gate' in r.get('integrity',[]): raise SecurityError('Critical containment/integrity failure; hold admissions')
                                failures[model]=failures[model]+1 if status=='infrastructure_failed' else 0
                                if failures[model]>=3: raise RuntimeError('Sustained provider failure; admissions held after three consecutive INFRA attempts')
                                if status=='infrastructure_failed': time.sleep(30)
                            elif current['status'] not in AGENT_OUTCOMES|{'infrastructure_failed'}: raise RuntimeError('Started unscored condition requires diagnosis; never replay')
                            if use.get(current['id'])['status']!='infrastructure_failed': break
                        finally:
                            if number>1: recovery.close()
        progress=export_all();record.update(finished_utc=now(),status='complete' if progress['counts']['resolved_conditions']==24 else 'held_incomplete')
        atomic_json(SHARED/'results/controller_process.json',record)
        atomic_json(SHARED/'results/completion.json',{'complete':progress['counts']['resolved_conditions']==24,'preserved':verify_preserved(),'counts':progress['counts'],'completed_utc':now()})
        return progress['counts']

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--launch-authorized',action='store_true');args=p.parse_args()
    try: print(encode(run(args.launch_authorized)),flush=True)
    except Exception as e:
        atomic_json(SHARED/'results/hold.json',{'held_utc':now(),'error_type':type(e).__name__,'reason':str(e),'controller_pid':os.getpid(),'restart_automatically':False})
        export_all();raise
