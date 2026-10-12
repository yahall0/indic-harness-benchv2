"""Fixed stdin round protocol. Entire OpenClaw, shell and descendants stay in Docker."""
import json
import os
import subprocess
import sys
from pathlib import Path

def main():
    os.environ.update(OPENCLAW_CONFIG_PATH='/home/bench/.openclaw/openclaw.json',
                      OPENCLAW_STATE_DIR='/home/bench/.openclaw',OPENCLAW_HOME='/home/bench/.openclaw',
                      WORKSPACE='/workspace',OPENCLAW_NO_AUTO_UPDATE='1')
    for line in sys.stdin:
        request=json.loads(line)
        if request['action']=='configure':
            p=Path('/home/bench/.openclaw/openclaw.json'); p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(request['config']),encoding='utf-8')
            os.environ.update(OPENCLAW_CONFIG_PATH=str(p),OPENCLAW_STATE_DIR=str(p.parent),
                              OPENCLAW_HOME=str(p.parent),WORKSPACE='/workspace',OPENCLAW_NO_AUTO_UPDATE='1')
            print(json.dumps({'configured':True}),flush=True)
        elif request['action']=='round':
            # No shell interpolation: the prompt is one literal argv element.
            cmd=['openclaw','agent','--local','--session-id',request['session'],
                 '--timeout',str(request['timeout']),'--thinking','medium','--json','--message',request['prompt']]
            try:
                proc=subprocess.run(cmd,cwd='/workspace',capture_output=True,timeout=request['timeout']+5)
                code,stdout,stderr=proc.returncode,proc.stdout,proc.stderr
            except subprocess.TimeoutExpired as e:
                code,stdout,stderr=124,e.stdout or b'',(e.stderr or b'')+b'\nBENCHMARK_ROUND_TIMEOUT\n'
            print(json.dumps({'round':request['round'],'returncode':code,
                'stdout':stdout[-2*1024*1024:].decode('utf-8','replace'),
                'stderr':stderr[-1024*1024:].decode('utf-8','replace'),
                'stdout_truncated':len(stdout)>2*1024*1024,'stderr_truncated':len(stderr)>1024*1024}),flush=True)
        elif request['action']=='snapshot_ready':
            print(json.dumps({'snapshot_ready':True}),flush=True)
        else: raise ValueError('Unknown controller action')

if __name__=='__main__': main()
