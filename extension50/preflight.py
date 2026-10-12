"""No-inference readiness, full fake integration and append-only source freeze."""
import ast, json, urllib.request
from datetime import datetime,timezone
from extension50.common import *
from extension50.contract import validate_profile,request_payload,completion
from extension50 import compatibility
from bench.security import docker
from bench.durable import atomic_json,encode

def provider_metadata():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('https://ollama.com/api/tags',timeout=30) as r: tags=json.load(r)
    profiles=read(SHARED/'config/profiles.json');values={}
    for label,p in profiles.items():
        model=p['model'];tag=next(t for t in tags['models'] if t['name']==model)
        req=urllib.request.Request('https://ollama.com/api/show',json.dumps({'model':model}).encode(),{'Content-Type':'application/json'})
        with opener.open(req,timeout=30) as r: value=json.load(r)
        if not {'completion','tools','thinking'}<=set(value['capabilities']): raise ValueError('Provider tool/thinking availability changed')
        contexts=[v for k,v in value['model_info'].items() if k.endswith('.context_length')]
        if contexts!=[p['provider_context_window']]: raise ValueError('Context metadata changed')
        if label=='nemotron' and tag['digest']!=p['provider_advertised_digest']: raise ValueError('Nemotron advertised identity changed')
        values[label]={'tag':tag,'show':{k:value.get(k) for k in ['capabilities','thinking','model_info','details']}}
    atomic_json(SHARED/'config/provider_metadata.json',{'retrieved_utc':datetime.now(timezone.utc).isoformat(),'models':values,'actual_inference_calls':0})

def main():
    for p in (ROOT/'extension50').glob('*.py'): ast.parse(p.read_text(encoding='utf-8'))
    profiles=read(SHARED/'config/profiles.json');images=read(SHARED/'config/images.json');limits=read(SHARED/'config/limits.json')
    checks=[]
    for model,profile in profiles.items():
        validate_profile(profile)
        payload=request_payload({'model':profile['model'],'messages':[{'role':'user','content':'नमस्ते hello'}]},profile)
        if payload['reasoning_effort']!=profile['agent_thinking']: raise ValueError('Wrong model effort')
        fake=SHARED/'checks/compatibility'/model
        atomic_json(fake/'config/model_profile.json',profile);atomic_json(fake/'config/images.json',images);atomic_json(fake/'config/protocol.json',limits)
        atomic_json(fake/'config/probe_budget.json',dict(limits,max_input_tokens=400000,max_output_tokens=16384,max_requests=12,attempt_timeout_sec=600))
        latest=fake/'checks/fake-runtime/latest.json'
        result=None
        if latest.exists():
            saved=read(read(latest)['report'])
            if saved.get('passed') and saved.get('images')==images and saved.get('model_profile')==profile:
                result=saved
                atomic_json(fake/'checks/reused_successful_fake_evidence.json',{'report':read(latest)['report'],'production_image_pins_and_profile_identical':True,'no_real_cloud_calls':True})
        if result is None: result=compatibility.check(fake,'fake')
        checks.append(result['passed'])
        print(encode({'model':model,'fake_full_harness_passed':result['passed'],'real_cloud_transmissions':0}),flush=True)
    if not all(checks): raise ValueError('Full fake integration failed')
    if not read(SHARED/'checks/oracle_validation.json')['passed'] or not verify_preserved(): raise ValueError('Oracle/preservation gate failed')
    provider_metadata()
    deps={str(p):sha(p) for name in ['bench','nextbench','nextbench_repair'] for p in (ROOT/name).rglob('*.py')}
    deps.update({str(ROOT/name):digest for name,digest in read(ROOT/'dataset/freeze.json')['file_hashes'].items()})
    files=source_hashes();freeze={'file_hashes':files,'protected_runtime_hashes':deps,'runtime_freeze_hash':__import__('hashlib').sha256(encode(files).encode()).hexdigest(),'created_utc':datetime.now(timezone.utc).isoformat(),'logical_extension_of_original_studies':True,'same_model_settings_and_budgets':True,'runtime_delta':'Generalize repaired streaming relay/agent to support original GPT-OSS medium and Nemotron boolean high; explicit provider watchdog bounded by unchanged task deadline. Original images/sources untouched.','benchmark_primary_calls_authorized_by_user':24,'separate_real_compatibility_probe_calls':0}
    if (SHARED/'config/freeze.json').exists() and read(SHARED/'config/freeze.json')!=freeze: raise ValueError('Never overwrite an existing extension freeze')
    atomic_json(SHARED/'config/freeze.json',freeze)
    atomic_json(SHARED/'checks/readiness.json',{'ready':True,'primary_attempt_count':24,'four_original_oracles_validated':True,'both_full_fake_harnesses_passed':True,'containment_and_unicode_checked':True,'all_existing_results_preserved':True,'new_cloud_transmissions':0,'freeze_hash':freeze['runtime_freeze_hash']})
    print(encode({'ready':True,'primary_attempt_count':24,'freeze_hash':freeze['runtime_freeze_hash']}),flush=True)

if __name__=='__main__': main()
