"""Explicitly authorized, bounded additional INFRA recovery in the same campaign.

Never edits a primary/recovery outcome or replays a started attempt. Uses the
unchanged frozen Docker attempt implementation; exports a separate resolved view.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAMPAIGN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench.durable import Journal, atomic_json, encode
from bench.lease import ControllerLease
from bench.credentials import load_keys
from bench.metrics import AGENT_OUTCOMES
from nextbench.prepare import metadata
from nextbench.scope import validate_scope
from nextbench_repair.runner import ready, hashes, baseline_unchanged, validate_metadata
from nextbench_repair.attempt import attempt

BATCH = CAMPAIGN/'results/additional-recoveries/20261002'
TARGETS = [('c9b6eff7b07c35d6d96913e0','001-file','hi'),
           ('de130ba3ed5610056e7919b0','067-canary-release-check','en')]

def readonly(path):
    db = sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
    return db

def original_paths():
    return [ROOT/'results/journal.sqlite3', CAMPAIGN/'results/journal.sqlite3'] + sorted(
        (CAMPAIGN/'results/recoveries').glob('*/attempt-2/journal.sqlite3'))

def digest_database(path):
    with closing(readonly(path)) as db:
        digests = {}
        for raw in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            table = raw[0]
            if not table.replace('_','').isalnum(): raise ValueError('Unexpected table name')
            digest = hashlib.sha256()
            for row in db.execute('SELECT * FROM "'+table+'" ORDER BY rowid'):
                digest.update(encode(dict(row)).encode()); digest.update(b'\n')
            digests[table] = digest.hexdigest()
        return digests

def preserved():
    evidence = json.loads((BATCH/'preservation/before.json').read_text())
    return (all(digest_database(Path(p))==v for p,v in evidence['journals'].items()) and
        all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in evidence['files'].items()))

def capture():
    path = BATCH/'preservation/before.json'
    if path.exists():
        if not preserved(): raise ValueError('Prior records changed since authorization capture')
        return
    journals = {str(p):digest_database(p) for p in original_paths()}
    files = {}
    for folder in [ROOT/'results/runs',ROOT/'results/infrastructure-retries',CAMPAIGN/'results/runs',CAMPAIGN/'results/recoveries']:
        for p in folder.rglob('*'):
            if p.is_file() and not p.name.startswith('journal') and 'checkpoints' not in p.parts:
                files[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    pdf = ROOT/'pdf/Indic_Harness_Bench_Experiment_Report.pdf'
    files[str(pdf)] = hashlib.sha256(pdf.read_bytes()).hexdigest()
    for index,p in enumerate(original_paths()):
        destination = BATCH/'preservation'/('journal-'+str(index)+'.sqlite3')
        destination.parent.mkdir(parents=True,exist_ok=True)
        with closing(readonly(p)) as source, closing(sqlite3.connect(destination)) as backup:
            source.backup(backup)
    atomic_json(path,dict(journals=journals,files=files,captured_utc=datetime.now(timezone.utc).isoformat()))

def validate_originals():
    with closing(readonly(CAMPAIGN/'results/journal.sqlite3')) as primary:
        rows = [dict(r) for r in primary.execute('SELECT * FROM runs ORDER BY rowid')]
        if len(rows)!=138 or any(r['status'] in {'planned','running'} for r in rows):
            raise ValueError('Main campaign must be entirely terminal')
        for ident,task,language in TARGETS:
            row = next(r for r in rows if r['id']==ident)
            if (row['task'],row['language'],row['status'])!=(task,language,'infrastructure_failed'):
                raise ValueError('Only the named unresolved INFRA conditions are authorized')
            registry = dict(primary.execute('SELECT * FROM recovery_attempts WHERE primary_run_id=?',(ident,)).fetchone())
            expected = 'recoveries/'+ident+'/attempt-2'
            if registry['relative_root']!=expected: raise ValueError('Unsafe recovery registry')
            with closing(readonly(CAMPAIGN/'results'/expected/'journal.sqlite3')) as retry:
                failed = dict(retry.execute('SELECT * FROM runs').fetchone())
                if failed['id']!=registry['retry_run_id'] or failed['status']!='infrastructure_failed':
                    raise ValueError('A successful recovery must never be retried')
        # Legacy OSS accounting is preserved verbatim; admission checks apply to
        # this Nemotron campaign's request-owning journals only.
        for p in original_paths()[1:]:
            with closing(readonly(p)) as db:
                if db.execute("SELECT COUNT(*) FROM calls WHERE status!='settled'").fetchone()[0]:
                    raise ValueError('Existing accounting is not settled')
                if db.execute("SELECT COUNT(*) FROM resources WHERE status!='removed'").fetchone()[0]:
                    raise ValueError('Existing resources are not retired')

def identity(study, primary_id):
    return hashlib.sha256((study+':'+primary_id+':user-authorized-infra-recovery:3:20261002').encode()).hexdigest()[:24]

def admissible(row):
    if row['status']!='planned': raise ValueError('Started additional attempt must never be replayed')
    if (row['task'],row['language']) not in {(t,l) for _,t,l in TARGETS}:
        raise ValueError('Scored/non-target condition rejected')

def accounting(journal):
    totals = dict(attempts=0,physical_transmissions=0,known_input_tokens=0,known_output_tokens=0,
                  charged_input=0,charged_output=0,usage_missing_calls=0)
    paths = original_paths()[1:] + [journal.path]
    for p in paths:
        with closing(readonly(p)) as db:
            totals['physical_transmissions'] += db.execute('SELECT COUNT(*) FROM forwards').fetchone()[0]
            for r in db.execute('SELECT * FROM runs'):
                totals['attempts'] += r['status']!='planned'
                for k,field in [('known_input_tokens','input_actual'),('known_output_tokens','output_actual'),
                    ('charged_input','input_bound'),('charged_output','output_reserved'),('usage_missing_calls','usage_missing')]:
                    totals[k] += r[field]
    return totals

def synchronize_exhaustion(journal):
    # Read old slot ledgers; only the new journal is mutated.
    paths = original_paths()[1:] + [CAMPAIGN/'probes/compatibility/journal.sqlite3'] + list(
        (CAMPAIGN/'revisions/transport-v2/probes').glob('*/journal.sqlite3'))
    for p in paths:
        if not p.exists(): continue
        with closing(readonly(p)) as db:
            for r in db.execute("SELECT id,reason FROM slots WHERE state='exhausted'"):
                journal.exhaust_slot(r['id'],r['reason'] or 'confirmed_quota_exhaustion',None)

def export(journal, phase):
    journal.export(BATCH/'checkpoints/latest')
    with closing(readonly(CAMPAIGN/'results/journal.sqlite3')) as db:
        primary = [dict(r) for r in db.execute('SELECT * FROM runs ORDER BY rowid')]
        registry = [dict(r) for r in db.execute('SELECT * FROM recovery_attempts')]
    chosen = {r['id']:{**r,'attempt_number':1,'primary_run_id':r['id']} for r in primary}
    for entry in registry:
        with closing(readonly(CAMPAIGN/'results'/entry['relative_root']/'journal.sqlite3')) as db:
            r = dict(db.execute('SELECT * FROM runs').fetchone())
            if r['status'] in AGENT_OUTCOMES:
                chosen[entry['primary_run_id']]={**r,'attempt_number':2,'primary_run_id':entry['primary_run_id']}
    extra = {r['id']:r for r in journal.runs()}
    study = json.loads((CAMPAIGN/'config/freeze.json').read_text())['study_id']
    for parent,_,_ in TARGETS:
        r = extra.get(identity(study,parent))
        if r and r['status'] in AGENT_OUTCOMES:
            chosen[parent]={**r,'attempt_number':3,'primary_run_id':parent}
    totals = accounting(journal)
    atomic_json(CAMPAIGN/'results/exports/user_requested_resolved_outcomes.json',list(chosen.values()))
    atomic_json(CAMPAIGN/'results/exports/accounting_including_additional_recoveries.json',totals)
    summary = []
    for parent,task,lang in TARGETS:
        r = extra.get(identity(study,parent))
        v = json.loads(r['result'] or '{}') if r else {}
        summary.append(dict(primary_run_id=parent,task=task,language=lang,attempt_number=3,
            run_id=r['id'] if r else None,status=r['status'] if r else 'planned',
            score=v.get('oracle',{}).get('outcome_score') if r and r['status'] in AGENT_OUTCOMES else None,
            requests=r['requests'] if r else 0,usage_missing=r['usage_missing'] if r else 0,
            pause_reason=v.get('pause_reason'),cleanup_incomplete=v.get('cleanup_incomplete',False),integrity=v.get('integrity',[])))
    atomic_json(BATCH/'status.json',dict(phase=phase,updated_utc=datetime.now(timezone.utc).isoformat(),
        campaign_study_id=study,attempts=summary,combined_accounting=totals,
        analysis_policy='User requested an additional INFRA-only recovery after the original one-recovery policy. Latest scored recovery replaces the condition without selecting the better score. Primary-only and original recovery-inclusive exports remain preserved.'))
    return summary

def start(authorized):
    if not authorized: raise ValueError('Explicit new user authorization required')
    with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(CAMPAIGN/'results/controller.lock'):
        validate_originals()
        if (CAMPAIGN/'results/STOP_REQUESTED').exists(): raise ValueError('Operator hold remains in place')
        if not ready(CAMPAIGN)['ready']: raise ValueError('Frozen runtime readiness failed')
        info=json.loads((CAMPAIGN/'revisions/transport-v2/config/freeze.json').read_text())
        study=json.loads((CAMPAIGN/'config/freeze.json').read_text())['study_id']
        profile=json.loads((CAMPAIGN/'config/model_profile.json').read_text())
        limits=json.loads((CAMPAIGN/'config/protocol.json').read_text())
        scope=json.loads((CAMPAIGN/'config/report_scope.json').read_text())
        images=json.loads((CAMPAIGN/'revisions/transport-v2/config/images.json').read_text())
        live=metadata();validate_metadata(live,profile)
        atomic_json(BATCH/'metadata-on-admission.json',live)
        capture()
        source_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        authorization=dict(created_utc=datetime.now(timezone.utc).isoformat(),study_id=study,
            user_instructions=['the main run was done, a few had infra errors, retry only those and follow along and try to make them succeed',
                               'save them as part of the same try for the sake of consistency'],
            targets=TARGETS,attempt_number=3,max_additional_attempts=2,automatic_further_retries=False,
            same_model_prompts_oracles_budgets_images=True,runtime_freeze_hash=info['runtime_freeze_hash'],controller_sha256=source_sha)
        auth_path=BATCH/'authorization.json'
        if not auth_path.exists(): atomic_json(auth_path,authorization)
        else:
            old=json.loads(auth_path.read_text())
            if old['targets']!=[list(x) for x in TARGETS] or old['controller_sha256']!=source_sha:
                raise ValueError('Additional recovery authorization changed')
        keys=load_keys()  # Credentials stay in memory, forwarded only to the trusted relay via stdin.
        with closing(Journal(BATCH/'journal.sqlite3')) as journal:
            journal.slot_init(list(keys))
            for parent,task,lang in TARGETS:
                rid=identity(study,parent)
                journal.db.execute('INSERT OR IGNORE INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',(rid,task,lang,study))
            expected=[(identity(study,p),t,l,study) for p,t,l in TARGETS]
            if [tuple(r[k] for k in ('id','task','language','dataset_hash')) for r in journal.runs()]!=expected:
                raise ValueError('Additional attempt journal identity conflict')
            if journal.resources() or any(r['status']=='running' for r in journal.runs()):
                raise ValueError('Started interrupted attempt requires inspection; no replay')
            atomic_json(BATCH/'controller_process.json',dict(pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat(),
                module='additional_recovery',study_id=study,runtime_freeze_hash=info['runtime_freeze_hash']))
            atomic_json(CAMPAIGN/'results/additional_recovery_registry.json',dict(batch='additional-recoveries/20261002',
                journal='additional-recoveries/20261002/journal.sqlite3',targets=authorization['targets'],attempt_number=3,study_id=study))
            preferred=None
            export(journal,'READY')
            try:
                for index,row in enumerate(journal.runs()):
                    if row['status']!='planned': continue
                    admissible(row)
                    if (CAMPAIGN/'results/STOP_REQUESTED').exists() or (BATCH/'STOP_REQUESTED').exists():
                        raise ValueError('Admission hold requested')
                    if hashes(CAMPAIGN)!=info['file_hashes'] or not baseline_unchanged(ROOT) or not preserved():
                        raise ValueError('Existing results or frozen runtime changed')
                    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=source_sha:
                        raise ValueError('Additional controller changed')
                    validate_scope(ROOT,scope);synchronize_exhaustion(journal)
                    totals=accounting(journal)
                    if (totals['charged_input']+limits['max_input_tokens']>limits['max_campaign_input_allowance'] or
                        totals['charged_output']+limits['max_output_tokens']>limits['max_campaign_output_allowance'] or
                        totals['physical_transmissions']+limits['max_requests']>limits['max_campaign_physical_transmissions'] or
                        totals['attempts']+1>limits['maximum_total_attempts']):
                        raise ValueError('Aggregate campaign allowance exhausted')
                    if index: time.sleep(30)
                    journal.event(row['id'],'explicit_additional_infrastructure_recovery',authorization)
                    export(journal,'RUNNING')
                    status,preferred=attempt(journal,row,keys,preferred,baseline_root=ROOT,campaign_root=CAMPAIGN,
                        profile=profile,limits=limits,images=images,runtime_freeze_hash=info['runtime_freeze_hash'],
                        destination_root=BATCH/'runs',checkpoint=BATCH/'checkpoints/latest')
                    results=export(journal,'RUNNING')
                    print(json.dumps({'task':row['task'],'language':row['language'],'status':status,'attempt_number':3}),flush=True)
                    val=json.loads(journal.get(row['id'])['result'] or '{}')
                    if (val.get('cleanup_incomplete') or val.get('integrity') or val.get('error_type') or status=='quota_paused'):
                        raise ValueError('Safety/accounting/quota gate requires inspection')
                report=export(journal,'FINISHED')
                if not preserved(): raise ValueError('Post-run preservation check failed')
                atomic_json(BATCH/'preservation/after.json',dict(passed=True,all_original_journal_tables_and_artifacts_unchanged=True))
                return report
            except BaseException as error:
                export(journal,'PAUSED')
                atomic_json(BATCH/'pause.json',dict(error_type=type(error).__name__,message=str(error),time_utc=datetime.now(timezone.utc).isoformat()))
                raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--launch-authorized',action='store_true');args=parser.parse_args()
    print(json.dumps(start(args.launch_authorized)),flush=True)
