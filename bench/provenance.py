from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT.parent / 'harness-bench'

def verify_reference():
    before = json.loads((ROOT / 'provenance/reference_before.json').read_text(encoding='utf-8'))
    now = {p.relative_to(REFERENCE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(REFERENCE.rglob('*')) if p.is_file()}
    differences = sorted(k for k in before.keys() | now.keys() if before.get(k) != now.get(k))
    result = {'reference_unchanged': not differences, 'files_hashed': len(now), 'differences': differences}
    (ROOT / 'provenance/reference_after.json').write_text(json.dumps(now, indent=2) + '\n', encoding='utf-8')
    if differences: raise RuntimeError(f'Reference integrity failure: {differences[:10]}')
    return result
