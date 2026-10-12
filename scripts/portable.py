"""Read/check completed research on any OS without private journals or keys.

Standard library only. Never imports task modules, starts Docker or calls a model.
Historical controllers and evidence are intentionally left untouched.
"""
import argparse,csv,hashlib,json,math,statistics,sys
from collections import Counter
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
LANGS=('en','hi','hinglish');MODELS=('oss','nemotron')

def read(path):return json.loads(path.read_text(encoding='utf-8'))

def safe_path(root,name):
    path=PurePosixPath(name)
    if not name or '\\' in name or path.is_absolute() or '..' in path.parts or ':' in name:
        raise ValueError('Unsafe manifest path')
    result=root.joinpath(*path.parts).resolve()
    if not result.is_relative_to(root.resolve()):raise ValueError('Manifest path escapes repository')
    return result

def validate_rows(rows,expected_tasks=50):
    if len(rows)!=expected_tasks*6:raise ValueError('Unexpected condition count')
    seen=set();tasks=set();normalized=[]
    for row in rows:
        key=(row['model'],row['task_id'],row['language'])
        if key in seen:raise ValueError('Duplicate condition')
        if key[0] not in MODELS or key[2] not in LANGS:raise ValueError('Unknown model/language')
        if row['status'] not in ('completed','budget_exhausted','agent_failed','timeout','integrity_failed'):
            raise ValueError('Unscored infrastructure outcome in selected population')
        score=float(row['original_score']);full=float(row['full_completion'])
        if not math.isfinite(score) or not 0<=score<=1 or full not in (0,1):raise ValueError('Invalid score')
        seen.add(key);tasks.add(key[1]);normalized.append({**row,'original_score':score,'full_completion':int(full)})
    if len(tasks)!=expected_tasks or any((m,t,l) not in seen for t in tasks for m in MODELS for l in LANGS):
        raise ValueError('Incomplete matched task group')
    return normalized

def load_rows(root):
    with (root/'output/pdf/report_data/matched_conditions.csv').open(encoding='utf-8-sig',newline='') as f:
        return validate_rows(list(csv.DictReader(f)))

def summary(rows):
    means={};complete={}
    for model in MODELS:
        means[model]={};complete[model]={}
        for lang in LANGS:
            group=[r for r in rows if r['model']==model and r['language']==lang]
            means[model][lang]=statistics.mean(100*r['original_score'] for r in group)
            complete[model][lang]=sum(r['full_completion'] for r in group)
    return {'tasks':len({r['task_id'] for r in rows}),'scored_conditions':len(rows),
            'mean_scores_out_of_100':means,'strict_full_completions':complete,
            'overall_model_gain_pp':statistics.mean(means['nemotron'].values())-statistics.mean(means['oss'].values()),
            'model_calls':0,'journals_required':False}

def check(root):
    manifest=read(root/'publication/manifest.json');missing=[];changed=[]
    for name,digest in manifest['files'].items():
        path=safe_path(root,name)
        if not path.is_file():missing.append(name)
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=digest:changed.append(name)
    if missing or changed:
        raise ValueError(f'Published-file integrity failure: {len(missing)} missing, {len(changed)} changed; first: {(missing+changed)[:3]}')
    rows=load_rows(root);result=summary(rows);saved=read(root/'output/pdf/report_data/analysis_summary.json')
    for model in MODELS:
        for lang in LANGS:
            if abs(result['mean_scores_out_of_100'][model][lang]-saved['models'][model][lang]['mean_score'])>1e-8:
                raise ValueError('Published statistics disagree with saved conditions')
            if result['strict_full_completions'][model][lang]!=saved['models'][model][lang]['full_count']:
                raise ValueError('Completion count mismatch')
    for relative in ('dataset/freeze.json','campaigns/shared/extension-to50-20261002/config/freeze.json'):
        for name,digest in read(root/relative)['file_hashes'].items():
            path=safe_path(root,name.replace('\\','/'))
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('Frozen input changed: '+name)
    result.update(passed=True,published_files_verified=len(manifest['files']),frozen_input_bytes_verified=True)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('check','summary'))
    args=parser.parse_args()
    try:
        result=check(ROOT) if args.command=='check' else summary(load_rows(ROOT))
        print(json.dumps(result,indent=2))
    except (OSError,ValueError,KeyError) as e:
        parser.exit(1,str(e)+'\n')

if __name__=='__main__':main()
