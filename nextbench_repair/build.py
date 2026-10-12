"""Thin new relay image; preserve all existing image tags and frozen configurations."""
import hashlib
import json
from pathlib import Path
from bench.durable import atomic_json
from bench.security import docker

ROOT=Path(__file__).resolve().parents[1]


def build(campaign):
    campaign=Path(campaign).resolve(); revision=campaign/'revisions/transport-v2'
    if (revision/'config/images.json').exists(): raise ValueError('Repair image configuration already exists')
    images=json.loads((campaign/'config/images.json').read_text())
    base=images['relay']['id']; info=json.loads(docker(['image','inspect',base]))[0]
    if info['Id']!=base or info['Config']['User']!='10001:10001': raise ValueError('Pinned relay base mismatch')
    context=revision/'build-context'; context.mkdir(parents=True,exist_ok=True)
    files={'relay.py':ROOT/'nextbench_repair/runtime/relay.py','upstream.py':ROOT/'nextbench_repair/upstream.py'}
    signature=hashlib.sha256(b''.join(p.read_bytes() for p in files.values())).hexdigest()[:12]
    tag='ihb-relay:nemotron-streaming-'+signature
    base_tag='ihb-streaming-base:'+base[7:19]; docker(['image','tag',base,base_tag])
    for name,path in files.items(): (context/name).write_bytes(path.read_bytes())
    file=context/'Dockerfile';file.write_text('FROM '+base_tag+'\nCOPY relay.py /opt/ihb/relay.py\nCOPY upstream.py /opt/ihb/upstream.py\nUSER 10001:10001\n',encoding='utf-8')
    docker(['build','--network=none','--pull=false','-f',str(file),'-t',tag,str(context)],timeout=600)
    made=json.loads(docker(['image','inspect',tag]))[0]
    if made['RootFS']['Layers'][:len(info['RootFS']['Layers'])]!=info['RootFS']['Layers'] or made['Config']['User']!='10001:10001':
        raise ValueError('Repaired relay changed containment or pinned base')
    images['relay']={'id':made['Id'],'tag':tag,'base_id':base,'source_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}}
    for name in ('model_profile.json','protocol.json','report_scope.json'):
        atomic_json(revision/'config'/name,json.loads((campaign/'config'/name).read_text()))
    atomic_json(revision/'config/images.json',images)
    atomic_json(revision/'config/probe_budget.json',{'max_requests':6,'max_input_tokens':200000,'max_output_tokens':16384,
        'max_response_tokens':4096,'attempt_timeout_sec':600,'benchmark_evidence':False,
        'authorization':'User instructed transport repair, bounded Hindi/Hinglish verification, then resume only if viable.'})
    atomic_json(revision/'config/transport.json',{'upstream_streaming':True,'initial_and_idle_socket_timeout_sec':180,
        'whole_attempt_timeout_unchanged':True,'deliver_only_after_durable_settlement':True,
        'preserve_all_initial_attempts':True,'additional_score_seeking_retries':False,
        'diagnosis_evidence':'probes/timeout-diagnostics/report.json','reason':'Valid Hindi buffered response took 129 seconds, exceeding v1 120-second timeout.'})
    return images


if __name__=='__main__':
    import sys
    print(json.dumps(build(sys.argv[1])))
