"""Freeze the pre-outcome 40-task candidate set; validation is still pending."""
from __future__ import annotations
import csv
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEW=Path(r'C:\Users\prish\Documents\Codex\2026-09-30\new-chat\outputs\indic-harness-bench-review')
CORE=[1,2,20,21,22,4,5,24,27,26,12,33,34,35,36,16,17,39,40,41,
      49,50,51,52,53,7,57,58,59,60,19,62,63,64,67,70,71,72,74,75]
HEAVY={3:'Browser/navigation setup and a public-tunnel hook; defer for the minimal offline release.',
       25:'Original oracle has an unsatisfiable check: followup_emails is searched after underscores are replaced with spaces. Deferred without modifying source grading; replaced pre-freeze by 027 in the same family.',
       6:'Browser/navigation setup and a public-tunnel hook; defer for the minimal offline release.',
       9:'Bespoke Git branch/remote preparation and push workflow; defer this setup within the 40-task cap.',
       10:'PDF/DOCX processing and binary artifact dependencies; defer specialist office tooling.',
       11:'Five rounds with changing code layers and executable hook verification; defer complex runtime orchestration.',
       14:'Open-ended decomposition and virtual launch deliverables; defer in favor of smaller deterministic workflows.',
       23:'Multi-step HTTP form and confirmation server; defer additional mock-service integration.',
       61:'Timed asynchronous injections and polling; defer timing-dependent evaluation.',
       78:'Cursor/retry server with a public-tunnel hook; defer additional service adaptation.',
       81:'DOM/form workflow with a public-tunnel hook; defer additional service adaptation.',
       88:'Executable mock-client repair, transient HTTP errors, and a public-tunnel hook; defer complex service integration.',
       104:'Timed asynchronous update injection and polling; defer timing-dependent evaluation.'}

def write(path,obj): path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
    tasks=json.loads((ROOT/'dataset/task_manifest.json').read_text(encoding='utf-8'))
    for t in tasks:
        t['pilot_candidate']=t['number'] in CORE
        if t['status']=='excluded': continue
        if t['number'] in CORE:
            t['status']='candidate'; t['reason']=None
        else:
            t['status']='deferred'
            t['reason']=HEAVY.get(t['number'],'Outside the 40-task initial release: five pre-outcome selections per task family; retained for later expansion.')
    candidates=[t for t in tasks if t['status']=='candidate']
    assert len(candidates)==40 and len(set(CORE))==40
    counts=Counter(t['category'] for t in candidates)
    assert len(counts)==8 and set(counts.values())=={5}
    write(ROOT/'dataset/task_manifest.json',tasks)
    write(ROOT/'dataset/pilot_plan.json',{'task_numbers':CORE,'languages':['en','hi','hinglish'],
        'attempts_per_language':1,'planned_task_triplets':40,'planned_runs':120,'status':'not_frozen',
        'selection':'Five tasks per original family, chosen before model outcomes. Emphasis on low-dependency local workflows.',
        'replacement_rule':'If environment/oracle/translation validation fails, use the lowest-numbered validated task in the same family that meets the lightweight policy before freezing; never replace based on agent performance.',
        'budget':'Free credits only; pause on quota exhaustion and report incomplete triplets.',
        'not_yet_validated':True})
    with (ROOT/'dataset/task_inventory.csv').open('w',newline='',encoding='utf-8-sig') as f:
        keys=['task_id','category','difficulty','status','reason','original_timeout_sec','attempt_timeout_sec','pilot_candidate']
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore'); w.writeheader(); w.writerows(tasks)
    summary=json.loads((ROOT/'reports/audit_summary.json').read_text(encoding='utf-8'))
    summary.update({'candidates':40,'excluded':2,'deferred':64,'planned_runs':120,'planned_language_versions':120,
        'candidate_categories':dict(counts),'curation_policy':'40 matched tasks; avoid heavy setup/external dependencies; local file tasks, lightweight code repair, and simple mock APIs retained.'})
    write(ROOT/'reports/audit_summary.json',summary)
    for path in (ROOT/'reports/audit_summary.json',ROOT/'dataset/task_inventory.csv',ROOT/'dataset/pilot_plan.json'):
        shutil.copy2(path,REVIEW/path.name)
    print(json.dumps({'candidates':40,'excluded':2,'deferred':64,'planned_runs':120,'category_counts':dict(counts)},indent=2))

if __name__=='__main__': main()
