"""Exercise the live controller with simulated inference; never run a study condition."""
import json,uuid
from pathlib import Path
import bench.controller as controller
from bench.runtime_check import mock_transport_code
from bench.durable import Journal,atomic_json

ROOT=Path(__file__).resolve().parents[1]

def check_controller():
    ident=uuid.uuid4().hex[:12]; dest=ROOT/'work/controller-check'/ident
    j=Journal(dest/'journal.sqlite3'); j.plan(['001-file'],ident); row=j.runs()[0]
    original=controller.docker
    code=mock_transport_code("python -c \"from pathlib import Path; Path('/workspace/out/linecount.txt').write_text('4')\"")
    code=code.replace("m.get('role')=='user' and any(marker in str(m.get('content','')) for marker in ('ROUND_ONE','ROUND_TWO'))", "m.get('role')=='user' and isinstance(m.get('content'),str)")
    code=code.replace("if 'ROUND_ONE' in prompt else",'if True else')
    relay_id=json.loads((ROOT/'config/images.json').read_text())['relay']['id']
    simulated_failure={'next':False}
    def simulated_docker(args,**kwargs):
        if args[0]=='create' and relay_id in args and args[-1]==relay_id:
            transport=code
            if simulated_failure['next']:
                simulated_failure['next']=False
                marker="  data=json.loads(request.data); messages=data['messages']; tools=data.get('tools',[])"
                assert marker in transport
                transport=transport.replace(marker,"  raise urllib.error.URLError('Synthetic upstream timeout; no cloud request')")
            args=[*args,'python','-c',transport]
        return original(args,**kwargs)
    controller.docker=simulated_docker
    try:
        status,slot=controller.attempt(j,row,{'slot-1':'FAKE_CONTROLLER_KEY'},destination_root=dest/'runs')
        saved=j.get(row['id']); result=json.loads(saved['result'])
        checks={'controller_completed':status=='completed','original_score_one':result.get('oracle',{}).get('outcome_score')==1,
                'no_integrity_violations':not result.get('integrity'),'results_saved':(dest/'runs'/row['id']/'run.json').is_file(),
                'artifacts_saved':(dest/'runs'/row['id']/'artifacts/out/linecount.txt').read_text()=='4','request_accounting':saved['requests']==2,
                'traces_saved':len(list((dest/'runs'/row['id']/'inference').glob('*.json')))==2,
                'owned_resources_removed':not j.resources()}
        j.close(); j=Journal(dest/'journal.sqlite3'); j.recover()
        checks['completed_result_survives_reopen']=j.get(row['id'])['status']=='completed'
        try: j.start(row['id']); checks['automatic_rerun_blocked']=False
        except ValueError: checks['automatic_rerun_blocked']=True
        preserved=j.get(row['id']); simulated_failure['next']=True; cooldown=[]
        controller._run_pending(j,{'slot-1':'FAKE_CONTROLLER_KEY'},'slot-1',sleep=cooldown.append,
                                checkpoint=dest/'campaign-checkpoint',destination_root=dest/'runs')
        remaining=j.runs()[1:]
        failed_call=j.db.execute('SELECT * FROM calls WHERE run_id=?',(remaining[0]['id'],)).fetchone()
        checks.update(provider_timeout_saved=remaining[0]['status']=='infrastructure_failed',
                      next_condition_completed=remaining[1]['status']=='completed',
                      next_condition_original_score_one=json.loads(remaining[1]['result']).get('oracle',{}).get('outcome_score')==1,
                      cooldown_applied=cooldown==[30],
                      prior_completed_result_unchanged=j.get(row['id'])==preserved,
                      ambiguous_usage_reserved=failed_call is not None and failed_call['status']=='settled' and remaining[0]['output_reserved']==4096,
                      campaign_resources_removed=not j.resources(),
                      no_speculative_key_rotation=all(r['slot']=='slot-1' for r in j.db.execute('SELECT slot FROM forwards')),
                      every_attempt_saved=all((dest/'runs'/r['id']/'run.json').is_file() for r in j.runs()))
        report={'passed':all(checks.values()),'checks':checks,'cloud_requests':0,'benchmark_runs':0,'evidence_directory':str(dest)}
    finally: controller.docker=original; j.close()
    from bench.fingerprint import runtime_fingerprint
    report['runtime_fingerprint']=runtime_fingerprint()
    atomic_json(ROOT/'reports/controller_check.json',report); print(json.dumps(report)); return report

if __name__=='__main__': raise SystemExit(0 if check_controller()['passed'] else 1)
