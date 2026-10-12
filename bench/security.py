from __future__ import annotations
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

LABEL = 'org.indic-harness-bench.project'
LABEL_VALUE = 'indic-harness-bench-v1'
PREFIX = 'ihb-'
MAX_EXPORT_BYTES = 64 * 1024 * 1024
MAX_EXPORT_FILES = 4096

class SecurityError(RuntimeError):
    pass

def docker(args, *, timeout=60, input_bytes=None):
    # Never invoke a shell or accept command text from an agent.
    p = subprocess.run(['docker', *args], input=input_bytes, capture_output=True, timeout=timeout)
    if p.returncode:
        raise SecurityError(p.stderr.decode('utf-8', errors='replace')[-3000:])
    return p.stdout

def resource_name(name):
    if not re.fullmatch(r'ihb-[a-z0-9-]{1,80}', name):
        raise SecurityError('Invalid benchmark resource name')
    return name

def restricted_args(name, *, network='none', workspace_volume=None):
    resource_name(name)
    if network != 'none': resource_name(network)
    args = ['--name', name, '--label', f'{LABEL}={LABEL_VALUE}', '--init',
        '--user', '10001:10001', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges:true', '--network', network,
        '--cpus', '2', '--memory', '3g', '--memory-swap', '3g', '--pids-limit', '256',
        '--ulimit', 'nofile=1024:1024', '--log-driver', 'local',
        '--log-opt', 'max-size=5m', '--log-opt', 'max-file=2',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=67108864,uid=10001,gid=10001,mode=1777',
        '--tmpfs', '/home/bench:rw,nosuid,nodev,size=134217728,uid=10001,gid=10001,mode=700',
        '--env', 'HOME=/home/bench', '--env', 'PYTHONDONTWRITEBYTECODE=1',
        '--env', 'PYTHONUNBUFFERED=1', '--workdir', '/workspace']
    if workspace_volume:
        resource_name(workspace_volume)
        validate_volume(json.loads(docker(['volume', 'inspect', workspace_volume]))[0])
        args += ['--mount', f'type=volume,source={workspace_volume},target=/workspace,volume-nocopy']
    else:
        args += ['--tmpfs', '/workspace:rw,nosuid,nodev,size=536870912,uid=10001,gid=10001,mode=770']
    return args

def create_workspace_volume(name):
    resource_name(name)
    docker(['volume', 'create', '--label', f'{LABEL}={LABEL_VALUE}', '--driver', 'local',
            '--opt', 'type=tmpfs', '--opt', 'device=tmpfs', '--opt',
            'o=size=536870912,uid=10001,gid=10001,mode=0770,nosuid,nodev', name])
    validate_volume(json.loads(docker(['volume', 'inspect', name]))[0])

def validate_volume(v):
    if v.get('Labels', {}).get(LABEL) != LABEL_VALUE or v.get('Driver') != 'local':
        raise SecurityError('Unowned or unexpected workspace volume')
    options = v.get('Options') or {}
    if options.get('type') != 'tmpfs' or options.get('device') != 'tmpfs':
        raise SecurityError('Workspace must be tmpfs-backed; disk fallback prohibited')
    if options.get('o') != 'size=536870912,uid=10001,gid=10001,mode=0770,nosuid,nodev':
        raise SecurityError('Workspace size/ownership/options differ from protocol')

def create_internal_network(name):
    resource_name(name)
    docker(['network', 'create', '--internal', '--driver', 'bridge', '--label', f'{LABEL}={LABEL_VALUE}',
            '--opt', 'com.docker.network.bridge.gateway_mode_ipv4=isolated', name])
    validate_network(json.loads(docker(['network', 'inspect', name]))[0])

def validate_network(n):
    if n.get('Labels', {}).get(LABEL) != LABEL_VALUE or not n.get('Internal') or n.get('Driver') != 'bridge':
        raise SecurityError('Network must be an owned internal bridge')
    if n.get('Options', {}).get('com.docker.network.bridge.gateway_mode_ipv4') != 'isolated':
        raise SecurityError('Internal bridge must have isolated gateway mode')

def validate_container(c, *, network='none', workspace_volume=None, relay_internal_network=None):
    cfg, h = c['Config'], c['HostConfig']
    if cfg.get('Labels', {}).get(LABEL) != LABEL_VALUE:
        raise SecurityError('Container ownership label mismatch')
    expected = {'ReadonlyRootfs': True, 'Privileged': False, 'Memory': 3221225472,
                'MemorySwap': 3221225472, 'NanoCpus': 2000000000, 'PidsLimit': 256,
                'NetworkMode': network, 'Init': True}
    for key, value in expected.items():
        if h.get(key) != value: raise SecurityError(f'Unexpected {key}: {h.get(key)!r}')
    if cfg.get('User') != '10001:10001': raise SecurityError('Agent UID/GID must be non-root')
    if set(h.get('CapDrop') or []) != {'ALL'} or h.get('CapAdd'):
        raise SecurityError('All capabilities must be dropped')
    opts = h.get('SecurityOpt') or []
    if not any(x in ('no-new-privileges', 'no-new-privileges:true') for x in opts):
        raise SecurityError('no-new-privileges missing')
    if any('unconfined' in x for x in opts): raise SecurityError('Unconfined security profile prohibited')
    for key in ('Binds', 'Devices', 'DeviceRequests', 'PortBindings', 'VolumesFrom'):
        if h.get(key): raise SecurityError(f'{key} prohibited')
    for key in ('PidMode', 'IpcMode', 'UTSMode', 'CgroupnsMode'):
        if h.get(key) not in ('', 'private', None): raise SecurityError(f'Non-private {key} prohibited')
    attached=set((c.get('NetworkSettings') or {}).get('Networks') or {})
    expected_networks={network}
    if relay_internal_network:
        if network!='bridge' or workspace_volume: raise SecurityError('Invalid trusted relay topology')
        resource_name(relay_internal_network)
        validate_network(json.loads(docker(['network','inspect',relay_internal_network]))[0])
        expected_networks.add(relay_internal_network)
    if attached and attached != expected_networks: raise SecurityError('Additional network attachment prohibited')
    if cfg.get('Volumes'): raise SecurityError('Image declares unmanaged volumes')
    env = cfg.get('Env') or []
    if any(re.match(r'(?:INDIC_OLLAMA_KEY|OLLAMA_API_KEY|OPENAI_API_KEY|AWS_SECRET_ACCESS_KEY)', x) for x in env):
        raise SecurityError('Real credential variable visible to agent')
    if h.get('LogConfig', {}).get('Type') != 'local' or h.get('LogConfig', {}).get('Config') != {'max-file': '2', 'max-size': '5m'}:
        raise SecurityError('Bounded Docker logging required')
    tmpfs = h.get('Tmpfs') or {}
    required = {'/tmp': 67108864, '/home/bench': 134217728}
    if not workspace_volume: required['/workspace'] = 536870912
    if set(tmpfs) != set(required): raise SecurityError('Unexpected tmpfs mounts')
    for target, size in required.items():
        if f'size={size}' not in tmpfs[target] or 'nosuid' not in tmpfs[target] or 'nodev' not in tmpfs[target]:
            raise SecurityError('Unbounded or unsafe temporary filesystem')
    mounts = c.get('Mounts') or []
    volumes = [m for m in mounts if m['Type'] == 'volume']
    if workspace_volume:
        if len(volumes) != 1 or volumes[0].get('Name') != workspace_volume or volumes[0].get('Destination') != '/workspace':
            raise SecurityError('Unexpected volume exposure')
    elif volumes: raise SecurityError('Unexpected named volume')
    if any(m['Type'] not in ('tmpfs', 'volume') for m in mounts):
        raise SecurityError('Host or other filesystem mount prohibited')

def remove_owned(kind, name, *, expected_id=None):
    resource_name(name)
    if kind not in ('container', 'volume', 'network'): raise SecurityError('Unsupported resource kind')
    obj = json.loads(docker([kind, 'inspect', name]))[0]
    labels = obj.get('Config', {}).get('Labels') if kind == 'container' else obj.get('Labels')
    if (labels or {}).get(LABEL) != LABEL_VALUE: raise SecurityError('Refusing to remove unowned resource')
    identity=obj['Name'] if kind=='volume' else obj['Id']
    if expected_id and expected_id!=identity: raise SecurityError('Recorded resource identity mismatch')
    docker([kind, 'rm', *(['-f'] if kind == 'container' else []), identity])

def validated_archive(data):
    if len(data) > MAX_EXPORT_BYTES + 4 * 1024 * 1024: raise SecurityError('Export archive oversized')
    tar = tarfile.open(fileobj=io.BytesIO(data), mode='r:')
    members, seen, total = [], set(), 0
    for m in tar:
        if m.name in ('.','./') and m.isdir(): continue
        if m.name.startswith('./'): m.name=m.name[2:]
        name = m.name.rstrip('/')
        parts = PurePosixPath(name).parts
        if (not parts or name != '/'.join(parts) or name.startswith('/') or '\\' in name or '\x00' in name or
            any(p in ('.', '..') or any(c in p for c in ':<>"|?*') or any(ord(c)<32 for c in p) or p.endswith((' ', '.')) or
                re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p) for p in parts)):
            raise SecurityError('Unsafe export path')
        normalized = '/'.join(parts).casefold()
        if normalized in seen: raise SecurityError('Duplicate/case-colliding export path')
        seen.add(normalized)
        if not (m.isfile() or m.isdir()) or m.issparse(): raise SecurityError('Links/special/sparse files prohibited')
        total += m.size
        if total > MAX_EXPORT_BYTES or len(members) >= MAX_EXPORT_FILES: raise SecurityError('Export exceeds quota')
        members.append(m)
    files={m.name.casefold() for m in members if m.isfile()}
    for m in members:
        parts=PurePosixPath(m.name).parts
        if any('/'.join(parts[:i]).casefold() in files for i in range(1,len(parts))):
            raise SecurityError('Export parent is a file')
    return tar, members

def safe_export(data, destination):
    # Validate all headers before writing; never use extract()/extractall().
    dest = Path(destination)
    if dest.exists(): raise SecurityError('Export destination must be new')
    tar, members = validated_archive(data)
    ancestor = dest.absolute().parent
    while ancestor != ancestor.parent:
        if ancestor.is_symlink() or (hasattr(ancestor, 'is_junction') and ancestor.is_junction()):
            raise SecurityError('Export ancestor is a link/junction')
        ancestor = ancestor.parent
    dest.mkdir(parents=True)
    root = dest.resolve()
    for m in members:
        target = dest.joinpath(*PurePosixPath(m.name).parts)
        if not target.resolve().is_relative_to(root): raise SecurityError('Export escaped destination')
        if m.isdir(): target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = tar.extractfile(m)
            with target.open('xb') as out:
                remaining = m.size
                while remaining:
                    chunk = stream.read(min(65536, remaining))
                    if not chunk: raise SecurityError('Truncated export')
                    out.write(chunk); remaining -= len(chunk)
    tar.close()

def bounded_docker(args, *, max_bytes, timeout=60, input_bytes=None):
    """Bound untrusted output while reading it, before allocating the whole response."""
    import threading
    proc=subprocess.Popen(['docker',*args],stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    errors=[]
    def error_reader():
        total=0
        while True:
            b=proc.stderr.read(4096)
            if not b: break
            total+=len(b)
            if total>65536: proc.kill(); break
            errors.append(b)
        proc.stderr.close()
    error_thread=threading.Thread(target=error_reader,daemon=True); error_thread.start()
    chunks=[]; count=0; failure=[]
    def reader():
        nonlocal count
        try:
            while True:
                b=proc.stdout.read(65536)
                if not b: break
                count+=len(b)
                if count>max_bytes:
                    failure.append('Container output exceeds export/log limit'); proc.kill(); break
                chunks.append(b)
        finally: proc.stdout.close()
    thread=threading.Thread(target=reader,daemon=True); thread.start()
    try:
        if input_bytes is not None:
            proc.stdin.write(input_bytes); proc.stdin.close()
        rc=proc.wait(timeout=timeout); thread.join(5)
        if thread.is_alive(): raise SecurityError('Output stream did not close')
        error_thread.join(5)
        if failure or rc: raise SecurityError(failure[0] if failure else f'Docker operation failed ({rc}): '+b''.join(errors)[-3000:].decode('utf-8','replace'))
        return b''.join(chunks)
    finally:
        if proc.poll() is None: proc.kill(); proc.wait(5)

def workspace_archive(container):
    # Container must be paused/stopped by caller before snapshotting mutable agent files.
    data=bounded_docker(['cp',f'{container}:/workspace/.','-'],max_bytes=MAX_EXPORT_BYTES+4*1024*1024)
    tar,members=validated_archive(data)
    tar.close()
    return data
