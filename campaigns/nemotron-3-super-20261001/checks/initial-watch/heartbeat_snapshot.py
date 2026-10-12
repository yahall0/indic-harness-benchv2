"""Read-only campaign health audit; writes only observational state files."""
import importlib.util,json,sqlite3,sys,time
from collections import Counter,defaultdict
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import atomic_json
CAMPAIGN=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('readonly_display',Path(__file__).with_name('status_server.py'))
display=importlib.util.module_from_spec(spec);spec.loader.exec_module(display)

def connect(path):
 db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
 db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
 return db

def audit():
 state=json.loads((CAMPAIGN/'results/away_monitor_state.json').read_text())
 known=set(state.get('already_reported_infra_ids',[]));runs=[];faults=[];pending=[];leaks=[]
 paths=[CAMPAIGN/'results/journal.sqlite3']+sorted((CAMPAIGN/'results/recoveries').glob('*/attempt-2/journal.sqlite3'))
 physical=0;known_input=0;known_output=0;charged_input=0;charged_output=0;pause_events=[]
 for path in paths:
  with closing(connect(path)) as db:
   physical+=db.execute('SELECT COUNT(*) FROM forwards').fetchone()[0]
   for raw in db.execute('SELECT * FROM runs ORDER BY rowid'):
    r=dict(raw);v=json.loads(r['result'] or '{}');known_input+=r['input_actual'];known_output+=r['output_actual']
    charged_input+=r['input_bound'];charged_output+=r['output_reserved']
    item={k:r[k] for k in ('id','task','language','status','requests','usage_missing')}
    item.update(score=v.get('oracle',{}).get('outcome_score') if r['status']!='infrastructure_failed' else None,
     pause_reason=v.get('pause_reason'),error_type=v.get('error_type'),integrity=v.get('integrity',[]),
     cleanup_incomplete=v.get('cleanup_incomplete',False),runtime=v.get('runtime_freeze_hash'),
     running_sec=round(time.time()-r['started']) if r['status']=='running' else None,recovery=path!=paths[0])
    runs.append(item)
    if r['id'] not in known and (r['status'] in ('infrastructure_failed','interrupted','quota_paused','integrity_failed')
      or v.get('integrity') or v.get('error_type') or v.get('cleanup_incomplete') or r['usage_missing']):faults.append(item)
   pending.extend(dict(r) for r in db.execute("SELECT c.id,c.run_id,c.status,c.reserved_at,r.status as run_status FROM calls c JOIN runs r ON c.run_id=r.id WHERE c.status!='settled'"))
   leaks.extend(dict(r) for r in db.execute("SELECT s.kind,s.run_id,s.status,r.status as run_status FROM resources s JOIN runs r ON s.run_id=r.id WHERE s.status!='removed' AND r.status!='running'"))
   for r in db.execute("SELECT kind,at,payload FROM events WHERE kind LIKE '%pause%' ORDER BY seq DESC LIMIT 3"):
    pause_events.append({'kind':r['kind'],'at':r['at'],'payload':json.loads(r['payload'])})
   if path==paths[0]:slots=[dict(r) for r in db.execute('SELECT id,state,reason FROM slots')]
 primary=[r for r in runs if not r['recovery']];groups=defaultdict(list)
 for r in primary:groups[r['task']].append(r)
 retry_by_task={(r['task'],r['language']):r for r in runs if r['recovery']}
 resolved=sum(len(g)==3 and all(r['status'] not in ('planned','running') and
  ((r['task'],r['language']) not in retry_by_task or retry_by_task[(r['task'],r['language'])]['status'] not in ('planned','running')) for r in g) for g in groups.values())
 probes=[]
 for name in ('hindi-hinglish','hindi-hinglish-final'):
  path=CAMPAIGN/'revisions/transport-v2/probes'/name/'journal.sqlite3'
  with closing(connect(path)) as db:
   probes.append({'name':name,'run':dict(db.execute('SELECT status,requests,input_actual,output_actual,usage_missing FROM runs').fetchone()),
    'unsettled_calls':db.execute("SELECT COUNT(*) FROM calls WHERE status!='settled'").fetchone()[0],
    'unremoved_resources':db.execute("SELECT COUNT(*) FROM resources WHERE status!='removed'").fetchone()[0]})
 sample=json.loads(Path(__file__).with_name('latest.json').read_text())
 checkpoint=CAMPAIGN/'results/checkpoints/latest/journal-backup.sqlite3'
 report={'observed_utc':datetime.now(timezone.utc).isoformat(),'controller':display.controller_state(),
  'held':(CAMPAIGN/'results/STOP_REQUESTED').exists(),'primary_statuses':dict(Counter(r['status'] for r in primary)),
  'resolved_task_groups':resolved,'next_progress_milestone':state.get('next_progress_milestone_task_groups',10),
  'active':[r for r in runs if r['status']=='running'],'new_faults':faults,
  'terminal_pending_calls':[r for r in pending if r['run_status']!='running'],'active_pending_calls':pending,
  'terminal_resource_leaks':leaks,'slots':slots,'probe_status':probes,
  'pause_events':sorted(pause_events,key=lambda e:e['at'],reverse=True)[:3],
  'recent_terminal':[r for r in primary if r['status'] not in ('planned','running')][-6:],
  'physical_transmissions':physical,'known_input_tokens':known_input,'known_output_tokens':known_output,
  'charged_input':charged_input,'charged_output':charged_output,'baseline_records_unchanged':sample['baseline_records_unchanged'],
  'checkpoint_exists':checkpoint.is_file(),'checkpoint_modified_utc':datetime.fromtimestamp(checkpoint.stat().st_mtime,timezone.utc).isoformat() if checkpoint.is_file() else None}
 atomic_json(CAMPAIGN/'results/away-monitor-observations'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),report)
 atomic_json(CAMPAIGN/'results/away-monitor-latest.json',report)
 return report

if __name__=='__main__':print(json.dumps(audit()))
