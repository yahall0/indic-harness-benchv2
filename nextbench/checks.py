"""Record meaningful static checks and their exact implementation fingerprints."""
import argparse
import io
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bench.durable import atomic_json
from nextbench.runner import ROOT, campaign_path, hash_sources


def check(campaign):
    campaign = campaign_path(campaign)
    before = hash_sources()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests_nextbench'))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    passed = result.wasSuccessful() and before == hash_sources()
    path = campaign / 'checks/unit_tests.log'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(log.getvalue(),encoding='utf-8')
    report = {'passed':passed, 'tests_run':result.testsRun, 'failures':len(result.failures),
              'errors':len(result.errors), 'source_hashes':before,
              'checked_utc':datetime.now(timezone.utc).isoformat(),
              'benchmark_attempts':0, 'actual_cloud_requests':0}
    atomic_json(campaign / 'checks/unit_tests.json',report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('campaign',type=Path)
    args = parser.parse_args(); value = check(args.campaign)
    print(json.dumps({key:value[key] for key in ('passed','tests_run','failures','errors')}))
    raise SystemExit(0 if value['passed'] else 1)
