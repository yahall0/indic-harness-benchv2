"""Resume only unstarted work under an append-only, verified runtime revision."""
import argparse
import hashlib
import json
import os
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

from bench.credentials import load_keys
from bench.durable import Journal,atomic_json,encode
from bench.lease import ControllerLease
from bench.security import docker
from nextbench.runner import ROOT,campaign_path,current_hashes as base_hashes,cleanup
from nextbench.scope import validate_scope
from nextbench.prepare import metadata
from nextbench.recovery import run_pending,_sync_slots
from nextbench.analysis import export
from nextbench_repair.attempt import attempt
from nextbench_repair.verify import sources


def baseline_unchanged(root):
    frozen=json.loads((root/'dataset/freeze.json').read_text())
    return all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
               for name,digest in frozen['file_hashes'].items())


def validate_metadata(live,profile):
    tag=next((m for m in live['tags'] if m['name']==profile['model']),{})
    show=live['show'].get(profile['model'],{})
    contexts=[v for k,v in show.get('model_info',{}).items() if k.endswith('.context_length')]
    if (tag.get('digest')!=profile['provider_advertised_digest'] or
        show.get('thinking')!={'values':[False,True],'default':True} or
        not {'completion','tools','thinking'}<=set(show.get('capabilities') or []) or
        contexts!=[profile['provider_context_window']]):
        raise ValueError('Cloud capability metadata changed; keep held')


def clear_repair_hold(campaign,revision):
    stop=campaign/'results/STOP_REQUESTED'
    hold=json.loads(stop.read_text()) if stop.exists() else None
    if hold is not None:
        if hold.get('admission_hold') is not True or hold.get('created_by')!='trusted monitoring controller in this chat':
            raise ValueError('Operator stop is not this repair hold; never silently clear it')
        atomic_json(revision/'checks/hold-cleared-on-authorized-resume.json',hold)
        stop.unlink()


def hashes(campaign):
    revision=campaign/'revisions/transport-v2'
    value={'base/'+k:v for k,v in base_hashes(campaign).items()}
    value.update({'repair/'+k:v for k,v in sources().items()})
    for p in sorted((revision/'config').glob('*.json')):
        if p.name!='freeze.json': value['revision/config/'+p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ('checks/fake-verification.json','probes/hindi-hinglish/report.json','probes/hindi-hinglish/checkpoint/journal-backup.sqlite3'):
        value['revision/'+name]=hashlib.sha256((revision/name).read_bytes()).hexdigest()
    return value


def ready(campaign,require_freeze=True):
    campaign=campaign_path(campaign);revision=campaign/'revisions/transport-v2'
    original=json.loads((campaign/'config/freeze.json').read_text())
    fake=json.loads((revision/'checks/fake-verification.json').read_text())
    probe=json.loads((revision/'probes/hindi-hinglish/report.json').read_text())
    images=json.loads((revision/'config/images.json').read_text())
    checks={'original_runtime_config_evidence_preserved':base_hashes(campaign)==original['file_hashes'],
            'repair_fake_checks':fake.get('passed') is True,'repair_fake_sources_current':fake.get('repair_sources')==sources(),
            'hindi_hinglish_canary':probe.get('passed') is True,'canary_sources_current':probe.get('repair_sources')==sources(),
            'canary_images_current':probe.get('images')==images,
            'canary_capped':probe.get('physical_transmissions',999)<=6 and probe.get('charged_input',999999)<=200000 and probe.get('charged_output',999999)<=16384,
            'fake_images_current':fake.get('images')==images,
            'relay_source_matches_image_build':images['relay']['source_sha256']=={
                'relay.py':hashlib.sha256((ROOT/'nextbench_repair/runtime/relay.py').read_bytes()).hexdigest(),
                'upstream.py':hashlib.sha256((ROOT/'nextbench_repair/upstream.py').read_bytes()).hexdigest()},
            'image_pins_available':all(json.loads(docker(['image','inspect',v['id']]))[0]['Id']==v['id'] for v in images.values()),
            'baseline_frozen_files_unchanged':baseline_unchanged(ROOT),
            'same_agent_helper_grader_images':all(images[k]==json.loads((campaign/'config/images.json').read_text())[k] for k in ('agent','helper','grader')),
            'source_scope_preserved':bool(validate_scope(ROOT,json.loads((campaign/'config/report_scope.json').read_text())))}
    if require_freeze:
        freeze=json.loads((revision/'config/freeze.json').read_text());current=hashes(campaign)
        checks['repair_frozen']=(freeze['file_hashes']==current and freeze['runtime_freeze_hash']==hashlib.sha256(encode(current).encode()).hexdigest())
    result={'ready':all(checks.values()),'checks':checks,'blocked':[k for k,v in checks.items() if not v]}
    atomic_json(revision/'checks/readiness.json',result);return result


def freeze(campaign):
    campaign=campaign_path(campaign);revision=campaign/'revisions/transport-v2'
    with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(campaign/'results/controller.lock'):
        if not ready(campaign,False)['ready']: raise ValueError('Repair readiness failed')
        values=hashes(campaign);digest=hashlib.sha256(encode(values).encode()).hexdigest();path=revision/'config/freeze.json'
        if path.exists():
            if json.loads(path.read_text())['file_hashes']!=values: raise ValueError('Never overwrite a different runtime revision freeze')
        else:
            atomic_json(path,{'runtime_freeze_hash':digest,'file_hashes':values,'created_utc':datetime.now(timezone.utc).isoformat(),
                'original_study_id':json.loads((campaign/'config/freeze.json').read_text())['study_id'],
                'revision':'transport-v2','record_transport_change_in_analysis':True,
                'original_terminal_attempts_preserved':True,'new_score_seeking_attempts':False})
    return ready(campaign)


def start(campaign,authorized=False):
    if not authorized: raise ValueError('Repair/resume authorization required')
    campaign=campaign_path(campaign);revision=campaign/'revisions/transport-v2'
    if not ready(campaign)['ready']: raise ValueError('Repair gates failed; leave benchmark held')
    info=json.loads((revision/'config/freeze.json').read_text());original=json.loads((campaign/'config/freeze.json').read_text())
    scope=json.loads((campaign/'config/report_scope.json').read_text());profile=json.loads((campaign/'config/model_profile.json').read_text())
    live=metadata()
    validate_metadata(live,profile)
    atomic_json(revision/'checks/metadata-on-resume.json',live)
    limits=json.loads((campaign/'config/protocol.json').read_text());images=json.loads((revision/'config/images.json').read_text())
    keys=load_keys();manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text())
    def admitted():
        clear_repair_hold(campaign,revision)
        atomic_json(campaign/'results/controller_process.json',{'pid':os.getpid(),'module':'nextbench_repair.runner',
            'study_id':original['study_id'],'runtime_freeze_hash':info['runtime_freeze_hash'],'started_utc':datetime.now(timezone.utc).isoformat()})
        with closing(Journal(campaign/'results/journal.sqlite3')) as primary:
            primary.event(None,'runtime_revision_activated',{'revision':'transport-v2','runtime_freeze_hash':info['runtime_freeze_hash'],
                'previous_runtime_freeze_hash':original['runtime_freeze_hash'],'original_terminal_records_unchanged':True,
                'upstream_streaming':True,'socket_timeout_sec':180,'whole_attempt_budgets_unchanged':True})
    def execute(journal,row,preferred,*,destination_root,checkpoint):
        if (campaign/'results/STOP_REQUESTED').exists(): raise RuntimeError('Operator stop requested')
        if hashes(campaign)!=info['file_hashes']: raise ValueError('Repair freeze changed')
        validate_scope(ROOT,scope)
        if not baseline_unchanged(ROOT): raise ValueError('Frozen baseline/shared implementation changed')
        with closing(Journal(revision/'probes/hindi-hinglish/journal.sqlite3')) as probe: _sync_slots(journal,probe)
        status,slot=attempt(journal,row,keys,preferred,baseline_root=ROOT,campaign_root=campaign,profile=profile,limits=limits,images=images,
            runtime_freeze_hash=info['runtime_freeze_hash'],destination_root=destination_root,checkpoint=checkpoint)
        print(json.dumps({'task':row['task'],'language':row['language'],'status':status,'revision':'transport-v2'}),flush=True)
        return slot
    return run_pending(ROOT,campaign,scope,original['study_id'],execute,cleanup,on_acquired=admitted,
        exporter=lambda journal:export(journal,campaign,manifest))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('ready','freeze','start'));parser.add_argument('campaign',type=Path)
    parser.add_argument('--launch-authorized',action='store_true');args=parser.parse_args()
    value=start(args.campaign,args.launch_authorized) if args.command=='start' else freeze(args.campaign) if args.command=='freeze' else ready(args.campaign)
    print(json.dumps(value),flush=True)
