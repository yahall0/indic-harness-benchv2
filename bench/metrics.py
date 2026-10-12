"""Machine-readable attempt metrics and paired task-level exploratory estimates."""
import csv,json,os,random,re
from pathlib import Path
from bench.durable import atomic_json,encode

AGENT_OUTCOMES={'completed','agent_failed','timeout','budget_exhausted','integrity_failed'}

def attempt_metrics(journal,row,category):
    result=json.loads(row['result']) if row.get('result') else {}
    oracle=result.get('oracle',{}); score=oracle.get('outcome_score')
    records=[json.loads(c['response']) for c in journal.db.execute('SELECT response FROM calls WHERE run_id=? AND response IS NOT NULL ORDER BY reserved_at',(row['id'],))]
    first=records[0].get('usage') if records else None
    unaccounted_input=max(0,row['input_bound']-row['input_actual'])
    unaccounted_output=max(0,row['output_reserved']-row['output_actual'])
    usage_uncertain=bool(row['usage_missing'] or unaccounted_input or unaccounted_output)
    full=row['status']=='completed' and score is not None and score>=.9999 and all(c.get('pass') for c in oracle.get('checks',[])) and not result.get('integrity')
    available=row['status'] in AGENT_OUTCOMES
    return {'run_id':row['id'],'task_id':row['task'],'language':row['language'],'category':category,'status':row['status'],
      'original_score':score,'full_completion':int(full) if available else None,'integrity_violations':result.get('integrity',[]),
      'runtime_freeze_hash':result.get('runtime_freeze_hash',row['dataset_hash'] if row.get('started') else None),
      'study_id':row['dataset_hash'],
      'operator_stop':bool(journal.db.execute("SELECT 1 FROM events WHERE run_id=? AND kind='operator_stop_annotation' LIMIT 1",(row['id'],)).fetchone()),
      'elapsed_sec':result.get('elapsed_sec'),'inference_latency_sec':sum(c.get('latency_sec',0) for c in records) if records else None,
      'physical_requests':row['requests'],'input_tokens':row['input_actual'] if not usage_uncertain and records else None,
      'output_tokens':row['output_actual'] if not usage_uncertain and records else None,'known_input_tokens':row['input_actual'],
      'usage_uncertain':usage_uncertain,'unaccounted_input_reserved':unaccounted_input,'unaccounted_output_reserved':unaccounted_output,
      'known_output_tokens':row['output_actual'],'usage_missing_calls':row['usage_missing'],
      'first_context_prompt_tokens':first.get('prompt_tokens') if isinstance(first,dict) else None,
      'tool_calls':sum(c.get('tool_calls',0) for c in records) if records else None,
      'transport_retries':sum(c.get('retries',0) for c in records),'key_rotations':sum(c.get('rotations',0) for c in records),
      'pause_cause':result.get('pause_reason'),'tool_errors':None,'tool_schema_errors':None,'compaction_events':None,
      'unavailable_measurements':['isolated_user_prompt_tokens','tool_errors','tool_schema_errors','compaction_events'],
      'agent_outcome':available,'score_available_for_analysis':available and score is not None}

def interval(values,seed=20260930,samples=10000):
    if len(values)<2: return None
    rng=random.Random(seed); means=sorted(sum(rng.choices(values,k=len(values)))/len(values) for _ in range(samples))
    return [means[int(.025*samples)],means[min(samples-1,int(.975*samples))]]

def compare(rows):
    grouped={}
    for row in rows: grouped.setdefault(row['task_id'],{})[row['language']]=row
    complete={t:v for t,v in grouped.items() if set(v)=={'en','hi','hinglish'} and all(r['agent_outcome'] for r in v.values())}
    estimates=[]
    for language in ('hi','hinglish'):
        for category in [None]+sorted({r['category'] for r in rows}):
            pairs=[v for v in complete.values() if category is None or v['en']['category']==category]
            diffs=[(v['en']['full_completion']-v[language]['full_completion'])*100 for v in pairs]
            scored=[v for v in pairs if all(v[l]['score_available_for_analysis'] for l in ('en',language))]
            score_diffs=[(v['en']['original_score']-v[language]['original_score'])*100 for v in scored]
            ratios=[v[language]['first_context_prompt_tokens']/v['en']['first_context_prompt_tokens'] for v in pairs if v['en']['first_context_prompt_tokens'] and v[language]['first_context_prompt_tokens']]
            estimates.append({'contrast':'English minus '+language,'category':category or 'all','complete_task_triplets':len(pairs),
                'completion_difference_pp':sum(diffs)/len(diffs) if diffs else None,'completion_bootstrap_95_percent_interval_pp':interval(diffs),
                'paired_score_tasks':len(scored),'score_difference_pp':sum(score_diffs)/len(score_diffs) if score_diffs else None,
                'score_bootstrap_95_percent_interval_pp':interval(score_diffs),'mean_first_context_token_ratio':sum(ratios)/len(ratios) if ratios else None})
    return {'exploratory':True,'bootstrap_unit':'original task; matched conditions resampled together','bootstrap_seed':20260930,'bootstrap_samples':10000,
        'attempted_runs':sum(r['status']!='planned' for r in rows),'complete_triplets':len(complete),
        'incomplete_triplets':[{'task_id':t,'statuses':{l:r['status'] for l,r in v.items()}} for t,v in grouped.items() if t not in complete],
        'infrastructure_outcomes':[r['run_id'] for r in rows if r['status'] not in AGENT_OUTCOMES|{'planned'}],
        'estimates':estimates,'limitations':[f'One attempt per language; {len(grouped)} tasks represented in these records; exploratory and no guarantee of significance.',
        'Original deterministic grading may reward incomplete semantic solutions; added integrity checks are reported separately.',
        'First-context token ratios include OpenClaw system/tool overhead; they do not isolate user-prompt tokenization or prove causal tokenizer effects.',
        'Conservative byte-based preflight reservations can stop an attempt before its actual token cap; reported as budget exhaustion, with complete-triplet availability shown.']}

def export(journal,destination,manifest):
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    categories={t['task_id']:t['category'] for t in manifest}
    rows=[attempt_metrics(journal,r,categories.get(r['task'],'unknown')) for r in journal.runs()]
    fields=list(rows[0]) if rows else ['run_id','task_id','language','category','status','original_score','full_completion']
    for name,kind in [('metrics.csv','csv'),('metrics.jsonl','jsonl')]:
        p=destination/name; temp=p.with_name(p.name+'.tmp')
        with temp.open('w',encoding='utf-8',newline='') as f:
            if kind=='csv':
                writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
                for r in rows: writer.writerow({k:encode(v) if isinstance(v,(list,dict)) else v for k,v in r.items()})
            else:
                for row in rows: f.write(encode(row)+'\n')
            f.flush(); os.fsync(f.fileno())
        os.replace(temp,p)
    analysis=compare(rows); atomic_json(destination/'analysis.json',analysis)
    return analysis
