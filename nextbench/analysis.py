"""Atomic future-campaign exports; retain all attempts and both analysis views."""
import csv
import json
import os
from contextlib import closing
from pathlib import Path

from bench.durable import Journal, atomic_json, encode
from bench.metrics import attempt_metrics, compare, interval, AGENT_OUTCOMES
from nextbench.recovery import _recovery_root


def paired_baseline(rows, baseline):
    """Pair complete scored task triplets in both models; never impute INFRA."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row['task_id'], {})[row['language']] = row
    old = {(r['task_id'], r['language']): r for r in baseline}
    complete = {task: values for task, values in grouped.items() if set(values) == {'en','hi','hinglish'}
                and all(r['score_available_for_analysis'] and r['agent_outcome']
                        and (task, lang) in old for lang, r in values.items())}
    estimates = []
    for lang in ('en','hi','hinglish'):
        differences = [(values[lang]['original_score'] - float(old[task, lang]['original_score'])) * 100
                       for task, values in complete.items()]
        completion = [(values[lang]['full_completion'] - int(old[task, lang]['full_completion'])) * 100
                      for task, values in complete.items()]
        estimates.append({'language':lang, 'paired_tasks':len(differences),
                          'score_difference_pp':sum(differences)/len(differences) if differences else None,
                          'score_bootstrap_95_percent_interval_pp':interval(differences),
                          'completion_difference_pp':sum(completion)/len(completion) if completion else None,
                          'completion_bootstrap_95_percent_interval_pp':interval(completion)})
    return {'contrast':'Nemotron minus completed GPT-OSS baseline', 'exploratory':True,
            'paired_task_ids':sorted(complete), 'paired_task_triplets':len(complete),
            'excluded_future_task_ids':sorted(set(grouped) - set(complete)), 'estimates':estimates,
            'bootstrap_unit':'original task; matched model/language conditions resampled together',
            'bootstrap_samples':10000, 'bootstrap_seed':20260930,
            'no_imputation':True, 'baseline_primary_report_unchanged':True}


def export(primary, campaign, manifest):
    campaign = Path(campaign).resolve()
    categories = {t['task_id']: t['category'] for t in manifest}
    primary_rows, recovered_rows, all_rows = [], [], []
    registry = {r['primary_run_id']: dict(r) for r in primary.db.execute('SELECT * FROM recovery_attempts')}
    def metric(journal, row, primary_id, number):
        value = attempt_metrics(journal, row, categories[row['task']])
        value.update(attempt_number=number, primary_run_id=primary_id)
        records = [json.loads(r['response']) for r in journal.db.execute(
            'SELECT response FROM calls WHERE run_id=? AND response IS NOT NULL', (row['id'],))]
        value['tool_schema_errors'] = sum(r.get('schema_errors', 0) for r in records) if records else None
        value['reasoning_tokens'] = sum(r['usage']['completion_tokens_details']['reasoning_tokens'] for r in records) if records and all(
            isinstance(r.get('usage'), dict) and isinstance(r['usage'].get('completion_tokens_details'), dict)
            and isinstance(r['usage']['completion_tokens_details'].get('reasoning_tokens'), int) for r in records) else None
        value['physical_transmissions'] = journal.db.execute('SELECT count(*) FROM forwards WHERE call_id IN (SELECT id FROM calls WHERE run_id=?)', (row['id'],)).fetchone()[0]
        value['unavailable_measurements'] = [v for v in value['unavailable_measurements'] if v != 'tool_schema_errors']
        if value['reasoning_tokens'] is None:
            value['unavailable_measurements'].append('separate_reasoning_token_count')
        return value
    for row in primary.runs():
        original = metric(primary, row, row['id'], 1)
        selected = original
        primary_rows.append(original); all_rows.append(original)
        entry = registry.get(row['id'])
        if entry:
            path = _recovery_root(campaign, row['id'], entry['relative_root']) / 'journal.sqlite3'
            if path.exists():
                with closing(Journal(path)) as retry:
                    retry_row = retry.get(entry['retry_run_id'])
                    recovered = metric(retry, retry_row, row['id'], 2)
                    all_rows.append(recovered)
                    if retry_row['status'] in AGENT_OUTCOMES:
                        selected = recovered
        recovered_rows.append(selected)
    destination = campaign / 'results/exports'
    destination.mkdir(parents=True, exist_ok=True)
    for name, rows in [('primary_metrics', primary_rows), ('recovery_inclusive_metrics', recovered_rows), ('all_attempt_metrics', all_rows)]:
        atomic_json(destination / (name + '.json'), rows)
        path = destination / (name + '.csv'); temporary = path.with_name(path.name + '.tmp')
        with temporary.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ['run_id'])
            writer.writeheader()
            for row in rows:
                writer.writerow({k: encode(v) if isinstance(v, (dict, list)) else v for k, v in row.items()})
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    for name, rows in [('primary_analysis', primary_rows), ('recovery_inclusive_analysis', recovered_rows)]:
        # Complete cases require an actual oracle score in all three languages.
        analysis = compare([{**row, 'agent_outcome': row['agent_outcome'] and row['score_available_for_analysis']} for row in rows])
        analysis.update(view=name, planned_tasks=46, planned_conditions=138,
                        selection_before_future_outcomes=True, baseline_report_unchanged=True,
                        attempt_selection='Use the sole recovery if it yields any agent outcome, without score selection; all attempts and costs retained.' if name.startswith('recovery') else 'Primary attempts only; no substitution.')
        analysis['limitations'].append('This fixed population was selected using baseline infrastructure attrition; future recovery policy differs from the baseline primary-only policy.')
        atomic_json(destination / (name + '.json'), analysis)
        baseline_path = Path(__file__).resolve().parents[1] / 'pdf/report_data/included_condition_metrics.csv'
        with baseline_path.open(encoding='utf-8-sig', newline='') as stream:
            baseline = list(csv.DictReader(stream))
        comparison = paired_baseline(rows, baseline)
        comparison['future_analysis_view'] = name
        comparison['attempt_policy_difference'] = name.startswith('recovery')
        atomic_json(destination / (name + '_vs_baseline.json'), comparison)
    return {'primary_conditions': len(primary_rows), 'all_attempts': len(all_rows)}
