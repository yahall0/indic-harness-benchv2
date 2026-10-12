"""Append restart-phase history outside all frozen evaluation inputs."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import atomic_json
from nextbench_repair.verify import sources
CAMPAIGN=Path(__file__).resolve().parents[2];path=CAMPAIGN/'results/repair_status.json'
phase=sys.argv[1]
if phase not in {'FINAL_LIVE_VALIDATION','FINAL_GATE_FAILED','VALIDATED_READY','RUNNING_TRANSPORT_V2','INITIAL_WATCH_COMPLETE','PAUSED_AFTER_RESTART'}: raise ValueError('Unknown restart phase')
now=datetime.now(timezone.utc);old=json.loads(path.read_text())
atomic_json(CAMPAIGN/'results/repair-history'/(now.strftime('%Y%m%dT%H%M%S%f')+'.json'),old)
old.update(state=phase,recorded_utc=now.isoformat(),repair_sources=sources(),repair_unit_tests=13,
 final_candidate_live_verified=phase in {'VALIDATED_READY','RUNNING_TRANSPORT_V2','INITIAL_WATCH_COMPLETE','PAUSED_AFTER_RESTART'},
 benchmark_resumed=phase in {'RUNNING_TRANSPORT_V2','INITIAL_WATCH_COMPLETE','PAUSED_AFTER_RESTART'},
 latest_user_instruction='Monitor while away, check stale terminal, and get things working after timeout repair.',
 away_monitor_automation='watch-nemotron-benchmark',stop_if_final_language_gate_fails=True)
gate=CAMPAIGN/'revisions/transport-v2/probes/hindi-hinglish-final/report.json'
if gate.exists():
 report=json.loads(gate.read_text())
 old.update(live_gate_name='hindi-hinglish-final',live_gate_physical_transmissions=report['physical_transmissions'],
  live_gate_known_input_tokens=report['known_input_tokens'],live_gate_known_output_tokens=report['known_output_tokens'],
  live_gate_unknown_usage_calls=report['usage_missing_calls'],live_gate_passed=report['passed'],
  next_admission_requires_successful_current_candidate_live_verification=not report['passed'])
atomic_json(path,old);print(json.dumps({'phase':phase,'final_candidate_live_verified':old['final_candidate_live_verified']}))
