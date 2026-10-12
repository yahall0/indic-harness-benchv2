"""Trusted read-only launch observation, outside the frozen evaluation runtime."""
import hashlib
import json
import sqlite3
import time
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from bench.durable import atomic_json, encode
from nextbench.monitor import snapshot

CAMPAIGN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TERMINAL = {'completed','agent_failed','timeout','budget_exhausted','integrity_failed','infrastructure_failed','interrupted','quota_paused'}


def brief(row):
    result = json.loads(row['result'] or '{}')
    return {k:row[k] for k in ('id','task','language','status','requests','input_actual','output_actual','input_bound','output_reserved')} | {
        'score': result.get('oracle', {}).get('outcome_score'),
        'integrity':result.get('integrity', []), 'error_type':result.get('error_type'),
        'pause_reason':result.get('pause_reason'), 'cleanup_incomplete':result.get('cleanup_incomplete',False),
        'elapsed_sec':result.get('elapsed_sec'), 'running_sec':round(time.time()-row['started'],1) if row['status']=='running' else None}


def observe():
    data = snapshot(CAMPAIGN)
    primary = data['primary'][:9]
    output = {'observed_utc':datetime.now(timezone.utc).isoformat(),'target_triplets':3,
              'all_primary_statuses':dict(Counter(r['status'] for r in data['primary'])),
              'first_nine':[brief(r) for r in primary],
              'first_nine_recoveries':[brief(data['recovery'][r['id']]) for r in primary if r['id'] in data['recovery']],
              'credential_slots':data['slots'], 'last_event_kind':data['last_event']['kind'] if data['last_event'] else None}
    with closing(sqlite3.connect((CAMPAIGN / 'results/journal.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory = sqlite3.Row; db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
        records = []
        for row in db.execute('SELECT c.run_id,c.id,c.status,c.response FROM calls c ORDER BY rowid'):
            value=json.loads(row['response'] or '{}')
            records.append({'run_id':row['run_id'],'call_id':row['id'],'call_status':row['status'],
                            **{k:value.get(k) for k in ('classification','status','latency_sec','tool_calls','schema_errors','retries','rotations')}})
        output['call_diagnostics']=records
        registry = [dict(r) for r in db.execute('SELECT * FROM recovery_attempts')]
        output['primary_physical_transmissions']=db.execute('SELECT count(*) FROM forwards').fetchone()[0]
        output['last_event_age_sec']=round(time.time()-db.execute('SELECT MAX(at) FROM events').fetchone()[0],1)
    retry_transmissions = 0
    for entry in registry:
        expected = 'recoveries/' + entry['primary_run_id'] + '/attempt-2'
        if entry['relative_root'] != expected: raise ValueError('Recovery evidence path mismatch')
        path=(CAMPAIGN/'results'/expected/'journal.sqlite3').resolve()
        if not path.is_relative_to(CAMPAIGN): raise ValueError('Recovery evidence escaped campaign')
        if not path.exists(): continue
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
            db.row_factory=sqlite3.Row; db.execute('PRAGMA query_only=ON')
            retry_transmissions+=db.execute('SELECT count(*) FROM forwards').fetchone()[0]
            for row in db.execute('SELECT run_id,id,status,response FROM calls ORDER BY rowid'):
                value=json.loads(row['response'] or '{}')
                output['call_diagnostics'].append({'run_id':row['run_id'],'call_id':row['id'],'call_status':row['status'],
                    'attempt_number':2, **{k:value.get(k) for k in ('classification','status','latency_sec','tool_calls','schema_errors','retries','rotations')}})
    output['recovery_physical_transmissions']=retry_transmissions
    output['all_attempt_physical_transmissions']=output['primary_physical_transmissions']+retry_transmissions
    with closing(sqlite3.connect((ROOT / 'results/journal.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        old = [dict(r) for r in db.execute('SELECT * FROM runs ORDER BY rowid')]
    evidence=json.loads((CAMPAIGN / 'preservation/verification.json').read_text())
    output['baseline_records_unchanged']=hashlib.sha256(encode(old).encode()).hexdigest()==evidence['baseline_primary_records_sha256']
    output['baseline_scores']=[{'task':r['task'],'language':r['language'],'status':r['status'],
                              'score':json.loads(r['result'] or '{}').get('oracle',{}).get('outcome_score')}
                             for r in old if r['task'] in {p['task'] for p in primary}]
    resolved=[]
    for row in primary:
        retry=data['recovery'].get(row['id'])
        scheduled=any(e['primary_run_id']==row['id'] for e in registry)
        resolved.append(row['status'] in TERMINAL and (not scheduled or bool(retry and retry['status'] in TERMINAL)))
    output['first_nine_resolved']=sum(resolved)
    output['first_three_triplets_resolved']=all(resolved)
    path=OUT / ('sample-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
    atomic_json(path,output); atomic_json(OUT / 'latest.json',output)
    print(json.dumps(output,ensure_ascii=False))
    return output


if __name__ == '__main__': observe()
