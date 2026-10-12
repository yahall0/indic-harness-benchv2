"""Read-only comparison of all pre-repair terminal records and run artifacts."""
import hashlib,json,sqlite3,sys
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from bench.durable import atomic_json,encode
CAMPAIGN=Path(__file__).resolve().parents[2]
SAVE=Path(__file__).with_name('before-transport-repair.json')

def rows(path):
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
        return [dict(r) for r in db.execute("SELECT * FROM runs WHERE status NOT IN ('planned','running') ORDER BY rowid")]

def capture():
    journals=[ROOT/'results/journal.sqlite3',CAMPAIGN/'results/journal.sqlite3']
    journals+=list((CAMPAIGN/'results/recoveries').glob('*/attempt-2/journal.sqlite3'))
    record={str(p):rows(p) for p in journals}
    artifacts={}
    for folder in (ROOT/'results/runs',ROOT/'results/infrastructure-retries',CAMPAIGN/'results/runs',CAMPAIGN/'results/recoveries'):
        for p in folder.rglob('*'):
            if p.is_file() and not p.name.startswith('journal') and 'checkpoints' not in p.parts:
                artifacts[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'terminal_records':record,'artifact_sha256':artifacts,
            'pdf_sha256':hashlib.sha256((ROOT/'pdf/Indic_Harness_Bench_Experiment_Report.pdf').read_bytes()).hexdigest()}

if sys.argv[1]=='capture':
    if SAVE.exists(): raise ValueError('Never overwrite pre-repair preservation evidence')
    value=capture();atomic_json(SAVE,value)
    print(json.dumps({'saved':True,'terminal_records':sum(map(len,value['terminal_records'].values())),'protected_artifacts':len(value['artifact_sha256'])}))
else:
    saved=json.loads(SAVE.read_text());passed=True
    for name,old in saved['terminal_records'].items():
        current={r['id']:r for r in rows(Path(name))}
        passed=passed and all(current.get(r['id'])==r for r in old)
    passed=passed and all(Path(name).is_file() and hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest for name,digest in saved['artifact_sha256'].items())
    passed=passed and saved['pdf_sha256']==hashlib.sha256((ROOT/'pdf/Indic_Harness_Bench_Experiment_Report.pdf').read_bytes()).hexdigest()
    report={'passed':passed,'old_terminal_records_unchanged':True if passed else False,'protected_artifacts':len(saved['artifact_sha256'])}
    atomic_json(SAVE.with_name('preservation-after-repair.json'),report);print(json.dumps(report));sys.exit(0 if passed else 1)
