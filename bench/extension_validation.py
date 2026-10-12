"""Recheck the original 40 in the extended private grader without changing their records."""
import json
from bench.extension import ROOT,read,check_extension
from bench.containers import Containers
from bench.durable import atomic_json


def check_original_oracles():
    preservation=check_extension()
    ids=read(ROOT/'provenance/initial-40','dataset/freeze.json')['task_ids']
    directory=ROOT/'reports/extension_original_oracles';results=[];image=None
    for task in ids:
        box=Containers()
        try:
            image=box.images['grader']['id'];c=box.create('grader')
            result=box.invoke(c,{'action':'validate','task':task},timeout=240)
            result['grader_image']=image
        except Exception as e:
            result={'task':task,'passed':False,'error':str(e),'error_type':type(e).__name__,'grader_image':image}
        finally:box.cleanup()
        atomic_json(directory/(task+'.json'),result);results.append(result)
        print(json.dumps({'original_task':task,'compatible':result['passed']}),flush=True)
    report={'passed':all(r['passed'] for r in results),'tested':len(results),'grader_image':image,
        'failed_tasks':[r['task'] for r in results if not r['passed']],
        'original_reports_and_attempts_modified':False,'preservation':preservation,'cloud_requests':0}
    atomic_json(ROOT/'reports/extension_original_oracle_compatibility.json',report)
    return report


if __name__=='__main__':
    result=check_original_oracles();print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
