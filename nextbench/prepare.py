"""Create only the separately authorized Nemotron preparation configuration."""
import argparse
import hashlib
import json
import sqlite3
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from bench.durable import atomic_json, encode
from nextbench.scope import validate_scope


def metadata():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('https://ollama.com/api/tags', timeout=30) as response:
        tags = json.load(response)
    models = [m for m in tags['models'] if m['name'] in {'nemotron-3-nano:30b', 'nemotron-3-super', 'nemotron-3-ultra'}]
    details = {}
    for model in models:
        request = urllib.request.Request('https://ollama.com/api/show',
            json.dumps({'model': model['name']}).encode(), {'Content-Type': 'application/json'})
        with opener.open(request, timeout=30) as response:
            show = json.load(response)
        details[model['name']] = {k: show.get(k) for k in ('capabilities', 'thinking', 'details', 'model_info')}
    return {'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'tags': models, 'show': details,
            'sources': ['https://ollama.com/api/tags', 'https://ollama.com/api/show',
                        'https://ollama.com/pricing', 'https://docs.ollama.com/cloud',
                        'https://docs.ollama.com/api/openai-compatibility',
                        'https://docs.ollama.com/capabilities/thinking'],
            'published_rates_usd_per_million': {'nemotron-3-nano:30b': {'input': .06, 'output': .24},
                'nemotron-3-super': {'input': .015, 'output': .60},
                'nemotron-3-ultra': {'input': .10, 'output': 3.00}},
            'free_access_note': 'Starter credits and model eligibility are account-specific. Four keys do not prove independent allowances. No purchase or automatic billing action is authorized.'}


def prepare(root, campaign):
    root, campaign = Path(root).resolve(), Path(campaign).resolve()
    if not campaign.is_relative_to(root / 'campaigns') or campaign.name == 'shared':
        raise ValueError('Separate campaign directory required')
    if (campaign / 'config/protocol.json').exists():
        raise ValueError('Preparation configuration already exists; inspect rather than overwrite')
    scope = json.loads((root / 'campaigns/shared/report_matched_scope.json').read_text(encoding='utf-8'))
    validate_scope(root, scope)
    cloud = metadata()
    model = 'nemotron-3-super'
    show = cloud['show'][model]
    contexts = [v for k, v in show['model_info'].items() if k.endswith('.context_length')]
    if show['thinking'] != {'values': [False, True], 'default': True} or not {'completion', 'tools', 'thinking'} <= set(show['capabilities']):
        raise ValueError('Cloud capabilities differ from the recommended model decision')
    if len(contexts) != 1 or contexts[0] < 65536:
        raise ValueError('Provider context metadata is insufficient')
    profile = {'model': model, 'thinking': True, 'provider_reasoning_effort': 'high',
               'thinking_control_semantics': 'Documented OpenAI compatibility high alias maps to boolean true; no named high effort exists for this model.',
               'context_window': 65536, 'provider_context_window': contexts[0],
               'response_model_aliases': [model],
               'provider_advertised_digest': next(m['digest'] for m in cloud['tags'] if m['name'] == model),
               'provider_model_version_limit': 'Managed cloud weights cannot be cryptographically pinned by this client; advertised metadata and every reported response model are checked.'}
    protocol = json.loads((root / 'config/protocol.json').read_text(encoding='utf-8'))
    protocol.pop('reasoning_effort', None)
    protocol.update(model=model, protocol_revision=3, target_tasks=46, target_task_language_versions=138,
                    planned_runs=138, pilot_status='preparation_only', maximum_recovery_attempts=138,
                    maximum_total_attempts=276, free_credits_only=True,
                    max_campaign_input_allowance=55200000, max_campaign_output_allowance=4416000,
                    max_campaign_physical_transmissions=8280)
    probe = {'max_requests': 12, 'max_input_tokens': 200000, 'max_output_tokens': 16384,
             'max_response_tokens': 4096, 'attempt_timeout_sec': 900,
             'free_credits_only': True, 'benchmark_evidence': False, 'status': 'authorized_not_run'}
    analysis = {'scope_selection_id': scope['selection_id'], 'planned_original_tasks': 46,
                'main_outcome_view': 'sole_infrastructure_recovery_if_agent_outcome_else_primary',
                'required_sensitivity_view': 'primary_only', 'select_best_score': False,
                'budget_exhaustion_included': True,
                'complete_case_filter': 'Exclude a whole task if any selected language condition lacks a terminal scored agent outcome; show attrition from the fixed 46-task scope.',
                'bootstrap_unit': 'original task; keep all matched model/language conditions together',
                'bootstrap_samples': 10000, 'bootstrap_seed': 20260930,
                'baseline_report_unchanged': True, 'model_fallbacks': [], 'free_credit_purchases': False}
    authorization = {'user_instruction': "Do all that's recommended I cannot seem to answer questions rn as I'm on codex remote on my phone",
                     'accepted': ['Nemotron 3 Super', '12-transmission separate probe caps',
                                  'baseline per-attempt caps plus one eligible recovery',
                                  'free credits only; no purchases', 'recovery-inclusive and primary-only analyses'],
                     'benchmark_launch_authorized': False}
    for name, data in [('report_scope.json', scope), ('provider_metadata.json', cloud),
                       ('model_profile.json', profile), ('protocol.json', protocol),
                       ('probe_budget.json', probe), ('analysis_plan.json', analysis),
                       ('user_decisions.json', authorization)]:
        atomic_json(campaign / 'config' / name, data)
    preservation = campaign / 'preservation'
    preservation.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect((root / 'results/journal.sqlite3').as_uri() + '?mode=ro', uri=True)) as source:
        source.row_factory = sqlite3.Row
        source.execute('PRAGMA query_only=ON')
        with closing(sqlite3.connect(preservation / 'baseline-journal.sqlite3')) as target:
            source.backup(target)
        rows = [dict(r) for r in source.execute('SELECT * FROM runs ORDER BY rowid')]
    atomic_json(preservation / 'baseline-primary-records.json', rows)
    atomic_json(preservation / 'baseline-state.json', {
        'primary_records_sha256': hashlib.sha256(encode(rows).encode()).hexdigest(),
        'baseline_study_id': scope['baseline_study_id'], 'selection_id': scope['selection_id'],
        'new_cloud_inference_calls': 0, 'frozen_file_hashes': json.loads((root / 'dataset/freeze.json').read_text())['file_hashes']})
    return {'campaign': str(campaign), 'model': model, 'tasks': 46, 'primary_conditions': 138,
            'benchmark_launch_authorized': False, 'inference_calls': 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('campaign', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(Path(__file__).resolve().parents[1], args.campaign)))


if __name__ == '__main__':
    main()
