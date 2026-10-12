"""Fail-closed preparation and freeze gates. This command makes no inference calls."""
import hashlib,json
from pathlib import Path
from bench.durable import atomic_json
from bench.fingerprint import runtime_fingerprint
from bench.provenance import verify_reference
from bench.translations import check_translations
from bench.credentials import status
from bench.security import docker

ROOT=Path(__file__).resolve().parents[1]

def frozen_files():
    manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text())
    files=[ROOT/'dataset/task_manifest.json',ROOT/'dataset/pilot_plan.json',ROOT/'dataset/translation_reviews.json',ROOT/'config/protocol.json',ROOT/'config/images.json']
    files.extend(p for folder in ('bench','runtime','docker','validation') for p in (ROOT/folder).rglob('*') if p.is_file() and (p.suffix in ('.py','.json') or p.name=='Dockerfile'))
    for task in manifest:
        if task['pilot_candidate']:
            files.extend(p for p in (ROOT/'tasks'/task['task_id']/'prompts').rglob('*') if p.is_file())
            files.append(ROOT/'reports/oracles'/(task['task_id']+'.json'))
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}

def readiness(require_freeze=True):
    checks={}; details={}
    try: checks['references_unchanged']=verify_reference()['reference_unchanged']
    except Exception: checks['references_unchanged']=False
    manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text()); chosen=[t for t in manifest if t['pilot_candidate']]
    checks['forty_matched_candidates']=len(chosen)==40
    checks['oracle_positive_and_negative_validation']=True
    for t in chosen:
        p=ROOT/'reports/oracles'/(t['task_id']+'.json')
        r=json.loads(p.read_text()) if p.exists() else {}
        if not r.get('passed') or r.get('source_task_sha256')!=t['source_task_sha256']: checks['oracle_positive_and_negative_validation']=False
    translations=check_translations(); checks['translations_and_review']=translations['passed']
    fingerprint=runtime_fingerprint()
    for name in ('runtime_check','relay_check','helper_check','controller_check'):
        p=ROOT/'reports'/(name+'.json'); r=json.loads(p.read_text()) if p.exists() else {}
        checks[name]=r.get('passed') is True and r.get('runtime_fingerprint')==fingerprint
    base=json.loads((ROOT/'reports/security_check.json').read_text()); checks['base_resource_isolation']=base.get('passed') is True
    configured=status(); details['credential_slots']=configured['count']
    key_report=json.loads((ROOT/'reports/key_check.json').read_text()) if (ROOT/'reports/key_check.json').exists() else {}
    probes={r['slot']:r for r in key_report.get('key_checks',[])}
    checks['credentials_checked']=configured['count']>0 and all(probes.get(s,{}).get('classification')=='success' for s in configured['configured_slots'])
    store=ROOT/'config/credentials.dpapi.json'
    if store.exists(): checks['credentials_checked']=checks['credentials_checked'] and key_report.get('key_store_cipher_sha256')==hashlib.sha256(store.read_bytes()).hexdigest()
    try:
        images=json.loads((ROOT/'config/images.json').read_text())
        checks['frozen_images_available']=all(json.loads(docker(['image','inspect',v['id']],timeout=15))[0]['Id']==v['id'] for v in images.values())
    except Exception: checks['frozen_images_available']=False
    if require_freeze:
        f=ROOT/'dataset/freeze.json'
        if not f.exists(): checks['dataset_frozen']=False
        else:
            freeze=json.loads(f.read_text()); checks['dataset_frozen']=freeze['file_hashes']==frozen_files()
    result={'ready':all(checks.values()),'blocking_gates':[k for k,v in checks.items() if not v],'checks':checks,'details':details,
            'oracle_validated_tasks':sum(json.loads(p.read_text()).get('passed',False) for t in chosen for p in [ROOT/'reports/oracles'/(t['task_id']+'.json')] if p.exists()),
            'translation_complete':translations['passed'],'benchmark_runs':len(list((ROOT/'results/runs').glob('*/run.json'))),'model_calls_by_this_check':0}
    atomic_json(ROOT/'reports/readiness.json',result); return result

def freeze():
    gate=readiness(require_freeze=False)
    if not gate['ready']: raise ValueError('Freeze blocked: '+', '.join(gate['blocking_gates']))
    manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text()); chosen=[t for t in manifest if t['pilot_candidate']]
    for t in chosen: t['validation']['release_eligible']=True; t['status']='validated'
    atomic_json(ROOT/'dataset/task_manifest.json',manifest)
    plan=json.loads((ROOT/'dataset/pilot_plan.json').read_text()); plan['status']='frozen'; plan['not_yet_validated']=False
    atomic_json(ROOT/'dataset/pilot_plan.json',plan)
    hashes=frozen_files(); digest=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    previous_path=ROOT/'dataset/freeze.json'
    previous=json.loads(previous_path.read_text()) if previous_path.exists() else None
    started=bool(list((ROOT/'results/runs').glob('*/run.json')))
    study_id=digest; revision=1
    if previous:
        protected=['dataset/task_manifest.json','dataset/pilot_plan.json','dataset/translation_reviews.json','config/protocol.json']
        protected.extend(k for k in previous['file_hashes'] if k.startswith('tasks/'))
        same_study=previous['task_ids']==[t['task_id'] for t in chosen] and all(previous['file_hashes'].get(k)==hashes.get(k) for k in protected)
        if started and not same_study: raise ValueError('Cannot change tasks, prompts, settings or review after study start')
        if same_study: study_id=previous.get('study_id',previous['dataset_hash'])
        revision=previous.get('runtime_revision',1)+(digest!=previous['dataset_hash'])
    result={'dataset_hash':digest,'study_id':study_id,'runtime_revision':revision,
            'previous_freeze_hash':previous['dataset_hash'] if previous else None,
            'task_ids':[t['task_id'] for t in chosen],'file_hashes':hashes,'task_count':40,'planned_runs':120,'benchmark_started':started}
    atomic_json(ROOT/'dataset/freeze.json',result); return result
