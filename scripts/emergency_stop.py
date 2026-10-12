"""Emergency stop works from any Windows working directory; only recorded Docker IDs."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bench.durable import Journal
from bench.containers import emergency_stop

if __name__=='__main__':
    paths=[ROOT/'results/journal.sqlite3']
    registry=ROOT/'results/infrastructure_retries.json'
    if registry.is_file():
        recovery=json.loads(registry.read_text(encoding='utf-8'))
        source=recovery['source_run_id']
        if not re.fullmatch('[a-f0-9]{24}',source):raise ValueError('Invalid recovery source ID')
        expected=(ROOT/'results/infrastructure-retries'/source/'attempt-2/journal.sqlite3').resolve()
        if Path(recovery['journal']).resolve()!=expected:raise ValueError('Unexpected recovery journal')
        if expected.is_file():paths.append(expected)
    stopped=[]
    for path in paths:
        journal=Journal(path)
        try:stopped.extend(emergency_stop(journal))
        finally:journal.close()
    print(json.dumps({'stopped_recorded_containers':stopped}))
