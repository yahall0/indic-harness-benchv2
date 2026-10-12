"""Read-only campaign scoreboard. No credentials, Docker operations or inference."""
import argparse
import json
import math
import sqlite3
import sys
import time
from collections import Counter
from contextlib import closing
from pathlib import Path


def read_database(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
        rows = [dict(r) for r in db.execute('SELECT * FROM runs ORDER BY rowid')]
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        retries = [dict(r) for r in db.execute('SELECT * FROM recovery_attempts')] if 'recovery_attempts' in tables else []
        slots = [dict(r) for r in db.execute('SELECT id,state FROM slots ORDER BY id')]
        last = db.execute('SELECT kind,payload FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        return rows, retries, slots, dict(last) if last else None


def snapshot(campaign):
    campaign = Path(campaign).resolve()
    rows, registry, slots, last = read_database(campaign / 'results/journal.sqlite3')
    retry_rows = {}
    for entry in registry:
        expected = 'recoveries/' + entry['primary_run_id'] + '/attempt-2'
        if entry['relative_root'] != expected:
            raise ValueError('Unexpected recovery path')
        path = (campaign / 'results' / expected / 'journal.sqlite3').resolve()
        if not path.is_relative_to(campaign): raise ValueError('Recovery path escaped campaign')
        if path.exists():
            children, _, _, _ = read_database(path)
            if len(children) != 1 or children[0]['id'] != entry['retry_run_id']:
                raise ValueError('Recovery journal mismatch')
            retry_rows[entry['primary_run_id']] = children[0]
    return {'primary': rows, 'recovery': retry_rows, 'slots': slots, 'last_event': last}


def label(row):
    if not row: return '-'
    if row['status'] == 'planned': return 'pending'
    if row['status'] == 'running': return 'RUNNING'
    value = json.loads(row['result'] or '{}')
    score = value.get('oracle', {}).get('outcome_score')
    valid = isinstance(score, (int, float)) and math.isfinite(score)
    return (f'{score:.2f} ' if valid else '') + {
        'completed': 'done', 'budget_exhausted': 'budget', 'infrastructure_failed': 'INFRA',
        'agent_failed': 'agentfail', 'integrity_failed': 'integrity', 'interrupted': 'interrupt',
        'quota_paused': 'QUOTA', 'timeout': 'timeout'}.get(row['status'], row['status'])


def render(campaign, data):
    states = Counter(r['status'] for r in data['primary'])
    recovery = data['recovery']; combined = data['primary'] + list(recovery.values())
    print('INDIC HARNESS BENCH — NEMOTRON 3 SUPER — READ-ONLY')
    print('46 fixed report tasks / 138 primary conditions; one eligible INFRA recovery')
    print(f"Primary terminal {138-states['planned']-states['running']}/138 | pending {states['planned']} | running {states['running']}")
    print(f"Recoveries {len(recovery)}/138 maximum | active {sum(r['status']=='running' for r in recovery.values())}")
    print('Known tokens across ALL attempts: ' + str(sum(r['input_actual'] for r in combined)) + '/' + str(sum(r['output_actual'] for r in combined)))
    print('Conservative charges: ' + str(sum(r['input_bound'] for r in combined)) + '/' + str(sum(r['output_reserved'] for r in combined)))
    print('Slots: ' + ' | '.join(s['id'] + '=' + s['state'] for s in data['slots']))
    if data['last_event']: print('Latest saved event: ' + data['last_event']['kind'])
    print('An isolated recoverable INFRA gets cooldown/recovery/continuation; critical failures or sustained outage pause.')
    print('Recovery outcomes are marked [R]; the primary record stays saved.')
    print('')
    print(f"{'Task':47} {'English':23} {'Hindi':23} Hinglish")
    groups = {}
    for row in data['primary']: groups.setdefault(row['task'], {})[row['language']] = row
    for task, languages in groups.items():
        cells = []
        for language in ('en', 'hi', 'hinglish'):
            row = languages.get(language); retry = recovery.get(row['id']) if row else None
            cells.append(label(retry) + ' [R]' if retry else label(row))
        print(f'{task:47} {cells[0]:23} {cells[1]:23} {cells[2]}')
    print('\nSaved outputs: ' + str(Path(campaign).resolve() / 'results/exports'))
    print('Ctrl+C closes this monitor only. Emergency stop: python -m nextbench.stop <campaign>')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('campaign', type=Path)
    parser.add_argument('--once', action='store_true'); args = parser.parse_args()
    while True:
        if not args.once and sys.stdout.isatty():
            print('\x1b[2J\x1b[H', end='')
        try: render(args.campaign, snapshot(args.campaign))
        except (OSError, ValueError, sqlite3.Error) as error:
            print('Read temporarily unavailable: ' + type(error).__name__)
        if args.once: return
        time.sleep(5)


if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: print('Monitor closed; controller is independent.')
