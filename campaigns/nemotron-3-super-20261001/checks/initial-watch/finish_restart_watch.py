"""Save read-only evidence for the first three task groups after repair."""
import json, sqlite3, sys
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import atomic_json

CAMPAIGN=Path(__file__).resolve().parents[2]
freeze=json.loads((CAMPAIGN/'revisions/transport-v2/config/freeze.json').read_text())
sample=json.loads(Path(__file__).with_name('latest.json').read_text())
if not sample['first_three_triplets_resolved'] or not sample['baseline_records_unchanged']:
 raise ValueError('Initial triplets are not resolved or baseline preservation failed')
records=[];failures=[];calls=0;known_input=0;known_output=0
journals=[CAMPAIGN/'results/journal.sqlite3']
journals+=sorted((CAMPAIGN/'results/recoveries').glob('*/attempt-2/journal.sqlite3'))
targets={r['task'] for r in sample['first_nine']}
for path in journals:
 with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
  db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
  for raw in db.execute('SELECT * FROM runs ORDER BY rowid'):
   row=dict(raw);result=json.loads(row['result'] or '{}')
   if row['task'] not in targets or result.get('runtime_freeze_hash')!=freeze['runtime_freeze_hash']:continue
   pending=db.execute("SELECT COUNT(*) FROM calls WHERE run_id=? AND status!='settled'",(row['id'],)).fetchone()[0]
   owned=db.execute("SELECT COUNT(*) FROM resources WHERE run_id=? AND status!='removed'",(row['id'],)).fetchone()[0]
   responses=[json.loads(c[0] or '{}') for c in db.execute('SELECT response FROM calls WHERE run_id=?',(row['id'],))]
   forward_count=db.execute('SELECT COUNT(*) FROM forwards WHERE call_id IN (SELECT id FROM calls WHERE run_id=?)',(row['id'],)).fetchone()[0]
   clean=(row['status']=='completed' and row['usage_missing']==0 and pending==0 and owned==0
    and not result.get('integrity') and not result.get('cleanup_incomplete') and not result.get('pause_reason')
    and all(c.get('classification')=='success' and c.get('status')==200 for c in responses))
   if not clean:failures.append(row['id'])
   calls+=forward_count;known_input+=row['input_actual'];known_output+=row['output_actual']
   records.append({'id':row['id'],'task':row['task'],'language':row['language'],
    'attempt_number':1 if path==journals[0] else 2,'status':row['status'],'score':result['oracle']['outcome_score'],
    'usage_missing':row['usage_missing'],'physical_transmissions':forward_count,
    'all_calls_settled':pending==0,'all_owned_resources_removed':owned==0,
    'failed_oracle_checks':[c['id'] for c in result['oracle'].get('checks',[]) if not c['pass']],
    'integrity':result.get('integrity',[])})
report={'passed':len(records)==7 and not failures,'observed_utc':datetime.now(timezone.utc).isoformat(),
 'study_id':freeze['original_study_id'],'runtime_freeze_hash':freeze['runtime_freeze_hash'],
 'first_three_task_groups_resolved':True,'old_first_task_hindi_infra_retained':True,
 'no_third_hindi_attempt':True,'new_repair_attempts_observed':len(records),'new_attempts':records,
 'new_infrastructure_failures':len(failures),'physical_transmissions':calls,
 'known_input_tokens':known_input,'known_output_tokens':known_output,
 'baseline_unchanged':sample['baseline_records_unchanged']}
destination=Path(__file__).with_name('restart-watch-verification.json')
if destination.exists():raise ValueError('Do not overwrite a completed restart-watch report')
atomic_json(destination,report)
if not report['passed']:raise ValueError('Restart watch verification failed')
state_path=CAMPAIGN/'results/away_monitor_state.json'
if state_path.exists():
 atomic_json(CAMPAIGN/'results/away-monitor-history'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),json.loads(state_path.read_text()))
atomic_json(state_path,{'updated_utc':report['observed_utc'],'last_notified_milestone':'first_three_task_groups_resolved',
 'first_three_task_groups_resolved':True,'already_reported_infra_ids':['c9b6eff7b07c35d6d96913e0','14ff66cc3d3e32ab38279030','534b9b4bf978124f64c4c55e'],
 'last_observed_primary_statuses':sample['all_primary_statuses'],
 'last_observed_physical_transmissions':sample['all_attempt_physical_transmissions'],
 'notifications':'meaningful progress, completion, new failure, or required action only',
 'monitor_must_not_start_inference':True})
print(json.dumps(report));sys.exit(0)
