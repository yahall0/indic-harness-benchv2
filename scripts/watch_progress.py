"""Read-only live scoreboard; never imports the controller or makes model calls."""
import argparse,ctypes,json,math,os,sqlite3,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LANGS=('en','hi','hinglish')
TERMINAL={'completed','agent_failed','timeout','budget_exhausted','integrity_failed','infrastructure_failed','interrupted','quota_paused'}

def alive(pid):
    if os.name!='nt': return None
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.OpenProcess.argtypes=(ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32)
    kernel.GetExitCodeProcess.argtypes=(ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32))
    kernel.CloseHandle.argtypes=(ctypes.c_void_p,)
    handle=kernel.OpenProcess(0x1000,False,int(pid))
    if not handle: return False
    try:
        code=ctypes.c_uint32()
        return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
    finally: kernel.CloseHandle(handle)

def snapshot():
    info={}
    process=ROOT/'results/controller_process.json'
    if process.exists():
        info=json.loads(process.read_text(encoding='utf-8-sig'))
    data={'controller_alive':alive(info['pid']) if info.get('pid') else None,'process':info,'runs':[],'slots':[],'events':[],'campaign':None,'recovery':None}
    path=ROOT/'results/journal.sqlite3'
    if not path.exists(): return data
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2)
    db.row_factory=sqlite3.Row
    try:
        db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
        data['runs']=[dict(r) for r in db.execute('SELECT * FROM runs ORDER BY rowid')]
        data['slots']=[dict(r) for r in db.execute('SELECT id,state FROM slots ORDER BY id')]
        data['events']=[dict(r) for r in db.execute('SELECT seq,at,kind FROM events ORDER BY seq DESC LIMIT 5')]
        policy=db.execute("SELECT kind,payload FROM events WHERE kind IN ('campaign_session_started','campaign_continuing','campaign_paused') ORDER BY seq DESC LIMIT 1").fetchone()
        if policy: data['campaign']={'kind':policy['kind'],**json.loads(policy['payload'])}
    finally: db.close()
    recovery=ROOT/'results/infrastructure_retries.json'
    if recovery.exists():
        record=json.loads(recovery.read_text(encoding='utf-8'))
        retry_path=Path(record['journal'])
        if retry_path.is_file():
            retry_db=sqlite3.connect(retry_path.as_uri()+'?mode=ro',uri=True,timeout=2)
            retry_db.row_factory=sqlite3.Row
            try:
                row=retry_db.execute('SELECT * FROM runs WHERE id=?',(record['retry_run_id'],)).fetchone()
                if row:data['recovery']={'record':record,'run':dict(row),'slots':[dict(s) for s in retry_db.execute('SELECT id,state FROM slots ORDER BY id')]}
            finally:retry_db.close()
    return data

def outcome(row):
    if not row: return '-'
    state=row['status']
    if state=='planned': return 'pending'
    if state=='running': return 'RUN '+str(int(time.time()-(row['started'] or time.time())))+'s'
    result=json.loads(row['result']) if row.get('result') else {}
    oracle=result.get('oracle',{});score=oracle.get('outcome_score')
    valid=isinstance(score,(int,float)) and math.isfinite(score)
    full=state=='completed' and valid and score>=.9999 and all(c.get('pass') for c in oracle.get('checks',[])) and not result.get('integrity')
    label='PASS' if full else {'completed':'partial','agent_failed':'agentfail','timeout':'timeout','budget_exhausted':'budget','integrity_failed':'integrity','infrastructure_failed':'INFRA','interrupted':'interrupt','quota_paused':'QUOTA'}.get(state,'unknown')
    return (format(score,'.2f')+' ' if valid and state in {'completed','agent_failed','timeout','budget_exhausted','integrity_failed'} else '')+label

def render(data):
    rows=data['runs'];all_rows=rows
    limits=json.loads((ROOT/'config/protocol.json').read_text(encoding='utf-8'))
    total=limits['planned_runs']
    selection=ROOT/'dataset/extension_selection.json'
    added=[]
    if selection.exists():
        added=json.loads(selection.read_text(encoding='utf-8'))['selected_task_ids']
        rows=[r for r in all_rows if r['task'] in added]
        total=len(added)*3
    states=Counter(r['status'] for r in rows)
    recovery=data.get('recovery')
    recovering=recovery and recovery['run']['status'] in ('planned','running')
    print('INDIC HARNESS BENCH - live scores (refresh every 5 seconds)')
    print(time.strftime('%Y-%m-%d %H:%M:%S')+' | controller: '+('RUNNING' if data['controller_alive'] else 'STOPPED' if data['controller_alive'] is False else 'starting/unknown'))
    if added:
        previous=[r for r in all_rows if r['task'] not in added]
        print('NEW TASKS ONLY: '+str(len(added))+' tasks / '+str(total)+' attempts | earlier '+str(len(previous))+' saved attempts are skipped')
    print('Finished: '+str(sum(states[s] for s in TERMINAL))+'/'+str(total)+' | running: '+str(states['running']+int(bool(recovering)))+' | pending: '+str(states['planned'])+' | not yet planned: '+str(max(0,total-len(rows))))
    print('Requests: '+str(sum(r['requests'] for r in rows))+' | known tokens in/out: '+str(sum(r['input_actual'] for r in rows))+'/'+str(sum(r['output_actual'] for r in rows)))
    slots=recovery['slots'] if recovering else data['slots']
    print('Keys: '+(' | '.join(s['id']+'='+s['state'] for s in slots) or 'initializing'))
    if recovery:
        row=recovery['run']
        print('AUTHORIZED INFRA RECOVERY: '+row['task']+' / '+row['language']+' / '+outcome(row)+' / requests='+str(row['requests'])+' (original INFRA retained)')
    print('Provider failure: save attempt, wait 30s, continue; pause after 3 consecutive failures or a critical gate.')
    policy=data.get('campaign')
    if policy and policy['kind']=='campaign_paused' and not recovering: print('CAMPAIGN PAUSED: '+policy.get('reason','unknown'))
    elif policy and policy.get('provider_failure'): print('Latest provider failure: '+policy['reason']+'; continuing after cooldown.')
    print('Per attempt: input '+str(limits['max_input_tokens'])+' | output '+str(limits['max_output_tokens'])+' | requests '+str(limits['max_requests'])+' | timeout <= '+str(limits['attempt_timeout_sec'])+'s')
    for row in rows:
        if row['status']=='running': print('ACTIVE: '+row['task']+' / '+row['language']+' / '+outcome(row)+' / requests='+str(row['requests']))
    print('')
    print(format('Task','31')+format('English','17')+format('Hindi','17')+'Hinglish')
    grouped={task:{} for task in added}
    for row in rows: grouped.setdefault(row['task'],{})[row['language']]=row
    for task,versions in grouped.items():
        print(format(task[:29],'31')+format(outcome(versions.get('en')),'17')+format(outcome(versions.get('hi')),'17')+outcome(versions.get('hinglish')))
    if not rows: print('Waiting for readiness checks and plan creation...')
    print('')
    print('Score range 0-1; PASS requires all oracle checks and no integrity violation.')
    print('Latest events: '+', '.join(time.strftime('%H:%M:%S',time.localtime(e['at']))+' '+e['kind'] for e in reversed(data['events'])))
    if data['controller_alive'] is False and states['planned']:
        print('CONTROLLER STOPPED with pending runs. Inspect saved outcome/logs before resuming.')
    print('Saved metrics: '+str(ROOT/'results/exports/metrics.csv'))
    print('Ctrl+C closes this monitor only; the benchmark continues.')
    print('Emergency stop: use scripts/emergency_stop.py (instructions in outputs/MONITORING.md).')

def configure_console():
    # Classic Windows console selection can suspend writes; disable Quick Edit.
    if os.name!='nt': return
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetStdHandle.argtypes=(ctypes.c_int,);kernel.GetStdHandle.restype=ctypes.c_void_p
    kernel.GetConsoleMode.argtypes=(ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32))
    kernel.SetConsoleMode.argtypes=(ctypes.c_void_p,ctypes.c_uint32)
    handle=kernel.GetStdHandle(-10);mode=ctypes.c_uint32()
    if kernel.GetConsoleMode(handle,ctypes.byref(mode)):
        kernel.SetConsoleMode(handle,(mode.value|0x0080)&~0x0040)

def main():
    configure_console()
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    while True:
        try:
            data=snapshot()
            if not args.once and os.name=='nt': os.system('cls')
            render(data)
        except (OSError,ValueError,sqlite3.Error) as exc:
            print('Monitor read temporarily unavailable: '+type(exc).__name__)
        if args.once: return
        time.sleep(5)

if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: print('Monitor closed; controller is independent.')
