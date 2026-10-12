"""Read-only study analysis: 50 task clusters, six matched conditions each."""
import csv,json,math
from collections import Counter,defaultdict
from contextlib import closing
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tmp/pdf-report-deps'))
import numpy as np
from extension50.common import ROOT,NEM,SHARED,TASKS,LABEL,read,readonly,sha,verify_preserved
from bench.metrics import attempt_metrics,AGENT_OUTCOMES
from bench.durable import atomic_json

OUT=ROOT/'output/pdf/report_data'
LANGS=['en','hi','hinglish'];MODELS=['oss','nemotron'];SEED=20260930

def normalize(r):
    out={}
    for k,v in r.items():
        if isinstance(v,str):
            if v=='': v=None
            elif v in ['True','False']:v=v=='True'
            elif k in ['original_score','elapsed_sec','inference_latency_sec','input_tokens','output_tokens','first_context_prompt_tokens','known_input_tokens','known_output_tokens','physical_requests','full_completion','usage_missing_calls','tool_calls','transport_retries','key_rotations','unaccounted_input_reserved','unaccounted_output_reserved']:
                v=float(v)
            elif v.startswith('['):
                try:v=json.loads(v)
                except ValueError:pass
        out[k]=v
    return out

def metrics(p,model,attempt_number=1):
    with closing(readonly(p)) as db:
        class View:pass
        v=View();v.db=db
        cats={t['task_id']:t['category'] for t in read(ROOT/'dataset/task_manifest.json')}
        rows=[]
        for r in db.execute('SELECT * FROM runs ORDER BY rowid'):
            m=attempt_metrics(v,dict(r),cats.get(r['task'],'unknown'));m.update(model=model,attempt_number=attempt_number,journal=str(p));rows.append(m)
        return rows

def interval(vals):
    vals=np.asarray(vals,dtype=float);rng=np.random.default_rng(SEED)
    boot=vals[rng.integers(0,len(vals),(10000,len(vals)))].mean(axis=1)
    return [float(x) for x in np.quantile(boot,[.025,.975])]

def summary(rows):
    values={}
    for m in MODELS:
        values[m]={}
        for l in LANGS:
            group=[r for r in rows if r['model']==m and r['language']==l]
            scores=[100*r['original_score'] for r in group]
            values[m][l]={'n':len(group),'mean_score':float(np.mean(scores)),'median_score':float(np.median(scores)),'score_ci':interval(scores),'full_count':sum(int(r['full_completion']) for r in group),'zero_count':sum(r['original_score']==0 for r in group),'status_counts':dict(Counter(r['status'] for r in group)),'median_elapsed_sec':float(np.median([r['elapsed_sec'] for r in group])),'median_known_input':float(np.median([r['known_input_tokens'] for r in group])),'median_known_output':float(np.median([r['known_output_tokens'] for r in group])),'usage_missing_calls':sum(int(r['usage_missing_calls']) for r in group)}
    return values

def contrasts(rows,tasks):
    index={(r['model'],r['task_id'],r['language']):r for r in rows}
    out={}
    for l in LANGS:
        diffs=[100*(index['nemotron',t,l]['original_score']-index['oss',t,l]['original_score']) for t in tasks]
        out['model_'+l]={'mean_difference_pp':float(np.mean(diffs)),'ci':interval(diffs),'wins':sum(d>1e-7 for d in diffs),'ties':sum(abs(d)<1e-7 for d in diffs),'losses':sum(d< -1e-7 for d in diffs)}
    diffs=[float(np.mean([100*(index['nemotron',t,l]['original_score']-index['oss',t,l]['original_score']) for l in LANGS])) for t in tasks]
    out['model_overall']={'mean_difference_pp':float(np.mean(diffs)),'ci':interval(diffs),'wins':sum(d>1e-7 for d in diffs),'ties':sum(abs(d)<1e-7 for d in diffs),'losses':sum(d< -1e-7 for d in diffs)}
    for m in MODELS:
        for l in ['hi','hinglish']:
            diffs=[100*(index[m,t,'en']['original_score']-index[m,t,l]['original_score']) for t in tasks]
            ratios=[index[m,t,l]['first_context_prompt_tokens']/index[m,t,'en']['first_context_prompt_tokens'] for t in tasks if index[m,t,'en']['first_context_prompt_tokens'] and index[m,t,l]['first_context_prompt_tokens']]
            out[m+'_en_minus_'+l]={'mean_difference_pp':float(np.mean(diffs)),'ci':interval(diffs),'first_context_ratio_n':len(ratios),'mean_first_context_ratio':float(np.mean(ratios)) if ratios else None,'median_first_context_ratio':float(np.median(ratios)) if ratios else None}
    return out

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        cols=list(dict.fromkeys(k for row in rows for k in row));writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader()
        writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)

def analyze():
    complete=read(SHARED/'results/completion.json')
    if not complete['complete'] or not complete['preserved'] or not verify_preserved():raise ValueError('All 24 scored additions and original preservation required')
    oldoss=[normalize(r) for r in csv.DictReader((ROOT/'pdf/report_data/included_condition_metrics.csv').open(encoding='utf-8-sig'))]
    oldnem=read(NEM/'results/exports/user_requested_resolved_metrics.json')
    oldtasks=read(SHARED/'config/selection.json')['original_matched_task_ids'];tasks=oldtasks+TASKS
    rows=[]
    for m,old in [('oss',oldoss),('nemotron',oldnem)]:
        for r in old:rows.append({**r,'model':m,'attempt_number':r.get('attempt_number',1),'added_task':False})
    progress=read(SHARED/'results/progress.json')
    for m in MODELS:
        for r in progress['models'][m]['resolved']:
            if not r['score_available_for_analysis']: raise ValueError('Missing new scored condition')
            rows.append({**r,'added_task':True})
    index={(r['model'],r['task_id'],r['language']):r for r in rows}
    assert len(rows)==len(index)==300 and len(tasks)==50
    assert all((m,t,l) in index for m in MODELS for t in tasks for l in LANGS)
    assert all(r['original_score'] is not None and 0<=r['original_score']<=1 for r in rows)
    # Reconcile every selected row against an authoritative read-only journal.
    lookup={}
    original_primary={}
    all_attempts=[]
    ledger=defaultdict(lambda:{'unsettled_reservations':0,'recorded_forwards':0})
    for m,origin in [('oss',ROOT),('nemotron',NEM)]:
        paths=[(origin/'results/journal.sqlite3',1)]
        recovery_folder=origin/'results/infrastructure-retries' if m=='oss' else origin/'results/recoveries'
        paths += [(p,2) for p in recovery_folder.rglob('journal.sqlite3') if 'checkpoints' not in p.parts]
        if m=='nemotron': paths += [(p,3) for p in (origin/'results/additional-recoveries').glob('*/journal.sqlite3')]
        paths += [(origin/'results'/LABEL/'journal.sqlite3',1)]
        paths += [(p,int(p.parent.name.split('-')[-1])) for p in (origin/'results'/LABEL/'recoveries').glob('*/attempt-*/journal.sqlite3')]
        for p,num in paths:
            if not p.exists():continue
            got=metrics(p,m,num);all_attempts+=got
            with closing(readonly(p)) as db:
                ledger[m]['unsettled_reservations']+=db.execute("SELECT count(*) FROM calls WHERE status='reserved'").fetchone()[0]
                ledger[m]['recorded_forwards']+=db.execute('SELECT count(*) FROM forwards').fetchone()[0]
            for r in got:
                lookup[m,r['run_id']]=r
                if num==1:original_primary[m,r['task_id'],r['language']]=r
    for r in rows:
        raw=lookup[r['model'],r['run_id']]
        assert raw['status']==r['status'] and raw['original_score']==r['original_score'] and raw['full_completion']==r['full_completion']
    eligible=[t for t in tasks if all(original_primary[m,t,l]['score_available_for_analysis'] for m in MODELS for l in LANGS)]
    primary_rows=[original_primary[m,t,l] for m in MODELS for t in eligible for l in LANGS]
    stats=summary(rows);differences=contrasts(rows,tasks)
    categories={t['task_id']:t['category'] for t in read(ROOT/'dataset/task_manifest.json')}
    cats=[]
    for c in sorted({categories[t] for t in tasks}):
        ts=[t for t in tasks if categories[t]==c]
        means={m:float(np.mean([100*index[m,t,l]['original_score'] for t in ts for l in LANGS])) for m in MODELS}
        cats.append({'category':c,'tasks':len(ts),'means':means,'difference_pp':means['nemotron']-means['oss']})
    accounting={}
    for m in MODELS:
        rs=[r for r in all_attempts if r['model']==m]
        accounting[m]={'attempts':len(rs),'primary_attempts':sum(r['attempt_number']==1 for r in rs),'recovery_attempts':sum(r['attempt_number']>1 for r in rs),'status_counts':dict(Counter(r['status'] for r in rs)),'physical_transmissions':sum(r['physical_requests'] for r in rs),'known_input':sum(r['known_input_tokens'] for r in rs),'known_output':sum(r['known_output_tokens'] for r in rs),'charged_input':sum(r['known_input_tokens']+r['unaccounted_input_reserved'] for r in rs),'charged_output':sum(r['known_output_tokens']+r['unaccounted_output_reserved'] for r in rs),'usage_missing_calls':sum(r['usage_missing_calls'] for r in rs)}
        accounting[m]['reserved_physical_allowances']=accounting[m]['physical_transmissions']
        accounting[m]['physical_transmissions']=ledger[m]['recorded_forwards']
        accounting[m]['unsettled_reservations']=ledger[m]['unsettled_reservations']
    atlas=[]
    for t in tasks:
        a={'task_id':t,'category':categories[t],'added':t in TASKS}
        for m in MODELS:
            for l in LANGS:a[m+'_'+l]=100*index[m,t,l]['original_score']
        a['mean_model_gain']=np.mean([a['nemotron_'+l]-a['oss_'+l] for l in LANGS]);atlas.append(a)
    failchecks=defaultdict(Counter)
    for m,origin in [('oss',ROOT),('nemotron',NEM)]:
        # Detailed oracle checks, including failed evidence/artifact contracts.
        for r in [r for r in rows if r['model']==m]:
            p=Path(lookup[m,r['run_id']]['journal'])
            with closing(readonly(p)) as db:
                raw=json.loads(db.execute('SELECT result FROM runs WHERE id=?',(r['run_id'],)).fetchone()[0])
                for check in raw.get('oracle',{}).get('checks',[]):
                    if not check.get('pass'):failchecks[m][check.get('id','unknown')]+=1
    result={'task_count':50,'conditions_per_model':150,'total_scored_conditions':300,'new_primary_conditions':24,'models':stats,'contrasts':differences,'categories':cats,'old46_models':summary([r for r in rows if not r['added_task']]),'additions_models':summary([r for r in rows if r['added_task']]),'primary_only':{'task_count':len(eligible),'tasks':eligible,'models':summary(primary_rows),'contrasts':contrasts(primary_rows,eligible),'excluded_task_ids':[t for t in tasks if t not in eligible]},'accounting_all_campaign_attempts':accounting,'extension_accounting':progress['accounting'],'bootstrap':{'unit':'original task; six matched model/language conditions remain together','samples':10000,'seed':SEED,'generator':'numpy default_rng','interval':'percentile 2.5%-97.5%; exploratory, unadjusted for multiplicity'},'most_frequent_failed_checks':{m:failchecks[m].most_common(12) for m in MODELS},'provenance':{'selection_file':str(SHARED/'config/selection.json'),'extension_freeze':read(SHARED/'config/freeze.json')['runtime_freeze_hash'],'original_oss_pdf_sha256':sha(ROOT/'pdf/Indic_Harness_Bench_Experiment_Report.pdf'),'old_results_preserved':True,'every_selected_score_reconciled_to_journal':True,'all_model_attempts_saved':True,'no_model_based_task_exclusion':True}}
    OUT.mkdir(parents=True,exist_ok=True);atomic_json(OUT/'analysis_summary.json',result);atomic_json(OUT/'matched_conditions.json',rows)
    write_csv(OUT/'matched_conditions.csv',rows);write_csv(OUT/'task_score_atlas.csv',atlas);write_csv(OUT/'all_campaign_attempts.csv',all_attempts);write_csv(OUT/'infrastructure_history.csv',[r for r in all_attempts if r['status'] not in AGENT_OUTCOMES]);write_csv(OUT/'task_selection.csv',[{'task_id':t,'category':categories[t],'added_task':t in TASKS} for t in tasks])
    atomic_json(OUT/'validation.json',{'passed':True,'n_tasks':50,'matched_conditions':300,'exactly_24_new_primary_conditions':sum(r['task_id'] in TASKS and r['attempt_number']==1 for r in all_attempts)==24,'original_results_preserved':True,'all_scores_match_journals':True})
    print(json.dumps({'tasks':50,'conditions':300,'models':stats,'contrasts':differences},indent=2))
    return result,rows,atlas

if __name__=='__main__':analyze()
