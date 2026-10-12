from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path
from bench.security import docker
from bench.durable import atomic_json

ROOT=Path(__file__).resolve().parents[1]

def build(targets=('agent','relay','helper','grader'),*,context_name='build-context',tag_suffix='2026.9.7'):
    if not context_name.replace('-','').isalnum() or not tag_suffix.replace('.','').replace('-','').isalnum():
        raise ValueError('Invalid fixed build context or tag suffix')
    context=ROOT/'work'/context_name
    context.mkdir(parents=True,exist_ok=True)
    for relative in ['docker/Dockerfile','runtime/agent.py','runtime/relay.py','runtime/mock_api.py','runtime/grader.py','bench/rotation.py','bench/__init__.py']:
        dst=context/relative; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/relative,dst)
    validation=context/'validation'; validation.mkdir(exist_ok=True)
    for p in (ROOT/'validation').glob('*.py'): shutil.copyfile(p,validation/p.name)
    manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text())
    for task in manifest:
        if not task['pilot_candidate']: continue
        source=ROOT/'vendor/harnessbench/tasks'/task['task_id']
        dest=context/'private_tasks'/task['task_id']
        shutil.copytree(source,dest,dirs_exist_ok=True)
        # The Windows checkout uses CRLF but source oracles embed Unix fixture hashes.
        # Normalize decodable text only in the PRIVATE build copy, preserving vendor/reference bytes.
        for fixture in (dest/'fixtures').rglob('*'):
            if not fixture.is_file(): continue
            b=fixture.read_bytes()
            try: b.decode('utf-8')
            except UnicodeDecodeError: continue
            if b'\x00' not in b: fixture.write_bytes(b.replace(b'\r\n',b'\n'))
    image_file=ROOT/'config/images.json'
    images=json.loads(image_file.read_text()) if image_file.exists() else {}
    for target in targets:
        tag=f'ihb-{target}:{tag_suffix}'
        docker(['build','--target',target,'-f',str(context/'docker/Dockerfile'),'-t',tag,str(context)],timeout=1800)
        info=json.loads(docker(['image','inspect',tag]))[0]
        images[target]={'id':info['Id'],'tag':tag}
        atomic_json(image_file,images)
        print(json.dumps({'built':target,'id':info['Id']}),flush=True)
    return images

if __name__=='__main__':
    import sys
    build(tuple(sys.argv[1:]) or ('agent','relay','helper','grader'))
