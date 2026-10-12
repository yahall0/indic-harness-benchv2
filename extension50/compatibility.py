"""Contained fake/live canaries with a separate durable, aggregate probe budget."""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shlex
import subprocess
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path

from nextbench_repair.collector import Collector
from bench.credentials import load_keys
from bench.durable import Journal, atomic_json
from bench.lease import ControllerLease
from bench.security import docker, restricted_args, validate_container, workspace_archive, safe_export, SecurityError
from nextbench.containers import CampaignContainers
from extension50.openclaw_config import configuration


MOCK = r'''import io,json,sys,time,urllib.request
sys.path.insert(0,'/opt/ihb')
real=urllib.request.build_opener
class Response(io.BytesIO):
 def __init__(self,data):
  rows=[]
  def event(value): rows.append('data: '+json.dumps(value,ensure_ascii=False)+'\n\n')
  for c in data['choices']:
   m=c['message']; delta={k:v for k,v in m.items() if k!='tool_calls' and v is not None}
   event({'id':data['id'],'model':data['model'],'choices':[{'index':c['index'],'delta':delta,'finish_reason':None}]})
   for i,t in enumerate(m.get('tool_calls') or []):
    args=t['function']['arguments']; middle=len(args)//2
    for n,fragment in enumerate((args[:middle],args[middle:])):
     tool={'index':i,'function':{'arguments':fragment}}
     if n==0: tool.update(id=t['id'],type=t['type']); tool['function']['name']=t['function']['name']
     event({'id':data['id'],'model':data['model'],'choices':[{'index':c['index'],'delta':{'tool_calls':[tool]},'finish_reason':None}]})
   event({'id':data['id'],'model':data['model'],'choices':[{'index':c['index'],'delta':{},'finish_reason':c['finish_reason']}]})
  event({'id':data['id'],'model':data['model'],'choices':[],'usage':data['usage']});rows.append('data: [DONE]\n\n')
  super().__init__(''.join(rows).encode()); self.status=200; self.headers={'Content-Type':'text/event-stream'}
 def __enter__(self): return self
 def __exit__(self,*args): self.close()
class Fake:
 def __init__(self,opener): self.real=opener
 def open(self,request,*a,**kw):
  if request.full_url!='https://ollama.com/v1/chat/completions': return self.real.open(request,*a,**kw)
  p=json.loads(request.data); assert p['model'] in ('nemotron-3-super','gpt-oss:20b') and p['reasoning_effort']==('medium' if p['model']=='gpt-oss:20b' else 'high') and p['stream'] is True and p['stream_options']['include_usage'] is True
  messages=p['messages']; last=max(i for i,m in enumerate(messages) if m['role']=='user' and ('IHB_PROBE' in str(m['content']) or 'IHB_COMMAND: ' in str(m['content']))) if any('IHB_PROBE' in str(m['content']) for m in messages) else max(i for i,m in enumerate(messages) if m['role']=='user'); text=str(messages[last]['content'])
  if 'IHB_COMMAND: ' in text and not any(m['role']=='tool' for m in messages[last+1:]):
   if 'IHB_DELAY' in text: time.sleep(130)
   command=text.split('IHB_COMMAND: ',1)[1].split('\n\nRuntime:',1)[0].strip(); names=[t['function']['name'] for t in p.get('tools',[])]
   name='exec' if 'exec' in names else 'tool_call'; args={'command':command,'yieldMs':1000}
   if name=='tool_call': args={'name':'exec','arguments':args}
   message={'role':'assistant','content':None,'reasoning':'विश्वसनीय नकली जाँच।','tool_calls':[{'id':'call_'+str(last),'type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}; finish='tool_calls'
  elif p['max_tokens']==8: message={'role':'assistant','content':'','reasoning':'unfinished'}; finish='length'
  else: message={'role':'assistant','content':'PROBE_OK हिन्दी ठीक है।','tool_calls':None}; finish='stop'
  return Response({'id':'fake-canary','object':'chat.completion','created':1,'model':p['model'],'choices':[{'index':0,'message':message,'finish_reason':finish}],'usage':{'prompt_tokens':min(100,len(request.data)),'completion_tokens':min(30,p['max_tokens']),'total_tokens':100+min(30,p['max_tokens'])}})
urllib.request.build_opener=lambda *a:Fake(real(*a))
import relay
relay.main()
'''


def _relay(box, net, collector, keys, profile, cap, command):
    relay = box.name('relay-probe'); box.record('container', relay)
    args = restricted_args(relay); args[args.index('--network') + 1] = 'bridge'
    docker(['create', '-i', *args, box.images['relay']['id'], *command])
    box.bind('container', relay)
    docker(['network', 'connect', '--alias', 'ihb-relay', net, relay])
    validate_container(json.loads(docker(['inspect', relay]))[0], network='bridge', relay_internal_network=net)
    token = secrets.token_hex(32)
    proc = subprocess.Popen(['docker', 'start', '-ai', relay], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    cfg = {'keys': keys, 'model': profile['model'], 'profile': profile,
           'upstream': 'https://ollama.com/v1/chat/completions', 'agent_token': token,
           'accounting': f'http://host.docker.internal:{collector.server.server_port}',
           'accounting_token': collector.token, 'max_response_tokens': cap}
    proc.stdin.write((json.dumps(cfg) + '\n').encode()); proc.stdin.flush()
    lines = []; thread = threading.Thread(target=lambda: lines.append(proc.stdout.readline(4096)), daemon=True)
    thread.start(); thread.join(20)
    if not lines or not json.loads(lines[0]).get('ready'):
        raise SecurityError('Probe relay startup failed')
    return proc, token


def _retire(box, proc):
    try:
        box.cleanup()
    finally:
        if proc:
            proc.stdin.close()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def _prompt(language, code):
    instruction = {
        'en': 'Use exec exactly once to run the literal command below, then reply PROBE_OK. Do not do any other work.',
        'hi': 'नीचे दिया गया कमांड चलाने के लिए exec का ठीक एक बार उपयोग करें, फिर PROBE_OK लिखें। कोई अन्य काम न करें।',
        'hinglish': 'Neeche diya exact command exec se sirf ek baar chalao, phir PROBE_OK likho. Koi aur kaam mat karo.',
    }[language]
    return ('IHB_PROBE\n' + instruction + '\nIf exec is deferred, call tool_call directly with name exec and arguments command (the literal command) and yieldMs 1000.\nIHB_COMMAND: python -c ' + shlex.quote(code))


def check(campaign, mode):
    campaign = Path(campaign).resolve(); root = Path(__file__).resolve().parents[1]
    profile = json.loads((campaign / 'config/model_profile.json').read_text())
    protocol = json.loads((campaign / 'config/protocol.json').read_text())
    limits = json.loads((campaign / 'config/probe_budget.json').read_text())
    if mode != 'fake': raise ValueError('Use the separately capped repair canary for live requests')
    dest = campaign / ('probes/compatibility' if mode == 'cloud' else 'checks/fake-runtime/' + uuid.uuid4().hex[:12])
    if (dest / 'journal.sqlite3').exists():
        raise ValueError('A recorded suite already exists; never automatically replay probe spending')
    limits = dict(limits, max_requests=12)
    keys = load_keys() if mode == 'cloud' else {'slot-1': 'FAKE_NO_CLOUD_KEY'}
    command = () if mode == 'cloud' else ('python', '-c', MOCK)
    with ControllerLease(root / 'results/controller.lock'), ControllerLease(campaign / 'results/controller.lock'), \
            closing(Journal(dest / 'journal.sqlite3')) as journal:
        study = hashlib.sha256((mode + ':' + str(campaign) + ':compatibility').encode()).hexdigest()
        ident = hashlib.sha256((study + ':mixed:1').encode()).hexdigest()[:24]
        journal.db.execute('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',
                           (ident, 'compatibility-suite', 'mixed', study))
        row = journal.get(ident)
        # One aggregate allowance covers every phase, including all retries.
        journal.start(row['id'])
        collector = Collector(journal, row['id'], limits, list(keys), trace_dir=dest / 'inference')
        collector.start()
        report = {'passed': False, 'mode': mode, 'benchmark_attempts': 0,
                  'checks': {}, 'phases': [], 'budget': limits, 'model_profile': profile,
                  'images': json.loads((campaign / 'config/images.json').read_text()),
                  'runtime_sources_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                      for name in ('nextbench/runtime/agent.py','nextbench_repair/runtime/relay.py','nextbench/contract.py','nextbench_repair/upstream.py')}}
        checks = report['checks']; begin = time.monotonic()
        try:
            for language, rounds, delayed in (('en', 1, False), ('hi', 1, False), ('hinglish', 2, False)):
                phase = f'{language}-{rounds}-rounds'+('-delayed' if delayed else '')
                box = CampaignContainers(journal, row['id'], json.loads((campaign / 'config/images.json').read_text()))
                proc = None
                try:
                    net, volume = box.internal(), box.workspace()
                    keeper = box.create('helper', volume=volume)
                    agent = box.create('agent', network=net, volume=volume)
                    proc, token = _relay(box, net, collector, keys, profile, 4096, command)
                    box.invoke(agent, {'action': 'configure', 'config': configuration(token, profile, protocol)}, program='/opt/ihb/agent.py')
                    # Trusted controller code executes only inside the hardened
                    # agent container. It does not depend on the model's honesty.
                    audit = r'''import json,os,socket
from pathlib import Path
c={}
for name,path in [('host_drive','/run/desktop/mnt/host/c'),('windows_mount','/mnt/c'),('docker_socket','/var/run/docker.sock'),('grader_files','/opt/ihb/tasks'),('solutions','/opt/ihb/validation')]: c[name+'_absent']=not Path(path).exists()
c['real_keys_absent']=not any('OLLAMA_KEY' in k or k=='OLLAMA_API_KEY' for k in os.environ)
try: Path('/etc/ihb-write-test').write_text('blocked'); c['root_readonly']=False
except OSError: c['root_readonly']=True
for name,host,port in [('internet','1.1.1.1',443),('host_accounting','host.docker.internal',HOST_PORT),('host_smb','host.docker.internal',445)]:
 try: s=socket.create_connection((host,port),timeout=1); s.close(); c[name+'_blocked']=False
 except OSError: c[name+'_blocked']=True
print(json.dumps(c))
'''.replace('HOST_PORT', str(collector.server.server_port))
                    boundary = json.loads(docker(['exec', agent, 'python', '-c', audit]))
                    checks[phase + '_boundary'] = all(boundary.values())
                    atomic_json(dest / phase / 'boundary.json', boundary)
                    for index in range(rounds):
                        value = 'नमस्ते_' + language
                        code = "from pathlib import Path; p=Path('/workspace/out/probe.txt'); "
                        if index == 0:
                            code += "p.parent.mkdir(exist_ok=True); p.write_text(" + repr(value) + ",encoding='utf-8')"
                        else:
                            code += "assert p.read_text(encoding='utf-8')==" + repr(value) + "; Path('/workspace/out/round2.txt').write_text('state_preserved')"
                        result = box.invoke(agent, {'action': 'round', 'session': 'probe-' + phase,
                            'round': index + 1, 'timeout': 180 if delayed else 90, 'thinking': profile['agent_thinking'],
                            'prompt': ('IHB_DELAY\n' if delayed else '')+_prompt(language, code)},
                            timeout=195 if delayed else 105, program='/opt/ihb/agent.py')
                        atomic_json(dest / phase / f'round-{index+1}.json', result)
                        checks[phase + f'_round_{index+1}'] = result['returncode'] == 0 and collector.paused is None
                        journal.export(dest / 'checkpoints/latest')
                        if not checks[phase + f'_round_{index+1}']:
                            raise SecurityError('Canary failed or its aggregate budget/provider gate paused')
                    docker(['kill', agent])
                    checks[phase + '_agent_stopped'] = not json.loads(docker(['inspect', agent]))[0]['State']['Running']
                    data = workspace_archive(keeper)
                    safe_export(data, dest / phase / 'artifacts')
                    grader = box.create('grader'); box.import_archive(grader, data)
                    grader_code = "from pathlib import Path; import json; c={'unicode_artifact':Path('/workspace/out/probe.txt').read_text(encoding='utf-8')==" + repr(value) + "}; "
                    if rounds == 2:
                        grader_code += "c['multi_round_state']=Path('/workspace/out/round2.txt').read_text()=='state_preserved'; "
                    grader_code += 'print(json.dumps(c))'
                    graded = json.loads(docker(['exec', grader, 'python', '-c', grader_code]))
                    checks[phase + '_separate_grader'] = all(graded.values())
                    atomic_json(dest / phase / 'grader.json', graded)
                    report['phases'].append({'phase': phase, 'known_checks': graded})
                finally:
                    _retire(box, proc)
            for phase, cap, content in [('truncation', 8, 'Count from one to one hundred; show detailed reasoning.'),
                                        ('context', 512, 'Read this filler and then reply PROBE_OK: ' + 'context_probe ' * 2000)]:
                box = CampaignContainers(journal, row['id'], json.loads((campaign / 'config/images.json').read_text()))
                proc = None
                try:
                    net = box.internal(); caller = box.create('helper', network=net)
                    proc, token = _relay(box, net, collector, keys, profile, cap, command)
                    client = r'''import json,sys,urllib.request
p=json.load(sys.stdin);token=p.pop('attempt_token')
r=urllib.request.Request('http://ihb-relay:8080/v1/chat/completions',json.dumps(p,ensure_ascii=False).encode(),{'Authorization':'Bearer '+token,'Content-Type':'application/json'})
with urllib.request.urlopen(r,timeout=130) as response: print(json.dumps(json.load(response),ensure_ascii=False))
'''
                    payload = {'model': profile['model'], 'messages': [{'role': 'user', 'content': content}],
                               'stream': False, 'attempt_token': token}
                    response = json.loads(docker(['exec', '-i', caller, 'python', '-c', client],
                        input_bytes=json.dumps(payload, ensure_ascii=False).encode(), timeout=140))
                    atomic_json(dest / phase / 'response.json', response)
                    checks[phase + '_identity'] = response['model'] in profile['response_model_aliases']
                    checks[phase + '_usage'] = isinstance(response.get('usage'), dict)
                    checks[phase + '_finish_reason'] = response['choices'][0].get('finish_reason') in {'stop', 'length'}
                    if phase == 'truncation':
                        checks['truncation_length_preserved'] = response['choices'][0]['finish_reason'] == 'length'
                    report['phases'].append({'phase': phase, 'finish_reason': response['choices'][0].get('finish_reason')})
                finally:
                    _retire(box, proc)
            traces = [json.loads(p.read_text(encoding='utf-8')) for p in (dest / 'inference').glob('*.response.json')]
            checks['thinking_alias_explicit'] = all(t['request']['reasoning_effort'] == profile['provider_reasoning_effort'] for t in traces)
            checks['reported_identity_exact'] = all(t['response'].get('model') in profile['response_model_aliases'] for t in traces)
            checks['no_unsettled_calls'] = journal.db.execute("SELECT COUNT(*) FROM calls WHERE status!='settled'").fetchone()[0] == 0
            checks['all_owned_resources_removed'] = not journal.resources()
            report['passed'] = bool(checks) and all(checks.values())
        except Exception as error:
            report.update(error_type=type(error).__name__, error_summary='Inspect the separately recorded canary results and accounting; no automatic probe replay.')
        finally:
            collector.close()
            saved = journal.get(row['id'])
            report.update(elapsed_sec=round(time.monotonic()-begin, 3), physical_transmissions=journal.db.execute('SELECT count(*) FROM forwards').fetchone()[0],
                          known_input_tokens=saved['input_actual'], known_output_tokens=saved['output_actual'],
                          conservative_input_charge=saved['input_bound'], conservative_output_charge=saved['output_reserved'],
                          usage_missing_calls=saved['usage_missing'], credential_slots=journal.slot_state())
            journal.finish(row['id'], 'completed' if report['passed'] else 'infrastructure_failed', report)
            journal.export(dest / 'checkpoints/latest')
            atomic_json(dest / 'report.json', report)
            if mode == 'fake':
                atomic_json(campaign / 'checks/fake-runtime/latest.json', {'report': str(dest / 'report.json'), 'passed': report['passed']})
    print(json.dumps({k: report[k] for k in ('passed','mode','physical_transmissions','known_input_tokens','known_output_tokens','checks')}))
    return report


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('campaign', type=Path)
    parser.add_argument('--mode', choices=('fake', 'cloud'), default='fake'); args = parser.parse_args()
    raise SystemExit(0 if check(args.campaign, args.mode)['passed'] else 1)


if __name__ == '__main__':
    main()
