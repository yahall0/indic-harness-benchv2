"""Trusted destructive-within-tmpfs probes. No model requests or task execution."""
import errno
import json
import os
import socket
import subprocess
import time
from pathlib import Path

checks = {}
checks['non_root'] = os.getuid() == 10001
status = Path('/proc/self/status').read_text()
checks['no_capabilities'] = 'CapEff:\t0000000000000000' in status
checks['no_new_privileges'] = 'NoNewPrivs:\t1' in status
checks['seccomp_filter'] = 'Seccomp:\t2' in status
try:
    Path('/etc/ihb-test-write').write_text('probe')
    checks['root_filesystem_readonly'] = False
except OSError as e:
    checks['root_filesystem_readonly'] = e.errno in (errno.EROFS, errno.EACCES)
checks['no_host_mounts_or_docker_interfaces'] = all(not Path(p).exists() for p in
    ['/mnt/c', '/host', '/var/run/docker.sock', '/run/docker.sock', '/opt/grader', '/opt/tasks',
     '/workspace/oracle_grade.py', '/workspace/ground_truth.json'])
checks['no_inference_credentials'] = not any(k.startswith('INDIC_OLLAMA_KEY') or k in
    ('OLLAMA_API_KEY', 'OPENAI_API_KEY') for k in os.environ)
checks['memory_limit'] = Path('/sys/fs/cgroup/memory.max').read_text().strip() == '3221225472'
checks['no_swap'] = Path('/sys/fs/cgroup/memory.swap.max').read_text().strip() == '0'
checks['pid_limit'] = Path('/sys/fs/cgroup/pids.max').read_text().strip() == '256'
checks['cpu_limit'] = Path('/sys/fs/cgroup/cpu.max').read_text().split() == ['200000', '100000']
fs = os.statvfs('/workspace')
checks['workspace_size_limit'] = fs.f_blocks * fs.f_frsize == 536870912
mountinfo = Path('/proc/self/mountinfo').read_text()
checks['workspace_is_tmpfs'] = any(' /workspace ' in x and ' - tmpfs ' in x for x in mountinfo.splitlines())
# Exercise storage exhaustion inside the disposable workspace, never on a host path.
try:
    with Path('/workspace/ihb-space-probe').open('wb') as f:
        block = b'x' * (1024 * 1024)
        for _ in range(514): f.write(block)
    checks['storage_exhaustion_contained'] = False
except OSError as e:
    checks['storage_exhaustion_contained'] = e.errno == errno.ENOSPC
finally:
    Path('/workspace/ihb-space-probe').unlink(missing_ok=True)
# Exercise the kernel PID limit without fork bombs or unbounded recursion.
children = []
try:
    for _ in range(260): children.append(subprocess.Popen(['sleep', '20']))
    checks['process_exhaustion_contained'] = False
except OSError as e:
    checks['process_exhaustion_contained'] = e.errno == errno.EAGAIN
finally:
    for child in children: child.terminate()
    for child in children: child.wait(timeout=5)
addresses = [('1.1.1.1', 443, 'public_ip'), ('8.8.8.8', 53, 'public_dns_tcp'),
             ('host.docker.internal', int(os.environ['IHB_CANARY_PORT']), 'host_canary'),
             ('host.docker.internal', 445, 'host_smb'), ('gateway.docker.internal', 2375, 'docker_api')]
for host, port, label in addresses:
    try:
        sock=socket.create_connection((host,port), timeout=1); sock.close()
        checks['blocked_' + label] = False
    except OSError:
        checks['blocked_' + label] = True
print(json.dumps({'checks': checks, 'passed': all(checks.values()), 'model_calls': 0}))
raise SystemExit(0 if all(checks.values()) else 1)
