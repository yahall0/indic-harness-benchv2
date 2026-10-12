"""Trusted background reporting queue; it never starts any model or agent call."""
import os,subprocess,sys,time
from datetime import datetime,timezone
from extension50.common import SHARED,ROOT,read
from bench.durable import atomic_json
from bench.lease import ControllerLease

def now():return datetime.now(timezone.utc).isoformat()
def main():
    with ControllerLease(SHARED/'results/report_pipeline.lock'):
        record={'pid':os.getpid(),'module':'scripts.finish50','started_utc':now(),'state':'waiting_for_24_scored_additions','starts_model_calls':False}
        atomic_json(SHARED/'results/report_pipeline_process.json',record)
        while not (SHARED/'results/completion.json').exists():
            if (SHARED/'results/hold.json').exists():
                record.update(state='held_with_benchmark',finished_utc=now());atomic_json(SHARED/'results/report_pipeline_process.json',record);return
            time.sleep(30)
        done=read(SHARED/'results/completion.json')
        if not done.get('complete') or not done.get('preserved'):
            record.update(state='held_incomplete',finished_utc=now());atomic_json(SHARED/'results/report_pipeline_process.json',record);return
        record.update(state='building_report',build_started_utc=now());atomic_json(SHARED/'results/report_pipeline_process.json',record)
        with (SHARED/'results/report_pipeline.log').open('a',encoding='utf-8') as log:
            p=subprocess.Popen([sys.executable,'-B','-X','utf8','-m','scripts.report50'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            record['builder_pid']=p.pid;atomic_json(SHARED/'results/report_pipeline_process.json',record);code=p.wait()
        record.update(state='awaiting_visual_review' if code==0 else 'report_build_failed',returncode=code,finished_utc=now());atomic_json(SHARED/'results/report_pipeline_process.json',record)

if __name__=='__main__':main()
