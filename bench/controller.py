"""Serial matched-triplet controller. Live start requires explicit freeze and readiness."""
from __future__ import annotations
import hashlib
import json
import os
import secrets
import subprocess
import threading
import time
from pathlib import Path
from bench.collector import Collector
from bench.containers import Containers,emergency_stop
from bench.credentials import load_keys
from bench.durable import Journal,atomic_json
from bench.openclaw_config import configuration
from bench.security import docker,workspace_archive,safe_export,validate_container,SecurityError
from bench.lease import ControllerLease

ROOT=Path(__file__).resolve().parents[1]

def atomic_bytes(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); temp=path.with_name(path.name+'.tmp')
    with temp.open('wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(temp,path)

def attempt(journal,row,keys,preferred=None,*,destination_root=None):
    limits=json.loads((ROOT/'config/protocol.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text(encoding='utf-8'))
    task=next(t for t in manifest if t['task_id']==row['task'])
    limits['attempt_timeout_sec']=task['attempt_timeout_sec']
    journal.start(row['id'])
    destination=Path(destination_root or ROOT/'results/runs')/row['id']; destination.mkdir(parents=True,exist_ok=True)
    checkpoint=Path(destination_root).parent/'checkpoints/latest' if destination_root else ROOT/'results/checkpoints/latest'
    box=Containers(journal,row['id']); collector=Collector(journal,row['id'],limits,list(keys),preferred,trace_dir=destination/'inference')
    port=collector.start(); relay_proc=None; agent=None; latest=None; keeper=None; mock=None
    current_freeze=json.loads((ROOT/'dataset/freeze.json').read_text(encoding='utf-8'))
    result={'task':row['task'],'language':row['language'],'rounds':[],'integrity':[],
            'runtime_freeze_hash':current_freeze['dataset_hash'],'study_id':row['dataset_hash']}
    status='infrastructure_failed'; begin=time.monotonic()
    try:
        prepared,state=box.prepared(row['task'])
        net=box.internal(); volume=box.workspace()
        # A non-agent holder keeps tmpfs data mounted while the agent is killed before grading.
        keeper=box.create('helper',volume=volume,command=('sleep','900'))
        agent=box.create('agent',network=net,volume=volume)
        box.import_archive(agent,prepared)
        token=secrets.token_hex(32)
        box.invoke(agent,{'action':'configure','config':configuration(token,limits['model'])},program='/opt/ihb/agent.py')
        # Trusted relay gets one ordinary egress network and the task's private internal network.
        relay=box.name('relay'); box.record('container',relay)
        from bench.security import restricted_args
        args=restricted_args(relay); args[args.index('--network')+1]='bridge'
        docker(['create','-i',*args,box.images['relay']['id']])
        box.bind('container',relay)
        docker(['network','connect','--alias','ihb-relay',net,relay])
        validate_container(json.loads(docker(['inspect',relay]))[0],network='bridge',relay_internal_network=net)
        relay_proc=subprocess.Popen(['docker','start','-ai',relay],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        relay_config={'keys':keys,'model':limits['model'],'upstream':limits['upstream'],
            'accounting':f'http://host.docker.internal:{port}','accounting_token':collector.token,
            'agent_token':token,'max_response_tokens':limits['max_response_tokens']}
        relay_proc.stdin.write((json.dumps(relay_config)+'\n').encode()); relay_proc.stdin.flush()
        # Read one small readiness line, bounded by the controller deadline.
        ready=[]
        rt=threading.Thread(target=lambda:ready.append(relay_proc.stdout.readline(4096)),daemon=True); rt.start(); rt.join(20)
        if not ready or not json.loads(ready[0]).get('ready'): raise SecurityError('Relay did not become ready')
        if row['task']=='022-local-rest-api-summary':
            from bench.task_services import start_mock
            mock=start_mock(box,agent,net,volume)
        status='completed'
        for index,prompt_name in enumerate(task['source_prompt_files']):
            remaining=int(limits['attempt_timeout_sec']-(time.monotonic()-begin))
            if remaining<=0: status='timeout'; break
            prompt=(ROOT/'tasks'/row['task']/'prompts'/row['language']/prompt_name).read_text(encoding='utf-8')
            prompt=prompt.replace('$WORKSPACE','/workspace')
            for key,value in state.items(): prompt=prompt.replace('$'+key,str(value))
            atomic_json(destination/f'round-{index+1}-prompt.json',{'prompt':prompt,'sha256':hashlib.sha256(prompt.encode()).hexdigest()})
            journal.event(row['id'],'round_started',{'round':index+1,'prompt_file':prompt_name})
            completed=[]; failed=[]
            def run_round():
                try: completed.append(box.invoke(agent,{'action':'round','session':'ihb-'+row['id'],'round':index+1,
                    'timeout':remaining,'prompt':prompt},timeout=remaining+10,program='/opt/ihb/agent.py'))
                except Exception as e: failed.append(type(e).__name__)
            thread=threading.Thread(target=run_round,daemon=True); thread.start()
            while thread.is_alive():
                thread.join(0.5)
                if collector.paused or time.monotonic()-begin>=limits['attempt_timeout_sec']:
                    docker(['kill',agent]); break
            thread.join(15)
            if collector.paused:
                status='quota_paused' if 'credential' in collector.paused.lower() else 'budget_exhausted' if 'budget' in collector.paused.lower() and 'violation' not in collector.paused.lower() else 'infrastructure_failed'
            elif time.monotonic()-begin>=limits['attempt_timeout_sec']: status='timeout'
            elif failed or not completed: status='infrastructure_failed'
            if completed:
                atomic_json(destination/f'round-{index+1}.json',completed[0]); result['rounds'].append(completed[0])
                journal.event(row['id'],'round_finished',{'round':index+1,'returncode':completed[0]['returncode']})
                if status=='completed' and completed[0]['returncode']!=0: status='agent_failed'
            if status in ('timeout','budget_exhausted','quota_paused','infrastructure_failed'): break
            docker(['pause',agent])
            latest=workspace_archive(agent)
            atomic_bytes(destination/f'round-{index+1}-workspace.tar',latest)
            # Agent stays paused during all hook inspection in a distinct no-network grader.
            hook=box.grade(row['task'],latest,action='after_round',state=state,round_index=index,ok=status=='completed')
            state=hook['state']; journal.event(row['id'],'round_hook_checked',{'round':index+1,'hook_ok':hook['hook_ok']})
            if not hook['hook_ok']:
                result['integrity'].extend(hook.get('integrity_violations',[])); status='integrity_failed'
            docker(['unpause',agent])
            journal.export(checkpoint)
            if status in ('agent_failed','integrity_failed'): break
        # Stop EVERY agent process before running submitted code in the grader.
        if agent:
            info=json.loads(docker(['inspect',agent]))[0]
            if info['State']['Running']:
                if info['State'].get('Paused'): docker(['unpause',agent])
                docker(['kill',agent])
            if mock:
                docker(['kill',mock])
                from bench.security import bounded_docker
                helper_logs=bounded_docker(['logs',mock],max_bytes=1024*1024)
                atomic_bytes(destination/'task-service.jsonl',helper_logs)
            if keeper: latest=workspace_archive(keeper)
            if latest:
                atomic_bytes(destination/'workspace.tar',latest)
                safe_export(latest,destination/'artifacts')
                result.update(box.grade(row['task'],latest))
                result['integrity'].extend(result.get('integrity_violations',[]))
                if mock:
                    observed=[json.loads(l)['path'] for l in helper_logs.decode().splitlines()]
                    access=destination/'artifacts/out/api_access.log'
                    if (access.read_text(encoding='utf-8').splitlines() if access.is_file() else [])!=observed:
                        result['integrity'].append('task_service_log_modified')
                if result['integrity'] and status=='completed': status='integrity_failed'
        result.update(elapsed_sec=round(time.monotonic()-begin,3),pause_reason=collector.paused,
                      credential_slot=collector.preferred,token_budget_method='conservative_utf8_byte_bound',
                      unavailable_metrics=['exact_preflight_prompt_tokens','tokenizer_causal_effect'])
    except Exception as e:
        result['error_type']=type(e).__name__; result['error_summary']='Trusted runtime or integrity gate failed; inspect controller events'
        if isinstance(e,SecurityError): result['integrity'].append('runtime_or_export_gate')
        status='infrastructure_failed'
    finally:
        # Stop containers first. Keys/accounting endpoint are retired only afterwards.
        try: box.cleanup()
        except Exception:
            result['cleanup_incomplete']=True; status='infrastructure_failed'
        collector.close()
        if relay_proc:
            relay_proc.stdin.close()
            try: relay_proc.wait(timeout=5)
            except subprocess.TimeoutExpired: relay_proc.kill()
        journal.finish(row['id'],status,result)
        atomic_json(destination/'run.json',journal.get(row['id']))
        journal.export(checkpoint)
        if destination_root is None:
            from bench.metrics import export
            export(journal,ROOT/'results/exports',manifest)
    return status,collector.preferred

def campaign_decision(journal,row):
    """Continue only after a saved, settled provider failure with safe cleanup."""
    result=json.loads(row.get('result') or '{}')
    pause={'action':'pause','reason':row['status']}
    if result.get('integrity') or result.get('cleanup_incomplete') or result.get('error_type'):
        return {**pause,'reason':'runtime_integrity_or_cleanup_failure'}
    if row['status'] in ('completed','agent_failed','timeout','budget_exhausted'):
        return {'action':'continue','reason':row['status'],'provider_failure':False}
    if row['status']!='infrastructure_failed': return pause
    classification=result.get('pause_reason')
    statuses={'ambiguous_transport':{0},'transient':{408,425,500,502,503,504},'rate_limited':{429}}
    if classification not in statuses: return pause
    with journal.lock:
        calls=[dict(r) for r in journal.db.execute('SELECT * FROM calls WHERE run_id=? ORDER BY rowid',(row['id'],))]
        events=[dict(r) for r in journal.db.execute('SELECT kind,payload FROM events WHERE run_id=? ORDER BY seq',(row['id'],))]
        resources=journal.db.execute("SELECT COUNT(*) FROM resources WHERE run_id=? AND status!='removed'",(row['id'],)).fetchone()[0]
    if resources or not calls or any(c['status']!='settled' for c in calls):
        return {**pause,'reason':'incomplete_cleanup_or_accounting'}
    response=json.loads(calls[-1]['response'] or '{}'); call_id=calls[-1]['id']
    if response.get('classification')!=classification or response.get('status') not in statuses[classification]:
        return {**pause,'reason':'provider_failure_not_confirmed'}
    confirmed=False
    for event in events:
        if event['kind']=='budget_integrity_violation': return {**pause,'reason':'accounting_integrity_failure'}
        if event['kind']!='provider_pause': continue
        payload=json.loads(event['payload'])
        if payload.get('call_id')!=call_id: return {**pause,'reason':'unexpected_provider_pause'}
        if payload.get('classification')==classification and payload.get('status')==response.get('status'):
            confirmed=True
        # Killing the paused agent can break response delivery AFTER durable settlement.
        # This specific secondary error is not an accounting failure.
        elif not (confirmed and payload.get('classification')=='relay_accounting_gate'
                  and payload.get('settled') is True
                  and payload.get('error_type') in ('BrokenPipeError','ConnectionResetError')
                  and payload.get('stage') in ('upstream_transport','agent_delivery')
                  and payload.get('upstream_status')==response.get('status')):
            return {**pause,'reason':'relay_or_accounting_failure'}
    if not confirmed: return {**pause,'reason':'provider_pause_not_confirmed'}
    return {'action':'continue','reason':classification,'provider_failure':True}


def _run_pending(journal,keys,preferred=None,*,sleep=time.sleep,checkpoint=None,destination_root=None):
    # Each explicit controller start is a fresh session, never an automatic restart.
    # Already-started conditions remain terminal; only new conditions can be admitted.
    consecutive=0
    journal.event(None,'campaign_session_started',{'provider_failure_limit':3,'provider_cooldown_sec':30,'automatic_rerun':False})
    for row in journal.runs():
        if row['status']!='planned': continue
        options={'destination_root':destination_root} if destination_root is not None else {}
        status,preferred=attempt(journal,row,keys,preferred,**options)
        saved=journal.get(row['id']); decision=campaign_decision(journal,saved)
        consecutive=consecutive+1 if decision.get('provider_failure') else 0
        if consecutive>=3: decision={'action':'pause','reason':'three_consecutive_provider_failures'}
        payload={'run_id':row['id'],'task':row['task'],'language':row['language'],
                 'status':status,**decision,'consecutive_provider_failures':consecutive}
        journal.event(row['id'],'campaign_paused' if decision['action']=='pause' else 'campaign_continuing',payload)
        if checkpoint: journal.export(checkpoint)
        print(json.dumps(payload),flush=True)
        if decision['action']=='pause': break
        if decision.get('provider_failure'):
            print(json.dumps({'campaign':'cooldown','seconds':30,'reason':decision['reason']}),flush=True)
            sleep(30)


def _start_locked():
    from bench.readiness import readiness
    gate=readiness()
    if not gate['ready']: raise ValueError('Live start blocked: '+', '.join(gate['blocking_gates']))
    freeze=json.loads((ROOT/'dataset/freeze.json').read_text(encoding='utf-8')); keys=load_keys()
    journal=Journal(ROOT/'results/journal.sqlite3')
    try:
        emergency_stop(journal); journal.recover(); journal.plan(freeze['task_ids'],freeze.get('study_id',freeze['dataset_hash']))
        _run_pending(journal,keys,checkpoint=ROOT/'results/checkpoints/latest')
    finally: journal.export(ROOT/'results/checkpoints/latest'); journal.close()

def start():
    with ControllerLease(ROOT/'results/controller.lock'): return _start_locked()

if __name__=='__main__': start()
