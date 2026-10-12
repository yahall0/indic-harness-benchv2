"""One-shot, read-only comparison of durable outcomes on matched report tasks."""
import csv
import json
import sqlite3
import statistics
import sys
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CAMPAIGN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench.durable import atomic_json
from bench.metrics import AGENT_OUTCOMES, interval

LANGS = ('en', 'hi', 'hinglish')
TERMINAL = AGENT_OUTCOMES | {'infrastructure_failed', 'interrupted', 'quota_paused'}

def connect(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    db.execute('BEGIN')
    return db

def metric(db, raw, attempt=1):
    row = dict(raw)
    result = json.loads(row['result'] or '{}')
    oracle = result.get('oracle', {})
    score = oracle.get('outcome_score')
    calls = [json.loads(r['response']) for r in db.execute(
        'SELECT response FROM calls WHERE run_id=? AND response IS NOT NULL ORDER BY reserved_at', (row['id'],))]
    full = row['status'] == 'completed' and score is not None and score >= .9999 and all(
        check.get('pass') for check in oracle.get('checks', [])) and not result.get('integrity')
    finishes = Counter()
    for response in calls:
        for choice in response.get('choices', []):
            finishes[str(choice.get('finish_reason'))] += 1
        if response.get('finish_reason') is not None:
            finishes[str(response['finish_reason'])] += 1
    return dict(run_id=row['id'], task=row['task'], language=row['language'], status=row['status'],
        score=score if row['status'] in AGENT_OUTCOMES else None, full_completion=int(bool(full)),
        attempt=attempt, requests=row['requests'], input_tokens=row['input_actual'], output_tokens=row['output_actual'],
        usage_missing=row['usage_missing'], elapsed_sec=result.get('elapsed_sec'),
        latency_sec=sum(c.get('latency_sec', 0) for c in calls) if calls else None,
        tool_calls=sum(c.get('tool_calls', 0) for c in calls) if calls else None,
        finish_reasons=dict(finishes), pause_cause=result.get('pause_reason'),
        failed_checks=[c.get('name', c.get('id', c)) for c in oracle.get('checks', []) if not c.get('pass')],
        runtime=result.get('runtime_freeze_hash'), integrity=result.get('integrity', []),
        error_type=result.get('error_type'), cleanup_incomplete=result.get('cleanup_incomplete', False))

def average(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else None

def summarize(selected, baseline, tasks):
    estimates = []
    for lang in LANGS:
        new = [selected[t, lang] for t in tasks]
        old = [baseline[t, lang] for t in tasks]
        differences = [(n['score'] - o['score']) * 100 for n, o in zip(new, old)]
        estimates.append(dict(language=lang, tasks=len(tasks), nemotron_score=average(new, 'score') * 100,
            oss_score=average(old, 'score') * 100, gain_pp=sum(differences)/len(differences),
            gain_bootstrap_95_pp=interval(differences), nemotron_full=sum(r['full_completion'] for r in new),
            oss_full=sum(r['full_completion'] for r in old), nemotron_budgets=sum(r['status']=='budget_exhausted' for r in new),
            oss_budgets=sum(r['status']=='budget_exhausted' for r in old),
            nemotron_input=sum(r['input_tokens'] for r in new), oss_input=sum(r['input_tokens'] for r in old),
            nemotron_output=sum(r['output_tokens'] for r in new), oss_output=sum(r['output_tokens'] for r in old),
            nemotron_requests=sum(r['requests'] for r in new), oss_requests=sum(r['requests'] for r in old),
            nemotron_mean_sec=average(new,'elapsed_sec'), oss_mean_sec=average(old,'elapsed_sec'),
            nemotron_median_sec=statistics.median(r['elapsed_sec'] for r in new if r['elapsed_sec'] is not None),
            oss_median_sec=statistics.median(r['elapsed_sec'] for r in old if r['elapsed_sec'] is not None)))
    contrasts = []
    for model, rows in [('nemotron', selected), ('oss', baseline)]:
        for lang in ('hi','hinglish'):
            diffs = [(rows[t, lang]['score'] - rows[t, 'en']['score']) * 100 for t in tasks]
            contrasts.append(dict(model=model, contrast=lang+' minus en', difference_pp=sum(diffs)/len(diffs),
                bootstrap_95_pp=interval(diffs)))
    return dict(task_ids=tasks, task_triplets=len(tasks), estimates=estimates, language_contrasts=contrasts)

def main():
    observed = datetime.now(timezone.utc)
    with (ROOT/'pdf/report_data/included_condition_metrics.csv').open(encoding='utf-8-sig',newline='') as stream:
        report_rows = list(csv.DictReader(stream))
    report_keys = {(r['task_id'],r['language']) for r in report_rows}
    primary = []
    recoveries = []
    with closing(connect(CAMPAIGN/'results/journal.sqlite3')) as db:
        primary = [metric(db,r) for r in db.execute('SELECT * FROM runs ORDER BY rowid')]
        registry = [dict(r) for r in db.execute('SELECT * FROM recovery_attempts')]
        terminal_unsettled = db.execute("SELECT COUNT(*) FROM calls c JOIN runs r ON c.run_id=r.id WHERE c.status!='settled' AND r.status!='running'").fetchone()[0]
        for entry in registry:
            path = CAMPAIGN/'results'/entry['relative_root']/'journal.sqlite3'
            if not path.exists():
                path = CAMPAIGN/entry['relative_root']/'journal.sqlite3'
            if not path.exists():
                raise RuntimeError('Registered recovery journal absent: '+entry['primary_run_id'])
            with closing(connect(path)) as retry:
                recoveries.extend(metric(retry,r,2) for r in retry.execute('SELECT * FROM runs'))
    baseline = {}
    with closing(connect(ROOT/'results/journal.sqlite3')) as db:
        for row in db.execute('SELECT * FROM runs ORDER BY rowid'):
            if (row['task'],row['language']) in report_keys:
                val = metric(db,row)
                baseline[val['task'],val['language']] = val
    for expected in report_rows:
        actual = baseline[expected['task_id'],expected['language']]
        assert actual['status'] == expected['status']
        assert actual['score'] == float(expected['original_score'])
        assert actual['full_completion'] == int(expected['full_completion'])
    assert {(r['task'],r['language']) for r in primary} == report_keys
    originals = {(r['task'],r['language']):r for r in primary}
    selected = dict(originals)
    retry_by_key = {(r['task'],r['language']):r for r in recoveries}
    for key,r in retry_by_key.items():
        if r['status'] in AGENT_OUTCOMES:
            selected[key] = r
    tasks = sorted({key[0] for key in report_keys})
    resolved = [t for t in tasks if all(originals[t,l]['status'] in TERMINAL and
        ((t,l) not in retry_by_key or retry_by_key[t,l]['status'] in TERMINAL) for l in LANGS)]
    matched = [t for t in resolved if all(selected[t,l]['score'] is not None for l in LANGS)]
    primary_matched = [t for t in resolved if all(originals[t,l]['score'] is not None for l in LANGS)]
    report = dict(observed_utc=observed.isoformat(), observed_ist=observed.astimezone(timezone(timedelta(hours=5,minutes=30))).isoformat(),
        method='Read-only SQLite snapshots; exact report-selected keys; terminal complete scored triplets; budgets retained; no INFRA imputation; sole scored recovery replaces primary without score selection.',
        planned_tasks=46, primary_statuses=dict(Counter(r['status'] for r in primary)),
        resolved_tasks=len(resolved), resolved_task_ids=resolved, omitted_resolved_tasks=sorted(set(resolved)-set(matched)),
        active=[{k:r[k] for k in ('run_id','task','language','status')} for r in primary if r['status']=='running'],
        baseline_report_rows_verified=len(report_rows), terminal_unsettled_calls=terminal_unsettled,
        recovery_inclusive=summarize(selected,baseline,matched), primary_only=summarize(originals,baseline,primary_matched),
        all_recoveries=recoveries,
        all_terminal_primary_budgets_by_language=dict(Counter(r['language'] for r in primary if r['status']=='budget_exhausted')),
        post_repair_terminal_faults=[r for r in primary+recoveries if r['runtime']=='30ae3dfeb3de6a789fdfeea4130ae2abe232b161b52b6d1e00b67bf193584bd6' and r['status'] in TERMINAL and
            (r['status'] not in AGENT_OUTCOMES or r['usage_missing'] or r['integrity'] or r['error_type'] or r['cleanup_incomplete'])],
        post_repair_terminal_attempts=sum(r['runtime']=='30ae3dfeb3de6a789fdfeea4130ae2abe232b161b52b6d1e00b67bf193584bd6' and r['status'] in TERMINAL for r in primary+recoveries),
        task_rows=[dict(task=t, nemotron={l:selected[t,l] for l in LANGS}, oss={l:baseline[t,l] for l in LANGS}) for t in resolved],
        limitations=['Interim sequential prefix of fixed population; task categories and easy/hard mix not representative of all 46.',
            'Models have different supported thinking controls and runtime revisions; harness budgets are held fixed.',
            'Elapsed duration includes provider/network latency; output usage is not a separately measured reasoning-token count.',
            'Original first-task Hindi remains unresolved INFRA; exclude whole triplet, never score infrastructure as zero.'])
    destination = CAMPAIGN/'results/analyses'/('interim-comparison-'+observed.strftime('%Y%m%dT%H%M%S')+'.json')
    atomic_json(destination,report)
    print(json.dumps({**{k:v for k,v in report.items() if k not in ('task_rows','all_recoveries')},
        'task_scores':[{ 'task':t['task'], 'nemotron':[t['nemotron'][l]['score'] for l in LANGS], 'oss':[t['oss'][l]['score'] for l in LANGS],
                        'statuses':[t['nemotron'][l]['status'] for l in LANGS]} for t in report['task_rows']],
        'saved_analysis':str(destination)},ensure_ascii=False))

if __name__ == '__main__':
    main()
