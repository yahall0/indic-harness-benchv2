"""Compact read-only view sized for a normal 80-column terminal."""
import json,sys
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from nextbench.monitor import snapshot,label,read_database
CAMPAIGN=Path(__file__).resolve().parents[2]
data=snapshot(CAMPAIGN);states=Counter(r['status'] for r in data['primary'])
_,registry,_,_=read_database(CAMPAIGN/'results/journal.sqlite3')
print('NEMOTRON 3 SUPER | read-only progress and scores')
print('46 report tasks / 138 primaries; one eligible infrastructure recovery')
print(f"Terminal {138-states['planned']-states['running']}/138 | pending {states['planned']} | running {states['running']}")
print(f"Recovery slots {len(registry)} | started {len(data['recovery'])}")
all_rows=data['primary']+list(data['recovery'].values())
if (CAMPAIGN/'results/STOP_REQUESTED').exists():
 print('HELD: no benchmark attempt is running; rows below are saved results.')
 status_path=CAMPAIGN/'results/repair_status.json'
 if status_path.exists():
  repair=json.loads(status_path.read_text(encoding='utf-8'))
  if repair.get('final_candidate_live_verified') is False:
   print('Final timeout fix: local tests passed; live validation pending.')
finished=[r['finished'] for r in all_rows if r.get('finished')]
if finished:
 last=datetime.fromtimestamp(max(finished),timezone(timedelta(hours=5,minutes=30)))
 print('Last saved benchmark result: '+last.strftime('%d %b %H:%M:%S IST'))
print('Benchmark known input/output: '+str(sum(r['input_actual'] for r in all_rows))+'/'+str(sum(r['output_actual'] for r in all_rows)))
print('Benchmark conservative charge: '+str(sum(r['input_bound'] for r in all_rows))+'/'+str(sum(r['output_reserved'] for r in all_rows)))
groups={}
for row in data['primary']: groups.setdefault(row['task'],{})[row['language']]=row
tasks=list(groups);active=[i for i,t in enumerate(tasks) if any(r['status']!='planned' for r in groups[t].values())]
end=min(len(tasks),max(active,default=0)+3);shown=tasks[max(0,end-5):end]
print('')
print(f"{'Task':26} {'English':15} {'Hindi':15} Hinglish")
scheduled={r['primary_run_id'] for r in registry}
for task in shown:
 cells=[]
 for language in ('en','hi','hinglish'):
  row=groups[task][language];retry=data['recovery'].get(row['id'])
  if retry: cell=('INFRA' if retry['status']=='infrastructure_failed' else label(retry))+' [R]'
  elif row['id'] in scheduled: cell='retry queued'
  else: cell='INFRA' if row['status']=='infrastructure_failed' else label(row)
  cells.append(cell)
 print(f'{task[:26]:26} {cells[0]:15} {cells[1]:15} {cells[2]}')
print('')
print('INFRA is not a language score; [R] is the separate recovery.')
print('All primary and recovery records stay saved. Ctrl+C closes this view.')
if data['last_event']: print('Last event: '+data['last_event']['kind'])
