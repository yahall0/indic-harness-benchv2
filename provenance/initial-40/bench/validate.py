import json
import hashlib
from pathlib import Path
from datetime import datetime,timezone
from bench.containers import Containers
from bench.durable import atomic_json

ROOT=Path(__file__).resolve().parents[1]

def validate(only=None):
    manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text())
    for task in manifest:
        if not task['pilot_candidate'] or (only and task['task_id'] not in only): continue
        box=Containers(); tid=task['task_id']
        try:
            c=box.create('grader')
            result=box.invoke(c,{'action':'validate','task':tid},timeout=240)
            result['grader_image']=box.images['grader']['id']
            result['timestamp_utc']=datetime.now(timezone.utc).isoformat()
            result['source_task_sha256']=task['source_task_sha256']
            result['validation_code_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'validation').glob('*.py')}
        except Exception as e:
            result={'task':tid,'passed':False,'error_type':type(e).__name__,'error':str(e)}
        finally: box.cleanup()
        atomic_json(ROOT/'reports/oracles'/(tid+'.json'),result)
        task['validation'].update(positive_workspace='passed' if result['passed'] else 'failed',
             negative_cases='passed' if result['passed'] else 'failed',hooks='passed' if result['passed'] else 'failed',release_eligible=False)
        print(json.dumps({'task':tid,'passed':result['passed'],
            'positive_score':result.get('positive',{}).get('outcome_score'),
            'failed_positive_checks':[c.get('id') for c in result.get('positive',{}).get('checks',[]) if not c.get('pass')],
            'error':result.get('error')}),flush=True)
    atomic_json(ROOT/'dataset/task_manifest.json',manifest)
    reports=[]
    for task in manifest:
        if not task['pilot_candidate']: continue
        p=ROOT/'reports/oracles'/(task['task_id']+'.json')
        if p.exists(): reports.append(json.loads(p.read_text()))
    summary={'candidate_tasks':40,'tested':len(reports),'passed':sum(r['passed'] for r in reports),
             'failed_tasks':[r['task'] for r in reports if not r['passed']],
             'benchmark_runs':0,'oracle_code_modified':False,'reports':'reports/oracles/'}
    atomic_json(ROOT/'reports/oracle_validation.json',summary)
    return summary

if __name__=='__main__':
    import sys
    validate(set(sys.argv[1:]) or None)
