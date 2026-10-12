"""Build thin campaign images from verified frozen local images without networking."""
import hashlib
import json
from pathlib import Path

from bench.durable import atomic_json
from bench.security import docker


def build(root, campaign):
    root, campaign = Path(root).resolve(), Path(campaign).resolve()
    baseline = json.loads((root / 'config/images.json').read_text(encoding='utf-8'))
    context = campaign / 'build-context'
    context.mkdir(parents=True, exist_ok=True)
    images = {role: dict(baseline[role]) for role in ('helper', 'grader')}
    for role in ('agent', 'relay'):
        pinned = baseline[role]['id']
        info = json.loads(docker(['image', 'inspect', pinned]))[0]
        if info['Id'] != pinned or info['Config']['User'] != '10001:10001':
            raise ValueError('Frozen base image identity/user mismatch')
        files = {role + '.py': root / 'nextbench/runtime' / (role + '.py')}
        if role == 'relay':
            files['contract.py'] = root / 'nextbench/contract.py'
        signature = hashlib.sha256(b''.join(p.read_bytes() for p in files.values())).hexdigest()[:12]
        base_tag = f'ihb-future-{role}-base:{pinned[7:19]}'
        docker(['image', 'tag', pinned, base_tag])
        for name, source in files.items():
            (context / name).write_bytes(source.read_bytes())
        dockerfile = context / ('Dockerfile.' + role)
        dockerfile.write_text('FROM ' + base_tag + '\n' + ''.join(
            'COPY ' + name + ' /opt/ihb/' + name + '\n' for name in files)
            + 'USER 10001:10001\n', encoding='utf-8')
        tag = f'ihb-{role}:nemotron-super-{signature}'
        docker(['build', '--network=none', '--pull=false', '-f', str(dockerfile), '-t', tag, str(context)], timeout=600)
        built = json.loads(docker(['image', 'inspect', tag]))[0]
        old_layers, new_layers = info['RootFS']['Layers'], built['RootFS']['Layers']
        if new_layers[:len(old_layers)] != old_layers or built['Config']['User'] != '10001:10001':
            raise ValueError('New image does not retain its pinned base layers/user')
        images[role] = {'id': built['Id'], 'tag': tag, 'base_id': pinned,
                        'source_sha256': {name: hashlib.sha256(source.read_bytes()).hexdigest() for name, source in files.items()}}
    atomic_json(campaign / 'config/images.json', images)
    return images
