"""Inspect the pinned container's installed OpenClaw code, with no model calls."""
import json,sys,uuid
from pathlib import Path
from contextlib import closing
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from bench.durable import Journal,atomic_json
from bench.lease import ControllerLease
from bench.security import docker
from nextbench.containers import CampaignContainers
CAMPAIGN=Path(__file__).resolve().parents[2]
dest=Path(__file__).parent/'idle-source';dest.mkdir(exist_ok=True)
code=r'''from pathlib import Path
import json
out=[]
for p in Path('/opt/openclaw/node_modules').rglob('*'):
 if p.suffix not in {'.js','.mjs'}: continue
 if not any(x in str(p) for x in ('openclaw/dist','pi-ai/dist','pi-coding-agent/dist')): continue
 text=p.read_text(errors='replace')
 for phrase in ('timeoutMs: number()', 'requestTimeoutMs =', 'requestTimeoutMs:', 'requestTimeoutMs'):
  if not any(x in p.name for x in ('model-', 'models-', 'zod-schema.core')): continue
  index=text.find(phrase)
  if index>=0: out.append({'path':str(p),'phrase':phrase,'context':text[max(0,index-1100):index+1600]})
print(json.dumps(out))
'''
with ControllerLease(ROOT/'results/controller.lock'),ControllerLease(CAMPAIGN/'results/controller.lock'),closing(Journal(dest/'journal.sqlite3')) as journal:
 box=CampaignContainers(journal,None,json.loads((CAMPAIGN/'config/images.json').read_text()))
 try:
  c=box.create('agent');data=json.loads(docker(['exec',c,'python','-c',code],timeout=120))
  atomic_json(dest/'findings.json',data);print(json.dumps(data))
 finally: box.cleanup()
