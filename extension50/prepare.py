"""Prepare immutable additions; builds and validation execute in hardened Docker."""
import copy, json, re, shutil, urllib.request
from datetime import datetime,timezone
from bench.durable import Journal, atomic_json, encode
from bench.lease import ControllerLease
from bench.security import docker
from nextbench.containers import CampaignContainers
from extension50.common import *
from extension50.translations import TEXT

def materialize():
    if (SHARED/'config/selection.json').exists(): return
    if not capture(): raise ValueError('Preservation failed')
    manifest=read(ROOT/'dataset/task_manifest.json'); old=set(read(ROOT/'dataset/pilot_plan.json')['execution_task_ids'])
    selected=[];reviews=[]
    for tid in TASKS:
        if tid in old: raise ValueError('Must be entirely new task')
        t=copy.deepcopy(next(t for t in manifest if t['task_id']==tid))
        if len(t['source_prompt_files'])!=1 or t['infrastructure_flags'] or t['subprocess_sites']: raise ValueError('Offline single-round audit failed')
        selected.append(t)
        for lang in ['en','hi','hinglish']:
            p=SHARED/'input/tasks'/tid/'prompts'/lang/t['source_prompt_files'][0];p.parent.mkdir(parents=True,exist_ok=True)
            original=(ROOT/'vendor/harnessbench/tasks'/tid/t['source_prompt_files'][0]).read_text(encoding='utf-8')
            value=original if lang=='en' else TEXT[tid][lang]
            p.write_text(value.rstrip()+CONTRACT,encoding='utf-8',newline='\n')
            # Match every workspace path and every protected quoted literal.
            paths=re.findall(r'\$WORKSPACE/[^\s]+',original)
            literals=re.findall(r'`([^`]+)`',original)
            missing=[s for s in paths+literals if s not in value]
            if missing: raise ValueError(str((tid,lang,missing)))
            reviews.append({'task':tid,'language':lang,'sha256':sha(p),'paths_and_quoted_literals_preserved':True,'requirements_self_reviewed':True,'independent_human_review':False})
    atomic_json(SHARED/'input/dataset/task_manifest.json',selected)
    atomic_json(SHARED/'config/translation_review.json',reviews)
    ids={'oss':read(ROOT/'dataset/freeze.json').get('study_id','be79c2f6c171dbe17a7c517df8fba4996844029a2be4cfd92b47db77ef0ee036'),'nemotron':read(NEM/'config/freeze.json')['study_id']}
    atomic_json(SHARED/'config/selection.json',{'selected_before_new_outcomes_utc':datetime.now(timezone.utc).isoformat(),'task_ids':TASKS,'parent_study_ids':ids,'original_matched_task_ids':read(ROOT/'campaigns/shared/report_matched_scope.json')['task_ids'],'selection_reason':'Four unused offline single-round tasks from underrepresented data, professional and approval-planning families; no task selected on either new model outcome. Original 46 are retained.','logical_task_count':50,'primary_attempt_count':24,'rerun_original_conditions':False,'translation_authorization':'User explicitly authorized current assistant translation rather than Luna.','selection_after_prior_model_results':True,'maximum_fresh_recoveries_per_condition':2,'retry_only_terminal_infrastructure_failure':True,'select_best_score':False,'preserve_all_attempts':True})
    nemprofile=read(NEM/'config/model_profile.json');nemprofile['agent_thinking']='high'
    profiles={'nemotron':nemprofile,'oss':{'model':'gpt-oss:20b','thinking':True,'provider_reasoning_effort':'medium','agent_thinking':'medium','context_window':65536,'provider_context_window':131072,'response_model_aliases':['gpt-oss:20b'],'thinking_control_semantics':'Same medium effort as the original GPT-OSS-20B campaign.'}}
    atomic_json(SHARED/'config/profiles.json',profiles)
    limits=read(ROOT/'config/protocol.json')
    for k in ['pilot_status','planned_runs','target_tasks','target_task_language_versions','reasoning_effort']: limits.pop(k,None)
    atomic_json(SHARED/'config/limits.json',limits)

def runtime():
    folder=ROOT/'extension50'
    contract=(ROOT/'nextbench/contract.py').read_text()
    a=contract.index('def validate_profile(');b=contract.index('\n\ndef request_payload',a)
    validation='''def validate_profile(profile):
    if not isinstance(profile,dict) or profile.get('model') not in ('gpt-oss:20b','nemotron-3-super'):
        raise ValueError('Only the two frozen models; no fallback')
    expected='medium' if profile['model']=='gpt-oss:20b' else 'high'
    if profile.get('thinking') is not True or profile.get('provider_reasoning_effort')!=expected or profile.get('agent_thinking')!=expected:
        raise ValueError('Original model-specific reasoning settings required')
    if profile.get('context_window')!=65536 or profile.get('provider_context_window',0)<65536:
        raise ValueError('Fixed supported context required')
    if profile.get('response_model_aliases')!=[profile['model']]: raise ValueError('Pinned identity required')
    return profile
'''
    (folder/'contract.py').write_text(contract[:a]+validation+contract[b:],encoding='utf-8',newline='\n')
    config=(ROOT/'nextbench/openclaw_config.py').read_text().replace('from nextbench.contract','from extension50.contract').replace("thinking = 'high' if profile['thinking'] else 'off'","thinking = profile['agent_thinking']").replace("'api': 'openai-completions', 'models':", "'api': 'openai-completions', 'timeoutSeconds': limits['attempt_timeout_sec'], 'models':")
    (folder/'openclaw_config.py').write_text(config,encoding='utf-8',newline='\n')
    agent=(ROOT/'nextbench/runtime/agent.py').read_text().replace("('off','high')","('medium','high')").replace('Frozen boolean thinking control required','Original model-specific thinking control required')
    (folder/'agent.py').write_text(agent,encoding='utf-8',newline='\n')
    attempt=(ROOT/'nextbench_repair/attempt.py').read_text().replace('from nextbench_repair.openclaw_config','from extension50.openclaw_config').replace("'high' if profile['thinking'] else 'off'","profile['agent_thinking']")
    (folder/'attempt.py').write_text(attempt,encoding='utf-8',newline='\n')
    compatibility=(ROOT/'nextbench_repair/compatibility.py').read_text().replace('from nextbench_repair.openclaw_config','from extension50.openclaw_config')
    compatibility=compatibility.replace("p['model']=='nemotron-3-super' and p['reasoning_effort']=='high'", "p['model'] in ('nemotron-3-super','gpt-oss:20b') and p['reasoning_effort']==('medium' if p['model']=='gpt-oss:20b' else 'high')")
    compatibility=compatibility.replace(", ('hi', 1, True)", "").replace("'thinking': 'high'", "'thinking': profile['agent_thinking']")
    compatibility=compatibility.replace("t['request']['reasoning_effort'] == 'high'", "t['request']['reasoning_effort'] == profile['provider_reasoning_effort']")
    (folder/'compatibility.py').write_text(compatibility,encoding='utf-8',newline='\n')

def build_validate():
    images=read(NEM/'revisions/transport-v2/config/images.json')
    for role,names in [('agent',{'agent.py':ROOT/'extension50/agent.py'}),('relay',{'contract.py':ROOT/'extension50/contract.py'}),('grader',{})]:
        context=SHARED/'private-build'/role;context.mkdir(parents=True,exist_ok=True)
        instructions=[]
        for name,p in names.items(): shutil.copyfile(p,context/name);instructions.append('COPY '+name+' /opt/ihb/'+name)
        if role=='grader':
            for tid in TASKS:
                shutil.copytree(ROOT/'vendor/harnessbench/tasks'/tid,context/'tasks'/tid,dirs_exist_ok=True)
            # Match the original baseline builder's canonical Unix fixture bytes.
            # Never edit the preserved Windows source or modify an oracle/hash.
            normalizations=[]
            for tid in TASKS:
                for p in (context/'tasks'/tid/'fixtures').rglob('*'):
                    if not p.is_file(): continue
                    raw=p.read_bytes()
                    try: raw.decode('utf-8')
                    except UnicodeDecodeError: continue
                    if b'\x00' in raw: continue
                    canonical=raw.replace(b'\r\n',b'\n')
                    if canonical!=raw:
                        p.write_bytes(canonical);normalizations.append({'path':p.relative_to(context).as_posix(),'source_sha256':__import__('hashlib').sha256(raw).hexdigest(),'canonical_sha256':sha(p)})
            atomic_json(SHARED/'config/canonical_source_copy.json',{'same_normalization_as_baseline_builder':True,'preserved_vendor_untouched':True,'line_endings_only':normalizations})
            shutil.copyfile(ROOT/'validation/solutions.py',context/'old_solutions.py')
            shutil.copyfile(ROOT/'extension50/private_solutions.py',context/'solutions.py')
            instructions+=['COPY tasks/ /opt/ihb/tasks/','COPY old_solutions.py solutions.py /opt/ihb/validation/']
        pin=images[role]['id']; base_tag=images[role]['tag']; tag='ihb-'+role+':extension50-20261002'
        if json.loads(docker(['image','inspect',base_tag]))[0]['Id']!=pin: raise ValueError('Local base tag moved')
        (context/'Dockerfile').write_text('FROM '+base_tag+'\n'+'\n'.join(instructions)+'\nUSER 10001:10001\n')
        docker(['build','--network=none','--pull=false','-t',tag,str(context)],timeout=600)
        info=json.loads(docker(['image','inspect',tag]))[0];base=json.loads(docker(['image','inspect',pin]))[0]
        if info['Config']['User']!='10001:10001' or info['RootFS']['Layers'][:len(base['RootFS']['Layers'])]!=base['RootFS']['Layers']: raise ValueError('Image inheritance failed')
        images[role]={'id':info['Id'],'base_id':pin,'tag':tag}
    atomic_json(SHARED/'config/images.json',images)
    j=Journal(SHARED/'checks/oracles/journal.sqlite3'); reports=[]
    try:
        for tid in TASKS:
            box=CampaignContainers(j,'validation-'+tid,images)
            try:
                c=box.create('grader');r=box.invoke(c,{'action':'validate','task':tid},timeout=240)
                atomic_json(SHARED/'checks/oracles'/ (tid+'.json'),r);reports.append(r)
                print(json.dumps({'task':tid,'validation_passed':r['passed'],'positive':r['positive']['outcome_score']}),flush=True)
            finally: box.cleanup()
        atomic_json(SHARED/'checks/oracle_validation.json',{'passed':all(r['passed'] for r in reports),'task_count':len(reports),'actual_cloud_transmissions':0,'all_owned_resources_removed':not j.resources(),'reports':[r['task'] for r in reports]})
    finally: j.close()
    if not all(r['passed'] for r in reports): raise ValueError('Oracle validation failed; no benchmark admission')

if __name__=='__main__':
    with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(NEM/'results/controller.lock'):
        materialize();runtime();build_validate()
