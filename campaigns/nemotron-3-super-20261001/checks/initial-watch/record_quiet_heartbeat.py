"""Record a healthy observation without advancing any notification milestone."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import atomic_json
CAMPAIGN=Path(__file__).resolve().parents[2]
report=json.loads((CAMPAIGN/'results/away-monitor-latest.json').read_text())
state_path=CAMPAIGN/'results/away_monitor_state.json';state=json.loads(state_path.read_text())
if (report['controller']!='running' or report['held'] or report['new_faults'] or
 report['terminal_pending_calls'] or report['terminal_resource_leaks'] or not report['baseline_records_unchanged'] or
 not report['checkpoint_exists'] or report['resolved_task_groups']>=report['next_progress_milestone'] or
 any(p['unsettled_calls'] or p['unremoved_resources'] for p in report['probe_status'])):
 raise ValueError('Observation needs review or notification; do not record as quiet')
budget_ids=set(state.get('observed_budget_outcome_ids',[]))
budget_ids.update(r['id'] for r in report['recent_terminal'] if r['status']=='budget_exhausted')
state.update(updated_utc=datetime.now(timezone.utc).isoformat(),last_checked_utc=report['observed_utc'],
 last_observed_primary_statuses=report['primary_statuses'],last_observed_physical_transmissions=report['physical_transmissions'],
 last_observed_resolved_task_groups=report['resolved_task_groups'],last_check_controller=report['controller'],
 last_check_admissions_held=report['held'],last_check_new_infrastructure_failures=[],last_check_new_unknown_usage_calls=0,
 last_check_terminal_resource_leaks=0,last_check_terminal_pending_calls=0,
 last_check_baseline_records_unchanged=True,last_check_checkpoint_exists=True,
 last_check_action='none; healthy progress below next milestone; scored budget outcomes remain included',
 last_active_attempts=report['active'],observed_budget_outcome_ids=sorted(budget_ids))
atomic_json(state_path,state)
print(json.dumps({'saved':True,'controller':report['controller'],'resolved_groups':report['resolved_task_groups'],
 'new_faults':report['new_faults'],'notify':False}))
