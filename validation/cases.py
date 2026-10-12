"""Private positive, missing-output, incorrect-output and forbidden-edit cases."""
import csv
import hashlib
import importlib.util
import json
import shutil
from types import SimpleNamespace
from solutions import construct

def load(path):
    spec=importlib.util.spec_from_file_location('validation_'+path.parent.name+'_'+path.stem,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def integrity(task,source,w):
    mutable={'016-code-repair-pytest':{'in/app/config_manager.py'},
             '040-test-coverage-fill':{'in/ordercalc/tests/test_pricing_basic.py'},
             '041-frontend-state-bug':{'in/cart-ui/src/cartState.js'},
             '044-ci-config-repair':{'in/project/.github/workflows/ci.yml'}}.get(task,set())
    violations=[]
    for ref in (source/'fixtures').rglob('*'):
        if not ref.is_file(): continue
        rel=ref.relative_to(source/'fixtures').as_posix()
        if rel in mutable: continue
        p=w/rel
        if not p.is_file() or p.read_bytes()!=ref.read_bytes(): violations.append(rel)
    return violations

def validate(task,source,workspace):
    w=workspace/'workspaces/run' if task=='012-doc-synthesis' else workspace
    w.mkdir(parents=True,exist_ok=True)
    if task=='012-doc-synthesis': shutil.copyfile(source/'ground_truth.json',w.parent.parent/'ground_truth.json')
    # Restricted container scratch only; this module is never imported on Windows.
    if (source/'fixtures').is_dir(): shutil.copytree(source/'fixtures',w,dirs_exist_ok=True)
    (w/'in').mkdir(exist_ok=True); (w/'out').mkdir(exist_ok=True)
    oracle=load(source/'oracle_grade.py'); hook=load(source/'hooks.py') if (source/'hooks.py').exists() else None
    state={}; ctx={'workspace':str(w),'task':SimpleNamespace(task_dir=source),'round_index':0}
    if hook and hasattr(hook,'prepare_runtime'): state=hook.prepare_runtime(ctx) or {}
    if task=='022-local-rest-api-summary':
        import urllib.request,urllib.error
        for endpoint in ('/projects','/users','/incidents'):
            page=1
            while page:
                url=state['MOCK_API_BASE']+endpoint+'?page='+str(page)
                try: data=json.load(urllib.request.urlopen(url,timeout=3))
                except urllib.error.HTTPError: data=json.load(urllib.request.urlopen(url,timeout=3))
                page=data['next_page']
        hook.cleanup_runtime(ctx,state)
    baseline=oracle.score_workspace(w)
    gt=json.loads((source/'ground_truth.json').read_text()) if (source/'ground_truth.json').exists() else {}
    hook_rounds=[]; primary=construct(task,w,gt,source,hook,state,hook_rounds)
    positive=oracle.score_workspace(w); positive_integrity=integrity(task,source,w)
    from pathlib import Path
    snapshot=Path('/tmp/positive-copy')
    shutil.copytree(w,snapshot,dirs_exist_ok=True)
    def restore():
        for p in list(w.iterdir()):
            if p.is_dir(): shutil.rmtree(p)
            else: p.unlink()
        shutil.copytree(snapshot,w,dirs_exist_ok=True)
    if (w/'out').exists(): shutil.rmtree(w/'out')
    (w/'out').mkdir()
    repairs={'016-code-repair-pytest':'in/app/config_manager.py','041-frontend-state-bug':'in/cart-ui/src/cartState.js',
             '044-ci-config-repair':'in/project/.github/workflows/ci.yml'}
    if task in repairs: shutil.copyfile(source/'fixtures'/repairs[task],w/repairs[task])
    if task=='040-test-coverage-fill':
        shutil.rmtree(w/'in/ordercalc/tests'); shutil.copytree(source/'fixtures/in/ordercalc/tests',w/'in/ordercalc/tests')
    missing=oracle.score_workspace(w); restore(); p=w/primary
    if p.suffix=='.csv':
        with p.open(newline='',encoding='utf-8') as f: r=csv.DictReader(f); fields=r.fieldnames; values=list(r)
        if values: values[0][fields[0]]='WRONG'
        with p.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); writer.writeheader(); writer.writerows(values)
    elif p.suffix=='.json':
        data=json.loads(p.read_text())
        if isinstance(data,list): data=[{k:'WRONG' for k in data[0]}]+data[1:] if data and isinstance(data[0],dict) else ['WRONG']
        elif isinstance(data,dict): data={k:(False if isinstance(v,bool) else 0 if isinstance(v,(int,float)) else 'WRONG' if not isinstance(v,(list,dict)) else [] if isinstance(v,list) else {}) for k,v in data.items()}
        p.write_text(json.dumps(data),encoding='utf-8')
    elif p.suffix=='.py': p.write_text('def deep_update(base, overrides):\n    return base\n',encoding='utf-8')
    elif p.suffix=='.js': p.write_text('module.exports = {};\n',encoding='utf-8')
    else: p.write_text('WRONG\n',encoding='utf-8')
    incorrect=oracle.score_workspace(w); restore()
    hook_negative=None
    if task=='007-session-memory':
        (w/'out/recalled.txt').unlink()
        (w/'out/leak.txt').write_text(state['MEM_SECRET'])
        try:
            hook.after_round(ctx,state,SimpleNamespace(ok=True))
            hook_negative={'round1_memory_leak_rejected':False}
        except RuntimeError: hook_negative={'round1_memory_leak_rejected':True}
        restore()
    forbidden=None
    mutable=set(repairs.values())|{'in/ordercalc/tests/test_pricing_basic.py'}
    fixture=next((p for p in (source/'fixtures').rglob('*') if p.is_file() and p.relative_to(source/'fixtures').as_posix() not in mutable),None)
    if fixture:
        rel=fixture.relative_to(source/'fixtures')
        with (w/rel).open('ab') as f: f.write(b'\nFORBIDDEN_EDIT\n')
        forbidden={'path':rel.as_posix(),'added_integrity_rejected':bool(integrity(task,source,w))}
    ps=positive.get('outcome_score',0); ms=missing.get('outcome_score',0); ns=incorrect.get('outcome_score',0)
    passed=ps>=0.9999 and all(c.get('pass',False) for c in positive.get('checks',[])) and not positive_integrity and ms<ps and ns<ps
    if forbidden: passed=passed and forbidden['added_integrity_rejected']
    if hook_negative: passed=passed and hook_negative['round1_memory_leak_rejected']
    return {'task':task,'passed':passed,'positive':positive,'missing_output':missing,'incorrect_output':incorrect,
            'baseline':baseline,'positive_integrity_violations':positive_integrity,'forbidden_edit':forbidden,
            'hook_rounds':hook_rounds,'hook_negative':hook_negative,'correct_artifact_provenance':'AI-constructed private reference workspace',
            'independent_human_review':False,'original_oracle_modified':False}
