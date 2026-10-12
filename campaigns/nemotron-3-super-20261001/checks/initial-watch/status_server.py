"""Loopback-only, read-only progress display. No inference or control endpoints."""
import ctypes,json,math,sys,time
from collections import Counter
from contextlib import closing
from datetime import datetime,timedelta,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import atomic_json
from nextbench.monitor import snapshot
CAMPAIGN=Path(__file__).resolve().parents[2]
IST=timezone(timedelta(hours=5,minutes=30))

def controller_state(record_path=None):
 p=Path(record_path) if record_path else CAMPAIGN/'results/controller_process.json'
 if not p.exists(): return 'stopped'
 try:
  record=json.loads(p.read_text(encoding='utf-8-sig'));pid=int(record['pid'])
  kernel=ctypes.WinDLL('kernel32',use_last_error=True)
  kernel.OpenProcess.restype=ctypes.c_void_p
  kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
  kernel.CloseHandle.argtypes=[ctypes.c_void_p]
  handle=kernel.OpenProcess(0x1000,False,pid)
  if not handle: return 'stopped'
  try:
   exitcode=ctypes.c_ulong();kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
   if not kernel.GetExitCodeProcess(handle,ctypes.byref(exitcode)): return 'unknown'
   if exitcode.value!=259: return 'stopped'
   created,ended,kernel_time,user_time=(ctypes.c_ulonglong() for _ in range(4))
   kernel.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_ulonglong)]*4
   if not kernel.GetProcessTimes(handle,*[ctypes.byref(v) for v in (created,ended,kernel_time,user_time)]): return 'unknown'
   started=datetime.fromisoformat(record['started_utc']).timestamp()
   process_started=created.value/10000000-11644473600
   return 'running' if started-180<=process_started<=started+1 else 'stopped'
  finally: kernel.CloseHandle(handle)
 except (OSError,ValueError,KeyError): return 'unknown'

def brief(row):
 result=json.loads(row['result'] or '{}');score=result.get('oracle',{}).get('outcome_score')
 scored=row['status'] in {'completed','agent_failed','budget_exhausted','timeout','integrity_failed'}
 return {'task':row['task'],'language':row['language'],'status':row['status'],
         'score':score if scored and isinstance(score,(int,float)) and math.isfinite(score) else None,
         'requests':row['requests'],'elapsed':round(time.time()-row['started']) if row['status']=='running' else None}

def status():
 data=snapshot(CAMPAIGN);rows=data['primary'];retry=data['recovery'];states=Counter(r['status'] for r in rows)
 pending=set()
 with closing(sqlite3.connect((CAMPAIGN/'results/journal.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
  db.execute('PRAGMA query_only=ON');pending={r[0] for r in db.execute('SELECT primary_run_id FROM recovery_attempts')}
 groups={}
 for row in rows:
  groups.setdefault(row['task'],{})[row['language']]={'primary':brief(row),
   'recovery':brief(retry[row['id']]) if row['id'] in retry else None,
   'recovery_queued':row['id'] in pending and row['id'] not in retry}
 stage_path=CAMPAIGN/'results/repair_status.json'
 stage=json.loads(stage_path.read_text()) if stage_path.exists() else {}
 gate=CAMPAIGN/'revisions/transport-v2/probes/hindi-hinglish-final/journal.sqlite3'
 verification=None
 if gate.exists():
  with closing(sqlite3.connect(gate.as_uri()+'?mode=ro',uri=True)) as db:
   db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');r=db.execute('SELECT status,requests,input_actual,output_actual,usage_missing FROM runs').fetchone()
   verification=dict(r) if r else None
 all_rows=rows+list(retry.values())
 extra=[];extra_phase=None;extra_controller=None
 registry_path=CAMPAIGN/'results/additional_recovery_registry.json'
 if registry_path.exists():
  registry=json.loads(registry_path.read_text())
  if registry.get('journal')!='additional-recoveries/20261002/journal.sqlite3' or registry.get('attempt_number')!=3:
   raise ValueError('Unexpected additional recovery registry')
  batch=CAMPAIGN/'results/additional-recoveries/20261002'
  with closing(sqlite3.connect((batch/'journal.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
   db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
   extra=[dict(r) for r in db.execute('SELECT * FROM runs')]
  for _,task,language in registry['targets']:
   found=next((r for r in extra if r['task']==task and r['language']==language),None)
   if found:groups[task][language]['additional_recovery']=brief(found)
  extra_phase=json.loads((batch/'status.json').read_text()).get('phase') if (batch/'status.json').exists() else 'PREPARING'
  extra_controller=controller_state(batch/'controller_process.json')
  all_rows+=extra
 current_stage=('ADDITIONAL_INFRA_RECOVERY_'+extra_phase if extra_phase else
                'MAIN_RUN_COMPLETE' if not states['planned'] and not states['running'] else stage.get('state','unknown'))
 return {'updated':datetime.now(IST).strftime('%d %b %H:%M:%S IST'),'held':(CAMPAIGN/'results/STOP_REQUESTED').exists(),
  'controller':extra_controller or controller_state(),'stage':current_stage,'verification':verification,
  'terminal':138-states['planned']-states['running'],'pending':states['planned'],'running':states['running']+sum(r['status']=='running' for r in extra),
  'requests':sum(r['requests'] for r in all_rows),'known_input':sum(r['input_actual'] for r in all_rows),
  'known_output':sum(r['output_actual'] for r in all_rows),'groups':groups,
  'last_event':data['last_event']['kind'] if data['last_event'] else None}

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_GET(self):
  try:
   if self.path in {'/','/index.html'}:
    body=Path(__file__).with_name('status.html').read_bytes();kind='text/html; charset=utf-8'
   elif self.path=='/status.json': body=json.dumps(status(),ensure_ascii=False).encode();kind='application/json; charset=utf-8'
   else: self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
   self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
  except (OSError,ValueError,sqlite3.Error): self.send_error(503,'Read temporarily unavailable')

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=0);args=parser.parse_args()
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
 atomic_json(CAMPAIGN/'results/browser_monitor.json',{'url':'http://127.0.0.1:'+str(server.server_port)+'/',
  'pid':__import__('os').getpid(),'read_only':True,'started_utc':datetime.now(timezone.utc).isoformat()})
 server.serve_forever()
