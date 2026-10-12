import json,uuid
from pathlib import Path
from bench.containers import Containers
from bench.task_services import start_mock
from bench.security import docker,bounded_docker
from bench.durable import atomic_json

ROOT=Path(__file__).resolve().parents[1]
CLIENT=r'''import json,urllib.request,urllib.error
out={}; errors={}
for endpoint in ('projects','users','incidents'):
 page=1; items=[]; codes=[]
 while page:
  url='http://127.0.0.1:8081/'+endpoint+'?page='+str(page)
  try: r=urllib.request.urlopen(url,timeout=3)
  except urllib.error.HTTPError as e:
   codes.append(e.code); r=urllib.request.urlopen(url,timeout=3)
  with r: data=json.load(r)
  items.extend(data['items']); page=data['next_page']
 out[endpoint]=items; errors[endpoint]=codes
print(json.dumps({'items':out,'transient_statuses':errors}))
'''

def check_helpers():
    results=[]; images=None
    for _ in range(2):
        box=Containers(); images=box.images
        try:
            net=box.internal(); vol=box.workspace(); agent=box.create('agent',network=net,volume=vol)
            prepared,state=box.prepared('022-local-rest-api-summary'); box.import_archive(agent,prepared)
            mock=start_mock(box,agent,net,vol)
            data=json.loads(docker(['exec',agent,'python','-c',CLIENT],timeout=20))
            expected={k:json.loads((ROOT/'vendor/harnessbench/tasks/022-local-rest-api-summary/fixtures/in/api_data'/(k+'.json')).read_text()) for k in ('projects','users','incidents')}
            docker(['kill',agent]); docker(['kill',mock])
            logs=[json.loads(l) for l in bounded_docker(['logs',mock],max_bytes=1048576).splitlines()]
            checks={'all_pages_preserved':data['items']==expected,'transient_statuses_preserved':all(code==(429 if k=='projects' else 503) for k,v in data['transient_statuses'].items() for code in v),
                    'projects_first_request_429':bool(data['transient_statuses']['projects']),
                    'incidents_first_request_503':bool(data['transient_statuses']['incidents']),
                    'users_no_transient_failure':not data['transient_statuses']['users'],
                    'trusted_logs_survive_agent_stop':all(any(l['path']=='/'+k for l in logs) for k in expected)}
            results.append({'passed':all(checks.values()),'checks':checks,'transient_statuses':data['transient_statuses'],'log_records':len(logs)})
        except Exception as e: results.append({'passed':False,'error':str(e)[:2000]})
        finally: box.cleanup()
    report={'passed':all(r['passed'] for r in results),'trials':results,'fresh_state_each_trial':True,'images':images,'cloud_requests':0,'benchmark_runs':0}
    from bench.fingerprint import runtime_fingerprint
    report['runtime_fingerprint']=runtime_fingerprint()
    atomic_json(ROOT/'reports/helper_check.json',report); print(json.dumps(report)); return report

if __name__=='__main__': raise SystemExit(0 if check_helpers()['passed'] else 1)
