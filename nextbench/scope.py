"""Pin future benchmark scope to the completed report using read-only evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path

from bench.durable import atomic_json, encode

LANGUAGES = ('en', 'hi', 'hinglish')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def build_scope(root):
    root = Path(root).resolve()
    scores = read_csv(root / 'pdf/report_data/included_task_scores.csv')
    metrics = read_csv(root / 'pdf/report_data/included_condition_metrics.csv')
    task_ids = {row['task_id'] for row in scores}
    if len(scores) != 46 or len(task_ids) != 46 or len(metrics) != 138:
        raise ValueError('The completed report must contain 46 tasks and 138 conditions')
    freeze = json.loads((root / 'dataset/freeze.json').read_text(encoding='utf-8'))
    manifest = json.loads((root / 'dataset/task_manifest.json').read_text(encoding='utf-8'))
    ordered_tasks = [task for task in freeze['task_ids'] if task in task_ids]
    if set(ordered_tasks) != task_ids:
        raise ValueError('Report scope does not match the frozen dataset')
    db = sqlite3.connect((root / 'results/journal.sqlite3').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        rows = [dict(row) for row in db.execute('SELECT * FROM runs ORDER BY rowid')]
    finally:
        db.close()
    selected = [row for row in rows if row['task'] in task_ids]
    expected = {(task, language) for task in task_ids for language in LANGUAGES}
    if len(selected) != 138 or {(r['task'], r['language']) for r in selected} != expected:
        raise ValueError('Selected journal conditions are missing or duplicated')
    if any(row['status'] in {'planned', 'running', 'infrastructure_failed'} for row in selected):
        raise ValueError('Report selection contains an ineligible primary condition')
    if {row['dataset_hash'] for row in selected} != {freeze['study_id']}:
        raise ValueError('Unexpected baseline study identity')
    if {(r['task_id'], r['language'], r['run_id']) for r in metrics} != {
            (r['task'], r['language'], r['id']) for r in selected}:
        raise ValueError('Report metrics and authoritative journal disagree')
    source_names = ['dataset/freeze.json', 'pdf/report_data/included_task_scores.csv',
                    'pdf/report_data/included_condition_metrics.csv',
                    'pdf/report_data/analysis_summary.json', 'pdf/report_data/report_validation.json',
                    'pdf/Indic_Harness_Bench_Experiment_Report.pdf']
    inputs = {'dataset/task_manifest.json', 'dataset/translation_reviews.json',
              'provenance/reference_before.json', 'config/images.json', 'runtime/grader.py'}
    for task in manifest:
        if task['task_id'] not in task_ids:
            continue
        inputs.add('reports/oracles/' + task['task_id'] + '.json')
        for language in LANGUAGES:
            for name in task['source_prompt_files']:
                inputs.add(f"tasks/{task['task_id']}/prompts/{language}/{name}")
    for name in inputs:
        expected_hash = freeze['file_hashes'].get(name)
        if expected_hash and digest(root / name) != expected_hash:
            raise ValueError('Frozen input changed: ' + name)
    validation = json.loads((root / 'pdf/report_data/report_validation.json').read_text(encoding='utf-8'))
    if digest(root / source_names[-1]) != validation['pdf_sha256']:
        raise ValueError('Completed PDF no longer matches its saved validation')
    if hashlib.sha256(encode(rows).encode()).hexdigest() != validation['primary_run_records_sha256']:
        raise ValueError('Baseline primary records no longer match the completed report')
    scope = {
        'schema_version': 1,
        'selection_basis': 'Exactly the original tasks included in the completed GPT-OSS report; selected before future model outcomes.',
        'baseline_study_id': freeze['study_id'],
        'baseline_runtime_freeze': freeze['dataset_hash'],
        'task_count': 46, 'condition_count': 138, 'languages': list(LANGUAGES),
        'task_ids': ordered_tasks,
        'conditions': [{'task': row['task'], 'language': row['language'],
                        'baseline_primary_run_id': row['id']} for row in selected],
        'execution_order_policy': 'Preserve the selected conditions in original baseline journal order, including each task language order.',
        'source_sha256': {name: digest(root / name) for name in source_names},
        'shared_input_sha256': {name: digest(root / name) for name in sorted(inputs)},
        'prompt_file_count': sum(name.startswith('tasks/') for name in inputs),
        'future_model_outcomes_used_for_selection': False,
        'new_study_id_required': True,
    }
    scope['selection_id'] = hashlib.sha256(encode(scope).encode()).hexdigest()
    return scope


def validate_scope(root, scope):
    if build_scope(root) != scope:
        raise ValueError('Pinned report scope or its source evidence has changed')
    return {'tasks': scope['task_count'], 'conditions': scope['condition_count'],
            'prompt_files': scope['prompt_file_count'], 'selection_id': scope['selection_id']}


def save_scope(root, destination):
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    if not destination.is_relative_to(root / 'campaigns/shared'):
        raise ValueError('Scope must be saved in the separate campaigns/shared namespace')
    scope = build_scope(root)
    if destination.exists():
        if json.loads(destination.read_text(encoding='utf-8')) != scope:
            raise ValueError('Refusing to overwrite a different pinned scope')
    else:
        atomic_json(destination, scope)
    return validate_scope(root, scope)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = save_scope(root, args.write) if args.write else validate_scope(root, build_scope(root))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
