"""Read-only numerical, layout and preservation checks for the finished report.

No model requests or evaluated agent code run here. Visual review is recorded
separately after every rendered page has actually been inspected.
"""
import csv,json,statistics,sys
from collections import Counter
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tmp/pdf-report-deps'))
import pdfplumber
from extension50.common import ROOT,NEM,SHARED,LABEL,TASKS,read,readonly,sha,source_hashes,verify_preserved
from bench.durable import atomic_json

OUT=ROOT/'output/pdf/report_data'
PDF=ROOT/'output/pdf/Indic_Harness_Bench_50_Task_Combined_Report.pdf'
RENDERS=ROOT/'tmp/pdfs/report50-final-qa'

def validate():
    rows=list(csv.DictReader((OUT/'matched_conditions.csv').open(encoding='utf-8')))
    s=read(OUT/'analysis_summary.json')
    assert len(rows)==300 and len({r['task_id'] for r in rows})==50
    index={(r['model'],r['task_id'],r['language']):r for r in rows}
    assert len(index)==300
    checks={}
    for model in ['oss','nemotron']:
        for lang in ['en','hi','hinglish']:
            group=[r for r in rows if r['model']==model and r['language']==lang]
            assert len(group)==50
            mean=statistics.mean(100*float(r['original_score']) for r in group)
            full=sum(int(float(r['full_completion'])) for r in group)
            assert abs(mean-s['models'][model][lang]['mean_score'])<1e-9
            assert full==s['models'][model][lang]['full_count']
            checks[model+'_'+lang]={'n':50,'mean_score':mean,'strict_full_count':full}
    task_differences=[]
    for task in {r['task_id'] for r in rows}:
        task_differences.append(statistics.mean(
            100*(float(index['nemotron',task,lang]['original_score'])-float(index['oss',task,lang]['original_score']))
            for lang in ['en','hi','hinglish']))
    assert abs(statistics.mean(task_differences)-s['contrasts']['model_overall']['mean_difference_pp'])<1e-9
    batch={};ids=set()
    for model,origin in [('oss',ROOT),('nemotron',NEM)]:
        journal=origin/'results'/LABEL/'journal.sqlite3'
        with closing(readonly(journal)) as db:
            runs=[dict(r) for r in db.execute('SELECT * FROM runs')]
            assert len(runs)==12 and {r['task'] for r in runs}==set(TASKS)
            assert all(r['status'] in ['completed','budget_exhausted'] for r in runs)
            assert all(r['usage_missing']==0 for r in runs)
            assert all(r['input_bound']==r['input_actual'] and r['output_reserved']==r['output_actual'] for r in runs)
            assert db.execute("SELECT count(*) FROM resources WHERE status!='removed'").fetchone()[0]==0
            assert db.execute("SELECT count(*) FROM calls WHERE status='reserved'").fetchone()[0]==0
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert all(json.loads(r['result']).get('oracle',{}).get('outcome_score') is not None for r in runs)
            ids.update(r['id'] for r in runs)
            batch[model]={'runs':len(runs),'status_counts':dict(Counter(r['status'] for r in runs)),
                          'physical_transmissions':db.execute('SELECT count(*) FROM forwards').fetchone()[0],
                          'known_input':sum(r['input_actual'] for r in runs),
                          'known_output':sum(r['output_actual'] for r in runs),
                          'unsettled_calls':0,'live_recorded_resources':0,'integrity_check':'ok'}
    assert len(ids)==24
    progress=read(SHARED/'results/progress.json')
    for source,target in [('physical_transmissions','transmissions'),('known_input','known_input'),('known_output','known_output')]:
        assert sum(v[source] for v in batch.values())==progress['accounting'][target]
    assert progress['counts']['total_attempts']==24 and progress['counts']['resolved_conditions']==24
    freeze=read(SHARED/'config/freeze.json')
    assert source_hashes()==freeze['file_hashes']
    assert all(sha(p)==d for p,d in freeze['protected_runtime_hashes'].items())
    assert verify_preserved()
    pages=[]
    with pdfplumber.open(PDF) as pdf:
        assert len(pdf.pages)==18
        for i,page in enumerate(pdf.pages,1):
            text=page.extract_text() or ''
            words=page.extract_words()
            body=[w for w in words if 45<float(w['top'])<page.height-45]
            assert len(body)>=25,('blank or orphan page',i)
            assert all(20<=w['x0'] and w['x1']<=page.width-20 and w['top']>=0 and w['bottom']<=page.height for w in words),('page bounds',i)
            assert not any(token in text for token in ['TODO','TBD','PLACEHOLDER','\ufffd','\u25a0'])
            assert str(i)==text.splitlines()[-1].strip().split()[-1],('page number',i)
            image=RENDERS/f'page-{i:02d}.png'
            assert image.is_file()
            pages.append({'page':i,'body_words':len(body),'render_sha256':sha(image)})
    result={'passed':True,'checked_utc':datetime.now(timezone.utc).isoformat(),
            'pdf_sha256':sha(PDF),'pages':pages,'independent_csv_point_estimates':checks,
            'paired_task_mean_gain_pp':statistics.mean(task_differences),
            'new_journals':batch,'exactly_24_attempts_no_recoveries':True,
            'original_preservation_verified':True,'frozen_execution_unchanged':True,
            'all_new_resources_removed_and_calls_settled':True,
            'visual_review_pending':True}
    atomic_json(OUT/'final_quality_checks.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['pages','independent_csv_point_estimates']},indent=2))
    return result

if __name__=='__main__':validate()
