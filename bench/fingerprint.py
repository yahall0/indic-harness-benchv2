import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=['bench/controller.py','bench/collector.py','bench/containers.py','bench/durable.py','bench/lease.py',
       'bench/security.py','bench/openclaw_config.py','bench/rotation.py','bench/task_services.py',
       'runtime/agent.py','runtime/relay.py','runtime/grader.py','runtime/mock_api.py','config/protocol.json','config/images.json']
def runtime_fingerprint():
    parts={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}
    return hashlib.sha256(json.dumps(parts,sort_keys=True).encode()).hexdigest()
