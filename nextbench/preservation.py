"""Read-only baseline/reference verification; save evidence in the new campaign."""
import hashlib
import json
import sqlite3
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from bench.durable import atomic_json, encode
from bench.extension import check_extension
from nextbench.scope import validate_scope

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while data := stream.read(1024 * 1024): value.update(data)
    return value.hexdigest()


def check(campaign):
    campaign = Path(campaign).resolve()
    if not campaign.is_relative_to(ROOT / 'campaigns') or campaign.name == 'shared':
        raise ValueError('Separate campaign evidence path required')
    scope = json.loads((campaign / 'config/report_scope.json').read_text())
    validate_scope(ROOT, scope)
    frozen = json.loads((ROOT / 'dataset/freeze.json').read_text())
    file_changes = [name for name, wanted in frozen['file_hashes'].items() if digest(ROOT / name) != wanted]
    reference = json.loads((ROOT / 'provenance/reference_before.json').read_text())
    reference_changes = [name for name, wanted in reference.items() if digest(ROOT.parent / 'harness-bench' / name) != wanted]
    primary = ROOT / 'results/journal.sqlite3'
    backup = campaign / 'preservation/baseline-journal.sqlite3'
    with closing(sqlite3.connect(primary.as_uri() + '?mode=ro',uri=True)) as old, closing(sqlite3.connect(backup.as_uri() + '?mode=ro',uri=True)) as saved:
        old.row_factory = sqlite3.Row
        rows = [dict(r) for r in old.execute('SELECT * FROM runs ORDER BY rowid')]
        same_tables = {}
        for table in ('runs','calls','forwards','events','slots','resources','metadata'):
            left = [tuple(r) for r in old.execute('SELECT * FROM ' + table + ' ORDER BY rowid')]
            right = saved.execute('SELECT * FROM ' + table + ' ORDER BY rowid').fetchall()
            same_tables[table] = left == right
    initial = check_extension(ROOT)
    report_validation = json.loads((ROOT / 'pdf/report_data/report_validation.json').read_text())
    records_digest = hashlib.sha256(encode(rows).encode()).hexdigest()
    pdf_digest = digest(ROOT / 'pdf/Indic_Harness_Bench_Experiment_Report.pdf')
    # Seal every preserved output file without reading its contents into logs.
    files = {p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT / 'results/runs').rglob('*')) if p.is_file()}
    atomic_json(campaign / 'preservation/baseline-output-files.json', files)
    checks = {'baseline_frozen_files_unchanged': not file_changes,
              'reference_files_unchanged': not reference_changes,
              'all_baseline_journal_tables_match_preparation_backup':all(same_tables.values()),
              'original_120_attempts_preserved':initial['passed'],
              'report_primary_record_fingerprint':records_digest == report_validation['primary_run_records_sha256'],
              'report_pdf_fingerprint':pdf_digest == report_validation['pdf_sha256'],
              'all_162_primary_conditions_terminal':len(rows) == 162 and not any(r['status'] in {'planned','running'} for r in rows)}
    report = {'passed':all(checks.values()), 'checks':checks, 'checked_utc':datetime.now(timezone.utc).isoformat(),
              'baseline_study_id':scope['baseline_study_id'], 'baseline_primary_records_sha256':records_digest,
              'baseline_primary_statuses':dict(Counter(r['status'] for r in rows)),
              'baseline_table_comparisons':same_tables, 'report_pdf_sha256':pdf_digest,
              'frozen_files_checked':len(frozen['file_hashes']), 'reference_files_checked':len(reference),
              'baseline_output_files_sealed':len(files), 'baseline_output_ledger_sha256':digest(campaign / 'preservation/baseline-output-files.json'),
              'baseline_backup_sha256':digest(backup), 'original_120_preservation':initial,
              'new_benchmark_attempts':0}
    atomic_json(campaign / 'preservation/verification.json', report)
    return report


if __name__ == '__main__':
    import sys
    value = check(sys.argv[1]); print(json.dumps(value))
    raise SystemExit(0 if value['passed'] else 1)
