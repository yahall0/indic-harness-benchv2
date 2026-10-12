"""Verify the authorized extra attempts and export a transparent same-campaign view."""
import csv
import importlib.util
import json
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('additional_recovery',HERE/'additional_recovery.py')
extra=importlib.util.module_from_spec(spec);spec.loader.exec_module(extra)
from bench.durable import atomic_json
from bench.metrics import attempt_metrics,compare,AGENT_OUTCOMES
from nextbench.analysis import paired_baseline

def main():
    batch=extra.BATCH;campaign=extra.CAMPAIGN
    status=json.loads((batch/'status.json').read_text())
    if status['phase']!='FINISHED':raise ValueError('Additional controller has not finished')
    with closing(extra.readonly(batch/'journal.sqlite3')) as db:
        runs=[dict(r) for r in db.execute('SELECT * FROM runs')]
        if any(r['status'] not in AGENT_OUTCOMES for r in runs):raise ValueError('An additional condition remains INFRA or pending')
        if db.execute("SELECT COUNT(*) FROM calls WHERE status!='settled'").fetchone()[0]:raise ValueError('Unsettled additional accounting')
        if db.execute("SELECT COUNT(*) FROM resources WHERE status!='removed'").fetchone()[0]:raise ValueError('Additional resource remains')
        for r in runs:
            v=json.loads(r['result']);
            if r['usage_missing'] or v.get('integrity') or v.get('cleanup_incomplete') or v.get('error_type'):
                raise ValueError('Additional attempt needs integrity/accounting inspection')
    if not extra.preserved():raise ValueError('Original campaign/baseline changed')
    categories={r['task_id']:r['category'] for r in json.loads((extra.ROOT/'dataset/task_manifest.json').read_text())}
    all_metrics=[];primary={};selected={}
    for index,path in enumerate(extra.original_paths()[1:]+[batch/'journal.sqlite3']):
        with closing(extra.readonly(path)) as db:
            for r in db.execute('SELECT * FROM runs ORDER BY rowid'):
                row=dict(r);metric=attempt_metrics(SimpleNamespace(db=db),row,categories[row['task']])
                metric['attempt_number']=1 if index==0 else 3 if path==batch/'journal.sqlite3' else 2
                key=(row['task'],row['language'])
                if index==0:
                    primary[key]=row['id'];selected[key]=metric
                metric['primary_run_id']=primary[key]
                all_metrics.append(metric)
                if index!=0 and row['status'] in AGENT_OUTCOMES:selected[key]=metric
    rows=list(selected.values())
    assert len(rows)==138 and len({r['task_id'] for r in rows})==46
    analysis=compare([{**r,'agent_outcome':r['agent_outcome'] and r['score_available_for_analysis']} for r in rows])
    with (extra.ROOT/'pdf/report_data/included_condition_metrics.csv').open(encoding='utf-8-sig',newline='') as stream:
        baseline=list(csv.DictReader(stream))
    comparison=paired_baseline(rows,baseline)
    policy='Same 46 tasks/138 conditions. One additional explicitly user-authorized recovery for each of two unresolved INFRA conditions after the original recovery policy. Latest scored recovery selected regardless of score; all attempts/costs preserved. Extra attempt policy differs from baseline and original preregistration.'
    analysis.update(view='user_requested_resolved',attempt_selection=policy,planned_tasks=46,planned_conditions=138)
    comparison.update(future_analysis_view='user_requested_resolved',attempt_policy_difference=True,attempt_selection=policy)
    destination=campaign/'results/exports'
    atomic_json(destination/'user_requested_resolved_metrics.json',rows)
    atomic_json(destination/'all_attempt_metrics_including_additional_recoveries.json',all_metrics)
    atomic_json(destination/'user_requested_resolved_analysis.json',analysis)
    atomic_json(destination/'user_requested_resolved_analysis_vs_baseline.json',comparison)
    report=dict(passed=True,verified_utc=datetime.now(timezone.utc).isoformat(),scored_conditions=len(rows),
        matched_task_triplets=comparison['paired_task_triplets'],all_original_tables_and_artifacts_preserved=True,
        all_additional_calls_settled=True,all_additional_resources_removed=True,new_unknown_usage_calls=0,
        additional_attempts=status['attempts'],combined_accounting=status['combined_accounting'],
        policy_deviation_disclosed=True,original_primary_and_recovery_views_preserved=True)
    atomic_json(batch/'verification.json',report)
    print(json.dumps(report))

if __name__=='__main__':main()
