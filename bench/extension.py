"""Append-only dataset extension checks. Static trusted-controller code only."""
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from bench.durable import atomic_json

ROOT=Path(__file__).resolve().parents[1]
COUNT_METADATA={'target_tasks','target_task_language_versions','planned_runs','pilot_status'}


def read(root,relative):
    return json.loads((root/relative).read_text(encoding='utf-8'))


def ordered_tasks(manifest,plan):
    selected=[t['task_id'] for t in manifest if t['pilot_candidate']]
    order=plan.get('execution_task_ids',selected)
    if len(order)!=len(set(order)) or set(order)!=set(selected):
        raise ValueError('Execution order must contain every selected task exactly once')
    return order


def check_extension(root=ROOT):
    root=Path(root); baseline=root/'provenance/initial-40'
    previous=read(baseline,'dataset/freeze.json')
    manifest=read(root,'dataset/task_manifest.json');plan=read(root,'dataset/pilot_plan.json')
    order=ordered_tasks(manifest,plan);old_ids=previous['task_ids']
    selection=read(root,'dataset/extension_selection.json')
    if order!=old_ids+selection['selected_task_ids'] or selection['original_task_ids']!=old_ids:
        raise ValueError('Extension must append the locked additions after the original execution order')
    if len(order)!=54 or len(selection['selected_task_ids'])!=14:
        raise ValueError('Authorized scope is 40 original tasks plus 14 additions')
    current={t['task_id']:t for t in manifest};old={t['task_id']:t for t in read(baseline,'dataset/task_manifest.json')}
    if any(current.get(t)!=old[t] for t in old_ids):
        raise ValueError('An original task manifest entry changed')
    reviews=read(root,'dataset/translation_reviews.json');old_reviews=read(baseline,'dataset/translation_reviews.json')
    if any(reviews.get(t)!=old_reviews.get(t) for t in old_ids):
        raise ValueError('An original translation review changed')
    for name,digest in previous['file_hashes'].items():
        if name.startswith('tasks/') or name.startswith('reports/oracles/'):
            p=root/name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
                raise ValueError('Original prompt or oracle validation changed: '+name)
    protocol=read(root,'config/protocol.json');old_protocol=read(baseline,'config/protocol.json')
    if {k:v for k,v in protocol.items() if k not in COUNT_METADATA}!={k:v for k,v in old_protocol.items() if k not in COUNT_METADATA}:
        raise ValueError('Model, inference settings, budgets or isolation protocol changed')
    if protocol['target_tasks']!=54 or protocol['target_task_language_versions']!=162 or protocol['planned_runs']!=162 or plan['planned_runs']!=162:
        raise ValueError('Expanded protocol counts must match the 54-task design')
    images=read(root,'config/images.json');old_images=read(baseline,'config/images.json')
    if any(images.get(k)!=old_images[k] for k in ('agent','relay','helper')):
        raise ValueError('Agent, relay or helper image changed; identical protocol required')
    old_rows=read(baseline,'runs.json')
    with closing(sqlite3.connect((root/'results/journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        rows={r['id']:dict(r) for r in db.execute('SELECT * FROM runs')}
    if any(rows.get(r['id'])!=r for r in old_rows):
        raise ValueError('Original attempt records changed')
    if any(r['status'] in ('planned','running') for r in old_rows):
        raise ValueError('Original campaign must be stopped and settled before extending')
    backup=baseline/'journal-backup.sqlite3'
    if backup.exists():
        run_ids=[r['id'] for r in old_rows];placeholders=','.join('?' for _ in run_ids)
        queries=[f'SELECT * FROM calls WHERE run_id IN ({placeholders}) ORDER BY id',
            f'SELECT f.* FROM forwards f JOIN calls c ON c.id=f.call_id WHERE c.run_id IN ({placeholders}) ORDER BY f.call_id,f.ordinal']
        with closing(sqlite3.connect((root/'results/journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)) as current_db,closing(sqlite3.connect(backup.resolve().as_uri()+'?mode=ro',uri=True)) as old_db:
            for query in queries:
                if current_db.execute(query,run_ids).fetchall()!=old_db.execute(query,run_ids).fetchall():
                    raise ValueError('Original inference accounting or transmission records changed')
    for run_id,item in read(baseline,'terminal_hashes.json').items():
        p=root/'results/runs'/run_id/'run.json'
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['run_json_sha256']:
            raise ValueError('Original saved run artifact changed: '+run_id)
    return {'passed':True,'original_tasks_unchanged':len(old_ids),'original_attempts_unchanged':len(old_rows),
        'additional_tasks':len(order)-len(old_ids),'combined_tasks':len(order),'combined_planned_runs':162,
        'study_id':previous.get('study_id',previous['dataset_hash']),
        'original_runtime_freeze_hash':previous['dataset_hash'],'same_inference_and_scoring_protocol':True,
        'new_model_calls':0}


if __name__=='__main__':
    result=check_extension();atomic_json(ROOT/'reports/extension_preservation.json',result)
    print(json.dumps(result,indent=2))
