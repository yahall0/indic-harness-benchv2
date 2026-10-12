"""Record finished report and bundle its reusable data; never starts inference."""
import json,os,tomllib,zipfile
from datetime import datetime,timezone
from pathlib import Path
from extension50.common import ROOT,SHARED,read,sha,verify_preserved
from bench.durable import atomic_json

def atomic_bytes(path,value):
    temp=path.with_name(path.name+'.tmp')
    with temp.open('wb') as f:
        f.write(value);f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def finish():
    out=ROOT/'output/pdf';data=out/'report_data'
    ready=read(SHARED/'results/report_ready.json')
    qa=read(data/'final_quality_checks.json')
    assert ready['ready'] and qa['passed'] and not qa['visual_review_pending']
    assert sha(ready['pdf'])==qa['pdf_sha256'] and verify_preserved()
    automation=tomllib.loads(Path('C:/Users/prish/.codex/automations/watch-nemotron-benchmark/automation.toml').read_text())
    assert automation['status']=='PAUSED'
    stamp=datetime.now(timezone.utc).isoformat()
    note='''# Reusable research data - Indic Harness Bench

50 original task clusters; 3 instruction languages and 2 models; 300 selected
scored conditions. Only four new tasks (24 primary attempts) were evaluated.
No earlier task was rerun. Budget stops and genuine low scores remain included.
All 24 additions are scored with no INFRA or recovery and no missing usage.

matched_conditions.csv / .json: selected scored records with run IDs, usage and
provenance. task_score_atlas.csv: one task per row with six scores.
analysis_summary.json: descriptive statistics, paired task-cluster bootstrap
intervals (10,000 resamples, seed 20260930), families and sensitivity analyses.
all_campaign_attempts.csv and infrastructure_history.csv: full operational
history, including excluded tasks and saved INFRA/recovery attempts. These are
not the statistical denominator. Known and conservative charges are separate.
task_selection.csv: the 46 retained and four added task IDs.
PNG/SVG figures: the eight charts used in the combined PDF report.
validation.json and final_quality_checks.json: journal reconciliation,
independent numerical checks, old-result preservation and completed visual QA.

The original task, not a language/model condition, is the uncertainty unit.
Managed-cloud execution, different reasoning semantics, transport revisions,
post-outcome task expansion and AI self-reviewed translations limit inference.
Intervals are exploratory and unadjusted for multiple contrasts. The resolved
main view and common primary-only sensitivity must be reported together.
This package contains no credentials, agent environments or private solutions.
'''
    atomic_bytes(data/'README.md',note.encode())
    archive=out/'Indic_Harness_Bench_50_Task_Research_Data.zip'
    files=[data/name for name in ['README.md','analysis_summary.json','matched_conditions.csv','matched_conditions.json','task_score_atlas.csv','all_campaign_attempts.csv','infrastructure_history.csv','task_selection.csv','validation.json','final_quality_checks.json','pdf_build_validation.json']]
    files+=sorted((out/'figures').glob('*.png'))+sorted((out/'figures').glob('*.svg'))
    temp=archive.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
        for file in files:z.write(file,file.relative_to(out))
    temp.replace(archive)
    final=dict(status='complete',finished_utc=stamp,report_ready=True,
               pdf=ready['pdf'],pdf_sha256=qa['pdf_sha256'],data_archive=str(archive),
               data_archive_sha256=sha(archive),new_attempts=24,new_infra=0,
               matched_tasks=50,scored_conditions=300,old_results_preserved=True,
               frozen_execution_unchanged=True,visual_review_passed=True,
               codex_pdf_tab_status='queued_by_open_in_codex',automation_status='PAUSED',
               prior_failed_pipeline_record_preserved=True,starts_model_calls=False)
    atomic_json(SHARED/'results/report_finish_status.json',final)
    handoff=SHARED/'results/HANDOFF.md'
    header=f'''# COMPLETED - 50-task report ready ({stamp})

Current authoritative state: 24/24 new primary conditions saved and scored,
exactly 24 total new attempts, zero INFRA, zero retries and zero unknown usage.
OSS: 5 completed processes + 7 scored budget stops; Nemotron: 11 completed
processes + 1 scored budget stop. No low score was retried or repaired.
All 50 matched task groups / 300 conditions are reconciled to journals.
All earlier results/PDF/reference and frozen execution files remain unchanged.
All new calls settled and owned Docker resources were removed; controller exited.

Final PDF: output/pdf/Indic_Harness_Bench_50_Task_Combined_Report.pdf (18 pages).
SHA-256: {qa['pdf_sha256']}
All pages rendered and visually verified; report_data/final_quality_checks.json
records the evidence. Research data/PNG/SVG bundle: {archive.name} under output/pdf.
Read results/report_ready.json and report_finish_status.json for final state.
The initial background builder's report-only serialization failure is preserved
in report_pipeline_process.json/log; subsequent repaired builds and visual QA
succeeded. Do not treat that historical failure or the notes below as pending work.
The PDF tab was queued in Codex. The visible read-only scoreboard at
http://127.0.0.1:51707/ now shows completion. The follow-up heartbeat is PAUSED.
No remaining benchmark or report work; never automatically rerun these attempts.
The PDF creation marker already ran exactly once; do not repeat it for this artifact.

## Historical preparation and execution notes (superseded by completion above)

'''
    atomic_bytes(handoff,header.encode()+handoff.read_bytes())
    print(json.dumps(final,indent=2))

if __name__=='__main__':finish()
