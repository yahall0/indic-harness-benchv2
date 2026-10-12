"""Record the held outcome and preserve the locally verified repair candidate."""
import hashlib,json,sys
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import Journal,atomic_json
from bench.lease import ControllerLease
from nextbench_repair.verify import sources
CAMPAIGN=Path(__file__).resolve().parents[2];REV=CAMPAIGN/'revisions/transport-v2'
with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(CAMPAIGN/'results/controller.lock'):
 if not (CAMPAIGN/'results/STOP_REQUESTED').exists(): raise ValueError('Do not record held status unless admission is actually held')
 transport=REV/'config/transport.json'
 old=REV/'probes/hindi-hinglish/config-at-live-check/transport.json'
 if not old.exists(): old.parent.mkdir(parents=True,exist_ok=True);old.write_bytes(transport.read_bytes())
 config=json.loads(transport.read_text());config.update(openclaw_provider_timeout_sec=210,
  original_whole_attempt_deadline_preserved=True,live_gate_failed_before_openclaw_idle_fix=True,
  final_candidate_live_verified=False,no_additional_cloud_requests_this_turn=True,
  openclaw_timeout_source='https://docs.openclaw.ai/agent-loop')
 atomic_json(transport,config)
 for name,digest in sources().items():
  p=REV/'candidate-source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()!=digest: raise ValueError('Never overwrite a different candidate snapshot')
  if not p.exists(): p.write_bytes((ROOT/name).read_bytes())
 value={'state':'HELD_AFTER_FAILED_LIVE_GATE','recorded_utc':datetime.now(timezone.utc).isoformat(),
  'benchmark_resumed':False,'new_benchmark_attempts_during_repair':0,'final_candidate_live_verified':False,
  'local_checks_passed':True,'repair_unit_tests':11,'simulated_130_second_response_passed':True,
  'live_gate_physical_transmissions':2,'live_gate_known_input_tokens':6029,'live_gate_known_output_tokens':74,
  'live_gate_unknown_usage_calls':1,'full_unknown_reservation_retained':True,
  'intrinsic_hindi_or_hinglish_incompatibility_established':False,
  'next_admission_requires_successful_current_candidate_live_verification':True,
  'baseline_and_old_terminal_attempts_unchanged':True,'repair_sources':sources()}
 atomic_json(CAMPAIGN/'results/repair_status.json',value)
 with closing(Journal(CAMPAIGN/'results/journal.sqlite3')) as journal:
  journal.event(None,'campaign_held_after_repair_verification',{
   'reason':'Failed live gate; stopped extra usage. Later provider-timeout fix passed locally but remains unverified live.',
   'new_benchmark_attempts':0,'benchmark_resume_authorized_but_safety_gate_failed':True})
 print(json.dumps({k:v for k,v in value.items() if k!='repair_sources'}))
