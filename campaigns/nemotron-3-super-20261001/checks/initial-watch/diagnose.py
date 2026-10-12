"""Two remaining authorized diagnostic transmissions; never replay a benchmark prompt."""
import hashlib
import io
import json
import sys
import time
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from bench.collector import Collector
from bench.credentials import load_keys
from bench.durable import Journal,atomic_json
from bench.lease import ControllerLease
from bench.security import docker,SecurityError
from nextbench.containers import CampaignContainers
from nextbench.compatibility import _relay,_retire

CAMPAIGN=Path(__file__).resolve().parents[2]
DEST=CAMPAIGN/'probes/timeout-diagnostics'

PATCH=r'''import io,json,time,urllib.request,sys
sys.path.insert(0,'/opt/ihb')
MODE=MODE_VALUE
real=urllib.request.build_opener
class Buffered(io.BytesIO):
 def __init__(self,data,status,headers): super().__init__(json.dumps(data,ensure_ascii=False).encode()); self.status=status; self.headers=headers
 def __enter__(self): return self
 def __exit__(self,*args): self.close()
class Timed:
 def __init__(self,opener): self.real=opener
 def open(self,request,*args,**kw):
  if request.full_url!='https://ollama.com/v1/chat/completions': return self.real.open(request,*args,**kw)
  begin=time.monotonic(); body=json.loads(request.data)
  if MODE=='streaming':
   body['stream']=True; body['stream_options']={'include_usage':True}
   request=urllib.request.Request(request.full_url,json.dumps(body,ensure_ascii=False).encode(),dict(request.header_items()))
  kw['timeout']=180
  try:
   response=self.real.open(request,*args,**kw)
   print(json.dumps({'diagnostic':MODE,'header_latency_sec':round(time.monotonic()-begin,3),'http_status':response.status}),file=sys.stderr,flush=True)
   if MODE=='buffered': return response
   data={'object':'chat.completion','choices':[]}; messages={}; total=0; first=None; usage=None
   with response:
    while True:
     if time.monotonic()-begin>180: raise TimeoutError('Diagnostic total time bound')
     line=response.readline(65537); total+=len(line)
     if total>4*1024*1024 or len(line)>65536: raise ValueError('Diagnostic response size bound')
     if not line: break
     if not line.startswith(b'data:'): continue
     payload=line[5:].strip()
     if payload==b'[DONE]': break
     chunk=json.loads(payload)
     if first is None:
      first=time.monotonic()-begin
      print(json.dumps({'diagnostic':MODE,'first_event_sec':round(first,3)}),file=sys.stderr,flush=True)
     for name in ('id','model','created','system_fingerprint'):
      if name in chunk: data[name]=chunk[name]
     if isinstance(chunk.get('usage'),dict): usage=chunk['usage']
     for choice in chunk.get('choices',[]):
      index=choice.get('index',0)
      row=messages.setdefault(index,{'index':index,'message':{'role':'assistant','content':''},'finish_reason':None})
      delta=choice.get('delta',{}); message=row['message']
      for name in ('content','reasoning','reasoning_content'):
       if isinstance(delta.get(name),str): message[name]=message.get(name,'')+delta[name]
      for tool in delta.get('tool_calls',[]) or []:
       tools=message.setdefault('tool_calls',[]); i=tool.get('index',0)
       while len(tools)<=i: tools.append({'id':'','type':'function','function':{'name':'','arguments':''}})
       target=tools[i]
       for name in ('id','type'):
        if tool.get(name): target[name]=tool[name]
       for name in ('name','arguments'):
        if isinstance(tool.get('function',{}).get(name),str): target['function'][name]+=tool['function'][name]
      if choice.get('finish_reason') is not None: row['finish_reason']=choice['finish_reason']
   data['choices']=[messages[i] for i in sorted(messages)]; data['usage']=usage
   print(json.dumps({'diagnostic':MODE,'complete_latency_sec':round(time.monotonic()-begin,3),'usage_received':usage is not None}),file=sys.stderr,flush=True)
   return Buffered(data,200,{'Content-Type':'application/json'})
  except Exception as error:
   print(json.dumps({'diagnostic':MODE,'upstream_error_type':type(error).__name__,'elapsed_sec':round(time.monotonic()-begin,3)}),file=sys.stderr,flush=True)
   raise
urllib.request.build_opener=lambda *args:Timed(real(*args))
import relay
relay.main()
'''


def check():
    if (DEST/'journal.sqlite3').exists(): raise ValueError('Never automatically replay recorded diagnostic spending')
    budget=json.loads((CAMPAIGN/'config/probe_budget.json').read_text())
    used=json.loads((CAMPAIGN/'probes/compatibility/report.json').read_text())
    remaining={k:budget[k]-used[source] for k,source in (
        ('max_requests','physical_transmissions'),('max_input_tokens','conservative_input_charge'),
        ('max_output_tokens','conservative_output_charge'))}
    if remaining['max_requests']!=2 or used['usage_missing_calls']!=0: raise ValueError('Diagnostic allowance requires manual review')
    remaining.update(max_response_tokens=4096,attempt_timeout_sec=500)
    profile=json.loads((CAMPAIGN/'config/model_profile.json').read_text())
    images=json.loads((CAMPAIGN/'config/images.json').read_text())
    # Reuse only the general OpenClaw system/tools, replacing all task instructions
    # and history with a benign synthetic diagnostic conversation.
    trace=next((CAMPAIGN/'results/runs/42220fe6cdd4f3b4a311a6f1/inference').glob('*.json'))
    template=json.loads(trace.read_text(encoding='utf-8'))['request']
    payload={'model':profile['model'],'tools':template['tools'],'stream':False,'messages':[
        template['messages'][0],
        {'role':'user','content':'IHB_DIAGNOSTIC केवल उपकरण द्वारा लौटाए गए पाठ की प्राप्ति स्वीकार करें। कोई और उपकरण न चलाएँ। ठीक DIAGNOSTIC_OK लिखें।'},
        {'role':'assistant','content':None,'reasoning_content':'I will inspect the synthetic diagnostic text.',
         'tool_calls':[{'id':'call_diagnostic_read','type':'function','function':{'name':'read','arguments':'{"path":"/workspace/in/diagnostic.txt"}'}}]},
        {'role':'tool','tool_call_id':'call_diagnostic_read','content':'नमस्ते\ndiagnostic text\n'}]}
    atomic_json(DEST/'request.json',payload)
    atomic_json(DEST/'allocation.json',{'prior':used,'remaining':remaining,'benchmark_evidence':False,
                'diagnostic_upstream_timeout_sec':180,'benchmark_upstream_timeout_unchanged_sec':120})
    keys=load_keys(); report={'passed':False,'benchmark_attempts':0,'modes':{},'remaining_allocation':remaining}
    with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(CAMPAIGN/'results/controller.lock'),closing(Journal(DEST/'journal.sqlite3')) as journal:
        ident=hashlib.sha256(b'authorized-two-call-timeout-diagnostic').hexdigest()[:24]
        journal.db.execute('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',(ident,'synthetic-tool-continuation','hi','separate-timeout-diagnostic'))
        journal.start(ident)
        collector=Collector(journal,ident,remaining,list(keys),trace_dir=DEST/'inference');collector.start()
        try:
            for mode in ('buffered','streaming'):
                box=CampaignContainers(journal,ident,images);proc=None;begin=time.monotonic()
                try:
                    net=box.internal(); caller=box.create('helper',network=net)
                    command=('python','-c',PATCH.replace('MODE_VALUE',repr(mode)))
                    proc,token=_relay(box,net,collector,keys,profile,4096,command)
                    client=r'''import json,sys,urllib.request,urllib.error,time
p=json.load(sys.stdin); token=p.pop('attempt_token'); begin=time.monotonic()
r=urllib.request.Request('http://ihb-relay:8080/v1/chat/completions',json.dumps(p,ensure_ascii=False).encode(),{'Authorization':'Bearer '+token,'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(r,timeout=205) as response: print(json.dumps({'http_status':response.status,'response':json.load(response),'elapsed_sec':time.monotonic()-begin},ensure_ascii=False))
except urllib.error.HTTPError as error:
 print(json.dumps({'http_status':error.code,'error':json.load(error),'elapsed_sec':time.monotonic()-begin}))
'''
                    value=json.loads(docker(['exec','-i',caller,'python','-c',client],input_bytes=json.dumps({**payload,'attempt_token':token},ensure_ascii=False).encode(),timeout=215))
                    atomic_json(DEST/mode/'response.json',value)
                    response=value.get('response',{})
                    report['modes'][mode]={'http_status':value['http_status'],'elapsed_sec':round(value['elapsed_sec'],3),
                        'reported_model':response.get('model'),'usage':response.get('usage'),
                        'finish_reason':response.get('choices',[{}])[0].get('finish_reason'),
                        'reply':response.get('choices',[{}])[0].get('message',{}).get('content'),
                        'collector_pause':collector.paused}
                    if collector.paused: break
                finally: _retire(box,proc)
        except Exception as error: report['diagnostic_error_type']=type(error).__name__
        finally:
            collector.close(); row=journal.get(ident)
            report.update(physical_transmissions=journal.db.execute('SELECT count(*) FROM forwards').fetchone()[0],
                          charged_input=row['input_bound'],charged_output=row['output_reserved'],
                          known_input_tokens=row['input_actual'],known_output_tokens=row['output_actual'],
                          usage_missing_calls=row['usage_missing'],all_resources_removed=not journal.resources())
            report['combined_probe_transmissions']=used['physical_transmissions']+report['physical_transmissions']
            report['combined_probe_charged_input']=used['conservative_input_charge']+row['input_bound']
            report['combined_probe_charged_output']=used['conservative_output_charge']+row['output_reserved']
            report['passed']=len(report['modes'])==2 and all(v['http_status']==200 for v in report['modes'].values())
            journal.finish(ident,'completed' if report['passed'] else 'infrastructure_failed',report)
            journal.export(DEST/'checkpoint'); atomic_json(DEST/'report.json',report)
    print(json.dumps(report,ensure_ascii=False)); return report


if __name__=='__main__': check()
