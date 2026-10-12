"""Explicitly requested small credential probes; never benchmark observations."""
import json
import uuid
from datetime import datetime,timezone
from pathlib import Path
from bench.credentials import load_keys
from bench.durable import atomic_json
from bench.security import docker,restricted_args,remove_owned

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=r'''
import json,sys,time,urllib.request,urllib.error
from bench.rotation import classify
keys=json.load(sys.stdin)
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k): return None
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
rows=[]
for slot,key in keys.items():
 start=time.monotonic()
 p={'model':'gpt-oss:20b','messages':[{'role':'user','content':'Reply with only OK.'}], 'temperature':0,'reasoning_effort':'none','max_tokens':16,'stream':False}
 req=urllib.request.Request('https://ollama.com/v1/chat/completions',json.dumps(p).encode(),{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 try:
  with opener.open(req,timeout=45) as resp:
   data=json.load(resp); row={'slot':slot,'http_status':resp.status,'classification':'success','model':data.get('model'), 'usage':data.get('usage'), 'response_present':bool(data.get('choices'))}
 except urllib.error.HTTPError as e:
  body=e.read(65536); row={'slot':slot,'http_status':e.code,'classification':classify(e.code,body),'usage':None}
 except Exception:
  row={'slot':slot,'http_status':None,'classification':'transport_failure','usage':None}
 row['elapsed_sec']=round(time.monotonic()-start,3); rows.append(row)
 print(json.dumps({'probe_progress':slot,'classification':row['classification']}),flush=True)
print(json.dumps({'key_checks':rows}),flush=True)
'''

def check():
    keys=load_keys(); images=json.loads((ROOT/'config/images.json').read_text())
    name='ihb-keycheck-'+uuid.uuid4().hex[:12]
    try:
        args=restricted_args(name)
        # Trusted relay-only credential test, with no evaluated agent attached.
        args[args.index('--network')+1]='bridge'
        docker(['create',*args,images['relay']['id'],'sleep','240'])
        docker(['start',name])
        output=docker(['exec','-i',name,'python','-c',SCRIPT],input_bytes=json.dumps(keys).encode(),timeout=200)
        lines=output.decode().splitlines(); result=json.loads(lines[-1])
        result.update(timestamp_utc=datetime.now(timezone.utc).isoformat(),purpose='credential_probe_only',
                      max_requests=len(keys),max_output_tokens_per_request=16,benchmark_runs=0,
                      secrets_disclosed=False,automatic_retries=0)
        import hashlib
        store=ROOT/'config/credentials.dpapi.json'
        if store.exists(): result['key_store_cipher_sha256']=hashlib.sha256(store.read_bytes()).hexdigest()
        atomic_json(ROOT/'reports/key_check.json',result)
        print(json.dumps(result,indent=2),flush=True)
        return result
    finally: remove_owned('container',name)

if __name__=='__main__': check()
