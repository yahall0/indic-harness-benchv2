"""One real fixture/hook/grader integration check with fake upstream inference."""
import hashlib
import json
import uuid
from contextlib import closing
from pathlib import Path

from bench.durable import Journal, atomic_json
from bench.lease import ControllerLease
from nextbench.attempt import attempt

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''import io,json,urllib.request,sys
sys.path.insert(0,'/opt/ihb')
real=urllib.request.build_opener
class Response(io.BytesIO):
 def __init__(self,data): super().__init__(json.dumps(data).encode()); self.status=200; self.headers={}
 def __enter__(self): return self
 def __exit__(self,*args): self.close()
class Fake:
 def __init__(self,opener): self.real=opener
 def open(self,request,*a,**kw):
  if request.full_url!='https://ollama.com/v1/chat/completions': return self.real.open(request,*a,**kw)
  p=json.loads(request.data); assert p['model']=='nemotron-3-super' and p['reasoning_effort']=='high'
  if not any(m['role']=='tool' for m in p['messages']):
   command="python -c \"from pathlib import Path; p=Path('/workspace'); (p/'out').mkdir(exist_ok=True); (p/'out/linecount.txt').write_text(str(len((p/'in/input.txt').read_text().splitlines())))\""
   names=[t['function']['name'] for t in p.get('tools',[])]
   name='exec' if 'exec' in names else 'tool_call'; args={'command':command,'yieldMs':1000}
   if name=='tool_call': args={'name':'exec','arguments':args}
   msg={'role':'assistant','content':None,'reasoning':'Check the fixture using the exec tool.','tool_calls':[{'id':'call_count','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}; finish='tool_calls'
  else: msg={'role':'assistant','content':'Done.'}; finish='stop'
  return Response({'id':'fake-production-check','object':'chat.completion','created':1,'model':p['model'],'choices':[{'index':0,'message':msg,'finish_reason':finish}],'usage':{'prompt_tokens':100,'completion_tokens':30,'total_tokens':130}})
urllib.request.build_opener=lambda *a:Fake(real(*a))
import relay
relay.main()
'''


def check(campaign):
    campaign = Path(campaign).resolve()
    suffix = uuid.uuid4().hex[:12]
    dest = campaign / 'checks/production-attempt' / suffix
    config = lambda name: json.loads((campaign / 'config' / name).read_text())
    images = config('images.json')
    report = {'passed': False, 'actual_cloud_requests': 0, 'benchmark_attempts': 0,
              'fixture': '001-file/en', 'images': images,
              'runtime_sources_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                  for name in ('nextbench/attempt.py','nextbench/runtime/agent.py',
                               'nextbench/runtime/relay.py','nextbench/contract.py',
                               'nextbench/openclaw_config.py','nextbench/containers.py')}}
    with ControllerLease(ROOT / 'results/controller.lock'), ControllerLease(campaign / 'results/controller.lock'), closing(Journal(dest / 'journal.sqlite3')) as journal:
        ident = hashlib.sha256(('fake-production-check:' + suffix).encode()).hexdigest()[:24]
        journal.db.execute('INSERT INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',
                           (ident, '001-file', 'en', 'diagnostic-fake-inference-' + suffix))
        status, _ = attempt(journal, journal.get(ident), {'slot-1':'FAKE_NO_CLOUD_KEY'},
            baseline_root=ROOT, campaign_root=campaign, profile=config('model_profile.json'),
            limits=config('protocol.json'), images=images, runtime_freeze_hash='diagnostic-fake-inference',
            destination_root=campaign / 'results/diagnostics/production-attempt' / suffix,
            checkpoint=campaign / 'results/diagnostics/production-attempt' / suffix / 'checkpoint',
            relay_command=('python','-c',MOCK))
        row = journal.get(ident)
        result = json.loads(row['result'])
        score = result.get('oracle', {}).get('outcome_score')
        checks = {'completed': status == 'completed', 'full_oracle_score': score == 1,
                  'no_integrity_violations': result.get('integrity') == [],
                  'round_hook_checked': journal.db.execute("SELECT COUNT(*) FROM events WHERE run_id=? AND kind='round_hook_checked'", (ident,)).fetchone()[0] == 1,
                  'all_owned_resources_removed': not journal.resources(),
                  'durable_usage_settled': journal.db.execute("SELECT COUNT(*) FROM calls WHERE status!='settled'").fetchone()[0] == 0,
                  'two_physical_fake_transmissions': journal.db.execute('SELECT COUNT(*) FROM forwards').fetchone()[0] == 2,
                  'checkpoint_exists': (campaign / 'results/diagnostics/production-attempt' / suffix / 'checkpoint/journal-backup.sqlite3').is_file()}
        report.update(checks=checks, passed=all(checks.values()), run_id=ident, status=status,
                      diagnostic_journal=str(dest / 'journal.sqlite3'), score=score)
        atomic_json(dest / 'report.json', report)
        atomic_json(campaign / 'checks/production-attempt/report.json', report)
    return report


if __name__ == '__main__':
    import sys
    value = check(sys.argv[1]); print(json.dumps(value))
    raise SystemExit(0 if value['passed'] else 1)
