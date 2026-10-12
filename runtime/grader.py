"""Private original oracle/hook execution: container must have --network none."""
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

def load(path):
    spec=importlib.util.spec_from_file_location('ihb_'+path.stem,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def main():
    request=json.loads(sys.stdin.readline())
    task=request['task']
    if '/' in task or '\\' in task or '..' in task: raise ValueError('Task path')
    source=Path('/opt/ihb/tasks')/task; w=Path('/workspace')
    hook=load(source/'hooks.py') if (source/'hooks.py').exists() else None
    ctx={'workspace':str(w),'task':SimpleNamespace(task_dir=source),'round_index':request.get('round',0)}
    if request['action']=='prepare':
        if (source/'fixtures').is_dir(): shutil.copytree(source/'fixtures',w,dirs_exist_ok=True)
        (w/'in').mkdir(exist_ok=True); (w/'out').mkdir(exist_ok=True)
        state={}
        if hook and hasattr(hook,'prepare_runtime') and task!='022-local-rest-api-summary':
            state=hook.prepare_runtime(ctx) or {}
        # Preserve the original runner's behavior: task 017 setup/teardown are not called.
        if task=='022-local-rest-api-summary': state={'MOCK_API_BASE':'http://127.0.0.1:8081'}
        print(json.dumps({'state':state,'prepared':True}),flush=True)
    elif request['action']=='after_round':
        state=request.get('state',{})
        if hook and hasattr(hook,'after_round'):
            try: result=hook.after_round(ctx,state,SimpleNamespace(ok=request.get('ok',True)))
            except RuntimeError:
                if task!='007-session-memory': raise
                print(json.dumps({'state':state,'hook_ok':False,'integrity_violations':['round1_memory_secret_leak']}),flush=True)
                return
            if result is not None: state=result
        print(json.dumps({'state':state,'hook_ok':True}),flush=True)
    elif request['action']=='grade':
        if task=='012-doc-synthesis':
            children=list(w.iterdir()); nested=w/'workspaces/run'; nested.mkdir(parents=True)
            for child in children: shutil.move(str(child),str(nested/child.name))
            shutil.copyfile(source/'ground_truth.json',w/'ground_truth.json'); w=nested
        oracle=load(source/'oracle_grade.py'); result=oracle.score_workspace(w)
        sys.path.insert(0,'/opt/ihb/validation')
        from cases import integrity
        print(json.dumps({'oracle':result,'integrity_violations':integrity(task,source,w)},ensure_ascii=False),flush=True)
    elif request['action']=='validate':
        sys.path.insert(0,'/opt/ihb/validation')
        from cases import validate
        print(json.dumps(validate(task,source,w),ensure_ascii=False),flush=True)
    else: raise ValueError('Grader action')

if __name__=='__main__': main()
