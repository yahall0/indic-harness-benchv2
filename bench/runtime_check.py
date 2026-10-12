"""No-credit integration check: actual OpenClaw + production relay with fake transport."""
import json
import secrets
import shlex
import subprocess
import threading
import uuid
from pathlib import Path
from bench.collector import Collector
from bench.containers import Containers
from bench.durable import Journal,atomic_json
from bench.openclaw_config import configuration
from bench.security import docker,restricted_args,validate_container,workspace_archive,safe_export,SecurityError

ROOT=Path(__file__).resolve().parents[1]

def mock_transport_code(command):
    # Installed only as a trusted integration-test argv, never selectable by the live controller.
    return '''import io,json,urllib.request,urllib.error,sys
sys.path.insert(0,'/opt/ihb')
original=urllib.request.build_opener
command='''+repr(command)+'''
class Response(io.BytesIO):
 def __init__(self,data): super().__init__(json.dumps(data).encode()); self.status=200; self.headers={}
 def __enter__(self): return self
 def __exit__(self,*args): self.close()
class Fake:
 def __init__(self,real): self.real=real
 def open(self,request,*args,**kwargs):
  if request.full_url!='https://ollama.com/v1/chat/completions': return self.real.open(request,*args,**kwargs)
  data=json.loads(request.data); messages=data['messages']; tools=data.get('tools',[])
  last_user=max((i for i,m in enumerate(messages) if m.get('role')=='user' and any(marker in str(m.get('content','')) for marker in ('ROUND_ONE','ROUND_TWO'))),default=-1)
  finished=any(m.get('role')=='tool' for m in messages[last_user+1:])
  if finished: message={'role':'assistant','content':'जाँच सफल।','tool_calls':None}; reason='stop'
  else:
   names=[t['function']['name'] for t in tools]
   assert 'exec' in names,names
   prompt=str(messages[last_user].get('content',''))
   cmd=command if 'ROUND_ONE' in prompt else "python -c \\"from pathlib import Path; assert Path('/workspace/out/canary.txt').read_text()=='persisted'; Path('/workspace/out/round2.txt').write_text('state_preserved')\\""
   message={'role':'assistant','content':None,'tool_calls':[{'id':'call_canary_'+str(last_user),'type':'function','function':{'name':'exec','arguments':json.dumps({'command':cmd,'yieldMs':1000})}}]}; reason='tool_calls'
  return Response({'id':'fake-canary','object':'chat.completion','created':1,'model':'gpt-oss:20b','choices':[{'index':0,'message':message,'finish_reason':reason}],'usage':{'prompt_tokens':100,'completion_tokens':30,'total_tokens':130}})
urllib.request.build_opener=lambda *args:Fake(original(*args))
import relay
relay.main()
'''

def check_runtime():
    ident=uuid.uuid4().hex[:12]; dest=ROOT/'work/runtime-check'/ident; dest.mkdir(parents=True)
    journal=Journal(dest/'journal.sqlite3'); journal.plan(['integration-canary'],ident)
    row=journal.runs()[0]; journal.start(row['id'])
    limits=json.loads((ROOT/'config/protocol.json').read_text())
    collector=Collector(journal,row['id'],limits,['slot-1'],trace_dir=dest/'inference'); port=collector.start()
    box=Containers(journal,row['id']); proc=None
    report={'passed':False,'scope':'Actual OpenClaw, production relay, trusted accounting and restricted grader; fake inference transport only','cloud_requests':0,'benchmark_runs':0,'images':box.images,'checks':{}}
    try:
        net=box.internal(); volume=box.workspace()
        keeper=box.create('helper',volume=volume)
        agent=box.create('agent',network=net,volume=volume)
        prepared,_=box.prepared('001-file'); box.import_archive(agent,prepared)
        token=secrets.token_hex(32)
        box.invoke(agent,{'action':'configure','config':configuration(token,limits['model'])},program='/opt/ihb/agent.py')
        canary='''import json,os,socket
from pathlib import Path
checks={}
for name,path in [('host_drive','/run/desktop/mnt/host/c'),('windows_mount','/mnt/c'),('docker_socket','/var/run/docker.sock'),('grader_files','/opt/ihb/tasks'),('solutions','/opt/ihb/validation')]: checks[name+'_absent']=not Path(path).exists()
checks['cloud_keys_absent']=not any('OLLAMA_KEY' in k or k=='OLLAMA_API_KEY' for k in os.environ)
try: Path('/etc/ihb-write-test').write_text('blocked'); checks['read_only_root']=False
except OSError: checks['read_only_root']=True
for name,host,port in [('internet','1.1.1.1',443),('host_accounting','host.docker.internal',HOST_PORT),('host_smb','host.docker.internal',445)]:
 try: s=socket.create_connection((host,port),timeout=1); s.close(); checks[name+'_blocked']=False
 except OSError: checks[name+'_blocked']=True
Path('/workspace/out').mkdir(exist_ok=True)
Path('/workspace/out/security.json').write_text(json.dumps(checks))
Path('/workspace/out/canary.txt').write_text('persisted')
Path('/workspace/out/linecount.txt').write_text('4\\n')
'''.replace('HOST_PORT',str(port))
        command='python -c '+shlex.quote(canary)
        relay=box.name('relay-test'); box.record('container',relay)
        args=restricted_args(relay); args[args.index('--network')+1]='bridge'
        docker(['create','-i',*args,box.images['relay']['id'],'python','-c',mock_transport_code(command)])
        box.bind('container',relay); docker(['network','connect','--alias','ihb-relay',net,relay])
        validate_container(json.loads(docker(['inspect',relay]))[0],network='bridge',relay_internal_network=net)
        proc=subprocess.Popen(['docker','start','-ai',relay],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        cfg={'keys':{'slot-1':'FAKE_INTEGRATION_KEY'},'model':limits['model'],'upstream':limits['upstream'],
             'accounting':f'http://host.docker.internal:{port}','accounting_token':collector.token,'agent_token':token,'max_response_tokens':4096}
        proc.stdin.write((json.dumps(cfg)+'\n').encode()); proc.stdin.flush()
        ready=[]; thread=threading.Thread(target=lambda:ready.append(proc.stdout.readline(4096)),daemon=True)
        thread.start(); thread.join(15)
        if not ready or not ready[0]:
            docker(['kill',relay]); raise SecurityError('Test relay failed: '+proc.stderr.read(4000).decode())
        for i,marker in enumerate(('ROUND_ONE','ROUND_TWO')):
            result=box.invoke(agent,{'action':'round','session':'integration-'+ident,'round':i+1,'timeout':60,'prompt':marker+' जाँच का tool चलाएँ और पूरा करें।'},timeout=75,program='/opt/ihb/agent.py')
            atomic_json(dest/f'round-{i+1}.json',result)
            if result['returncode']!=0: raise SecurityError('OpenClaw canary round failed; see saved round trace')
            docker(['pause',agent]); data=workspace_archive(agent)
            (dest/f'round-{i+1}-workspace.tar').write_bytes(data)
            docker(['unpause',agent]); journal.export(dest/'checkpoint')
        docker(['kill',agent])
        data=workspace_archive(keeper); safe_export(data,dest/'artifacts')
        checks=json.loads((dest/'artifacts/out/security.json').read_text())
        checks['multi_round_state']=(dest/'artifacts/out/round2.txt').read_text()=='state_preserved'
        checks['agent_stopped_before_grading']=not json.loads(docker(['inspect',agent]))[0]['State']['Running']
        grade=box.grade('001-file',data); report['grader_result']=grade
        checks['separate_original_oracle']=grade['oracle']['outcome_score']==1 and not grade['integrity_violations']
        checks['accounting_outside_agent']=len(list((dest/'inference').glob('*.json')))==4 and journal.get(row['id'])['requests']==4
        checks['no_accounting_pause']=collector.paused is None
        traces=[json.loads(p.read_text(encoding='utf-8')) for p in (dest/'inference').glob('*.json')]
        checks['devanagari_request_preserved']=all(any('जाँच' in str(m.get('content','')) for m in t['request']['messages']) for t in traces)
        checks['devanagari_response_preserved']=sum(any(c.get('message',{}).get('content')=='जाँच सफल।' for c in t['response']['choices']) for t in traces)==2
        checks['nullable_tool_calls_handled']=sum(any('tool_calls' in c['message'] and c['message']['tool_calls'] is None for c in t['response']['choices']) for t in traces)==2
        report.update(checks=checks,passed=all(checks.values()),evidence_directory=str(dest))
    except Exception as e:
        report.update(error_type=type(e).__name__,error=str(e)[:3000],evidence_directory=str(dest))
    finally:
        try: box.cleanup()
        except Exception as e: report.update(passed=False,cleanup_error=str(e))
        collector.close()
        if proc:
            proc.stdin.close()
            try: proc.wait(5)
            except subprocess.TimeoutExpired: proc.kill()
        journal.finish(row['id'],'completed' if report['passed'] else 'infrastructure_failed',report)
        journal.export(dest/'checkpoint'); journal.close()
        from bench.fingerprint import runtime_fingerprint
        report['runtime_fingerprint']=runtime_fingerprint()
        atomic_json(ROOT/'reports/runtime_check.json',report)
    print(json.dumps(report),flush=True)
    return report

if __name__=='__main__':
    raise SystemExit(0 if check_runtime()['passed'] else 1)
