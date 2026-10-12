"""Campaign-specific emergency stop: only recorded, ownership-verified containers."""
import argparse
import json
from contextlib import closing

from bench.durable import Journal, atomic_json
from bench.containers import emergency_stop
from nextbench.runner import campaign_path
from nextbench.recovery import _recovery_root


def stop(campaign):
    campaign = campaign_path(campaign)
    atomic_json(campaign / 'results/STOP_REQUESTED', {'operator_stop_requested': True})
    paths = [campaign / 'results/journal.sqlite3']; stopped = []
    with closing(Journal(paths[0])) as primary:
        tables = {r[0] for r in primary.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'recovery_attempts' in tables:
            paths.extend(_recovery_root(campaign, r['primary_run_id'], r['relative_root']) / 'journal.sqlite3'
                         for r in primary.db.execute('SELECT * FROM recovery_attempts'))
    for path in paths:
        if not path.exists(): continue
        with closing(Journal(path)) as journal:
            stopped.extend(emergency_stop(journal))
    return {'campaign': str(campaign), 'stopped_recorded_containers': stopped, 'further_admission_blocked': True}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('campaign'); args = parser.parse_args()
    print(json.dumps(stop(args.campaign)))


if __name__ == '__main__': main()
