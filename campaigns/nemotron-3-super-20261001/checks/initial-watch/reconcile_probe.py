"""Append unknown-use settlement after the held probe's containers are retired."""
import json,sys
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import Journal,atomic_json
from bench.lease import ControllerLease
CAMPAIGN=Path(__file__).resolve().parents[2]
DEST=CAMPAIGN/'revisions/transport-v2/probes/hindi-hinglish'
with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(CAMPAIGN/'results/controller.lock'),closing(Journal(DEST/'journal.sqlite3')) as journal:
 if not (CAMPAIGN/'results/STOP_REQUESTED').exists() or journal.resources(): raise ValueError('Reconcile only the held, fully retired probe')
 calls=journal.db.execute("SELECT id FROM calls WHERE status='reserved'").fetchall()
 if calls:
  journal.export(DEST/'checkpoint-before-reconciliation')
  for call in calls:
   journal.settle(call['id'],{'usage':None,'classification':'controller_retired_unsettled_transport','status':0})
  journal.event(None,'probe_accounting_reconciliation',{'unknown_calls':len(calls),'full_reservations_retained':True,'terminal_result_not_overwritten':True})
  journal.export(DEST/'checkpoint-after-reconciliation')
 row=journal.runs()[0]
 value={k:row[k] for k in ('status','requests','input_actual','output_actual','input_bound','output_reserved','usage_missing')}
 value.update(remaining_reserved_calls=journal.db.execute("SELECT count(*) FROM calls WHERE status='reserved'").fetchone()[0],
  original_report_preserved=True,original_terminal_result_preserved=True,new_inference_calls=0)
 atomic_json(DEST/'accounting-reconciliation.json',value);print(json.dumps(value))
