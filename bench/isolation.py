from __future__ import annotations
import json
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from bench.security import (SecurityError, docker, create_workspace_volume, create_internal_network,
                            restricted_args, validate_container, remove_owned)

ROOT = Path(__file__).resolve().parents[1]
PROBE_IMAGE = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'

def check_isolation():
    server_info=json.loads(docker(['version', '--format', '{{json .}}']))
    if server_info.get('Server',{}).get('Os') != 'linux': raise SecurityError('Linux Docker engine required')
    suffix=uuid.uuid4().hex[:12]
    net, volume, container = ('ihb-probe-net-'+suffix, 'ihb-probe-work-'+suffix, 'ihb-probe-agent-'+suffix)
    created=[]
    class Canary(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b'isolated-host-canary')
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Canary)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    result={'timestamp_utc':datetime.now(timezone.utc).isoformat(), 'passed':False,
            'scope':'Docker boundary probes only; OpenClaw integration, relay and graders are not yet validated',
            'probe_image':PROBE_IMAGE, 'docker_version':server_info.get('Server',{}).get('Version'),
            'model_calls':0, 'cleanup_errors':[]}
    try:
        # Positive control: prove that the benign host canary is reachable from
        # an ordinary Docker bridge. Otherwise a failed isolated connection
        # would not establish that the network boundary blocked it.
        control='ihb-probe-control-'+suffix
        control_args=restricted_args(control)
        control_args[control_args.index('--network')+1]='bridge'
        docker(['create',*control_args,PROBE_IMAGE,'sleep','90'])
        created.append(('container',control))
        docker(['start',control])
        canary_code=(f'import socket; s=socket.create_connection(("host.docker.internal", {server.server_port}),timeout=3); '
                     's.sendall(b"GET / HTTP/1.0\\r\\nHost: canary\\r\\n\\r\\n"); '
                     'assert b"200" in s.recv(1024); s.close(); print("reachable")')
        result['host_canary_positive_control']=docker(['exec',control,'python','-c',canary_code]).strip()==b'reachable'
        if not result['host_canary_positive_control']: raise SecurityError('Host canary positive control failed')
        remove_owned('container',control); created.remove(('container',control))
        create_internal_network(net); created.append(('network',net))
        create_workspace_volume(volume); created.append(('volume',volume))
        args=['create', *restricted_args(container,network=net,workspace_volume=volume),
              '--env', f'IHB_CANARY_PORT={server.server_port}', PROBE_IMAGE, 'sleep','600']
        docker(args); created.append(('container',container))
        inspected=json.loads(docker(['container','inspect',container]))[0]
        validate_container(inspected,network=net,workspace_volume=volume)
        docker(['start',container])
        probe=(ROOT/'runtime/isolation_probe.py').read_bytes()
        # This script is trusted controller code, not agent-generated text.
        p=docker(['exec','-i',container,'python','-'], input_bytes=probe,timeout=90)
        result.update(json.loads(p))
        result['configuration_inspection_passed']=True
    except Exception as e:
        result['error']=str(e)
    finally:
        for kind,name in reversed(created):
            try: remove_owned(kind,name)
            except Exception as e: result['cleanup_errors'].append(f'{kind} {name}: {e}')
        server.shutdown(); server.server_close()
        if result['cleanup_errors']: result['passed']=False
        target=ROOT/'reports/security_check.json'; target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
