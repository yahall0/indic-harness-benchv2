"""Exercise real relay HTTP/SQLite accounting with simulated provider quota responses."""
import json,subprocess,threading,uuid,secrets
from pathlib import Path
from bench.collector import Collector
from bench.containers import Containers
from bench.durable import Journal,atomic_json
from bench.security import docker,restricted_args,validate_container,SecurityError

ROOT=Path(__file__).resolve().parents[1]
MOCK=r'''import io,json,urllib.request,urllib.error,urllib.parse,sys
sys.path.insert(0,'/opt/ihb')
original=urllib.request.build_opener
counts={}
lost_acks=set()
class Response(io.BytesIO):
 def __init__(self,data): super().__init__(json.dumps(data).encode()); self.status=200; self.headers={}
 def __enter__(self): return self
 def __exit__(self,*args): self.close()
class Fake:
 def __init__(self,real): self.real=real
 def open(self,r,*a,**kw):
  if r.full_url!='https://ollama.com/v1/chat/completions':
   data=json.loads(r.data); path=urllib.parse.urlparse(r.full_url).path
   target=path if path!='/event' else path+':'+str(data.get('kind'))
   response=self.real.open(r,*a,**kw)
   if target in {'/reserve','/trace','/settle','/rejected','/quota','/event:inference_forwarded'} and target not in lost_acks:
    response.read();response.close();lost_acks.add(target)
    raise urllib.error.URLError('Simulated lost acknowledgment after committed accounting')
   return response
  slot=r.get_header('Authorization').split()[-1]; counts[slot]=counts.get(slot,0)+1
  if slot=='FAKE_1' and counts[slot]<=2: body={'error':'too many requests'}
  elif (slot=='FAKE_1' and counts[slot]>=4) or slot in ('FAKE_2','FAKE_3') or (slot=='FAKE_4' and counts[slot]>=2): body={'error':{'code':'insufficient_quota'}}
  else:
   data=json.loads(r.data)
   assert data['temperature']==0 and data['reasoning_effort']=='medium' and data['max_tokens']<=4096
   return Response({'model':'gpt-oss:20b','choices':[{'message':{'role':'assistant','content':'fake success'},'finish_reason':'stop'}],'usage':{'prompt_tokens':10,'completion_tokens':2}})
  raise urllib.error.HTTPError(r.full_url,429,'provider simulation',{'Retry-After':'0'},io.BytesIO(json.dumps(body).encode()))
urllib.request.build_opener=lambda *args:Fake(original(*args))
import relay
relay.main()
'''

def check_relay():
    ident=uuid.uuid4().hex[:12]; dest=ROOT/'work/relay-check'/ident; dest.mkdir(parents=True)
    j=Journal(dest/'journal.sqlite3'); j.plan(['relay-canary'],ident); row=j.runs()[0]; j.start(row['id'])
    limits=json.loads((ROOT/'config/protocol.json').read_text()); keys={'slot-'+str(i):'FAKE_'+str(i) for i in range(1,5)}
    collector=Collector(j,row['id'],limits,list(keys),trace_dir=dest/'inference'); port=collector.start()
    box=Containers(j,row['id']); proc=None; report={'passed':False,'cloud_requests':0,'benchmark_runs':0,'relay_image':box.images['relay']['id'],'checks':{}}
    try:
        net=box.internal(); caller=box.create('helper',network=net)
        relay=box.name('relay-rotation'); box.record('container',relay)
        args=restricted_args(relay); args[args.index('--network')+1]='bridge'
        docker(['create','-i',*args,box.images['relay']['id'],'python','-c',MOCK]); box.bind('container',relay)
        docker(['network','connect','--alias','ihb-relay',net,relay])
        validate_container(json.loads(docker(['inspect',relay]))[0],network='bridge',relay_internal_network=net)
        token=secrets.token_hex(32)
        proc=subprocess.Popen(['docker','start','-ai',relay],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        cfg={'keys':keys,'model':limits['model'],'upstream':limits['upstream'],'agent_token':token,
             'accounting':f'http://host.docker.internal:{port}','accounting_token':collector.token,'max_response_tokens':4096}
        proc.stdin.write((json.dumps(cfg)+'\n').encode()); proc.stdin.flush()
        ready=[]; t=threading.Thread(target=lambda:ready.append(proc.stdout.readline(4096)),daemon=True); t.start(); t.join(15)
        if not ready or not ready[0]: raise SecurityError('Relay rotation test startup failed')
        client=r'''import json,sys,urllib.request,urllib.error
payload={'model':'gpt-oss:20b','messages':[{'role':'user','content':'fake quota test'}]}
for path,auth in [('/forward','TOKEN'),('/v1/chat/completions','wrong'),('/v1/chat/completions','TOKEN'),('/v1/chat/completions','TOKEN'),('/v1/chat/completions','TOKEN'),('/v1/chat/completions','TOKEN')]:
 r=urllib.request.Request('http://ihb-relay:8080'+path,json.dumps(payload).encode(),{'Authorization':'Bearer '+auth.replace('TOKEN',sys.argv[1]),'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(r,timeout=25) as response: print(json.dumps({'status':response.status,'body':json.load(response)}))
 except urllib.error.HTTPError as e: print(json.dumps({'status':e.code,'body':json.load(e)}))
'''
        responses=[json.loads(line) for line in docker(['exec',caller,'python','-c',client,token],timeout=60).decode().splitlines()]
        physical=[dict(r) for r in j.db.execute('SELECT * FROM forwards ORDER BY at')]
        ids=[r['slot'] for r in physical]
        checks={'endpoint_not_forwarded':responses[0]['status']==404,'bad_attempt_token_blocked':responses[1]['status']==403,
                'generic_429_same_key_retries':ids[:3]==['slot-1']*3,
                'confirmed_quota_rotates_in_order':ids[3:7]==['slot-1','slot-2','slot-3','slot-4'],
                'successful_requests_200':responses[2]['status']==responses[3]['status']==200,
                'all_keys_exhausted_pauses':responses[4]['status']==503 and all(s['state']=='exhausted' for s in j.slot_state()),
                'paused_request_no_extra_spending':responses[5]['status']==503 and len(physical)==8,
                'all_transmissions_accounted':j.get(row['id'])['requests']==8,
                'quota_state_durable':True,
                'lost_local_acknowledgments_recovered':j.db.execute("SELECT COUNT(*) FROM events WHERE kind='accounting_transport_retry'").fetchone()[0]>=6}
        j.export(dest/'checkpoint'); backup=Journal(dest/'checkpoint/journal-backup.sqlite3')
        try: checks['quota_state_durable']=all(s['state']=='exhausted' for s in backup.slot_state())
        finally: backup.close()
        report.update(passed=all(checks.values()),checks=checks,physical_slot_sequence=ids,controller_pause=collector.paused,evidence_directory=str(dest))
    except Exception as e: report.update(error=str(e)[:3000],error_type=type(e).__name__,evidence_directory=str(dest))
    finally:
        try: box.cleanup()
        except Exception as e: report.update(passed=False,cleanup_error=str(e))
        collector.close()
        if proc:
            proc.stdin.close()
            try: proc.wait(5)
            except subprocess.TimeoutExpired: proc.kill()
        j.finish(row['id'],'completed' if report['passed'] else 'infrastructure_failed',report); j.export(dest/'checkpoint'); j.close()
        from bench.fingerprint import runtime_fingerprint
        report['runtime_fingerprint']=runtime_fingerprint()
        atomic_json(ROOT/'reports/relay_check.json',report)
    print(json.dumps(report),flush=True); return report

if __name__=='__main__': raise SystemExit(0 if check_relay()['passed'] else 1)
