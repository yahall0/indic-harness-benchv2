"""Trusted host utilities; task code is never imported here."""
import hashlib, json, sqlite3
from contextlib import closing
from pathlib import Path
from bench.durable import atomic_json, encode

ROOT=Path(__file__).resolve().parents[1]
NEM=ROOT/'campaigns/nemotron-3-super-20261001'
SHARED=ROOT/'campaigns/shared/extension-to50-20261002'
TASKS=['056-inventory-forecast','073-research-repro-package','089-ab-test-caveat-analysis','106-release-approval-gate-plan']
LABEL='extension-to50-20261002'
MODELS={'oss':ROOT,'nemotron':NEM}
CONTRACT='\n\nBenchmark output contract: Write prose deliverables in English. Preserve the specified filenames, commands, identifiers, JSON keys, enum values, headings, and exact output strings.\n'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def readonly(p):
    db=sqlite3.connect(Path(p).resolve().as_uri()+'?mode=ro',uri=True); db.row_factory=sqlite3.Row; db.execute('PRAGMA query_only=ON'); db.execute('BEGIN'); return db
def db_digest(p):
    with closing(readonly(p)) as db:
        values={}
        for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            t=row[0]
            if not t.replace('_','').isalnum(): raise ValueError('Unexpected table')
            h=hashlib.sha256()
            for r in db.execute('SELECT * FROM "'+t+'" ORDER BY rowid'): h.update((encode(dict(r))+'\n').encode())
            values[t]=h.hexdigest()
        return values
def capture():
    path=SHARED/'preservation/before.json'
    if path.exists(): return verify_preserved()
    journals=[ROOT/'results/journal.sqlite3',NEM/'results/journal.sqlite3']
    for folder in [ROOT/'results/infrastructure-retries',NEM/'results/recoveries',NEM/'results/additional-recoveries']:
        journals.extend(p for p in folder.rglob('journal.sqlite3') if 'preservation' not in p.parts)
    files={}
    for folder in [ROOT/'vendor/harnessbench',ROOT.parent/'harness-bench',ROOT/'pdf',ROOT/'results/runs',ROOT/'results/infrastructure-retries',NEM/'results/runs',NEM/'results/recoveries',NEM/'results/additional-recoveries']:
        for p in folder.rglob('*'):
            if p.is_file() and not p.name.startswith('journal') and 'checkpoints' not in p.parts and 'preservation' not in p.parts: files[str(p)]=sha(p)
    for name,digest in read(ROOT/'dataset/freeze.json')['file_hashes'].items():
        p=ROOT/name
        if sha(p)!=digest: raise ValueError('Original baseline freeze changed: '+name)
        files[str(p)]=digest
    atomic_json(path,{'journals':{str(p):db_digest(p) for p in journals},'files':files})
    return verify_preserved()
def verify_preserved():
    old=read(SHARED/'preservation/before.json')
    return all(db_digest(p)==d for p,d in old['journals'].items()) and all(Path(p).is_file() and sha(p)==d for p,d in old['files'].items())
def source_hashes():
    files={}
    for folder in [ROOT/'extension50',SHARED/'input',SHARED/'config']:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.name!='freeze.json': files[str(p.relative_to(ROOT))]=sha(p)
    return files
