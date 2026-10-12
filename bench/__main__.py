from __future__ import annotations
import argparse
import json
from pathlib import Path
from bench.provenance import verify_reference

def main():
    p=argparse.ArgumentParser(description='Indic Harness Bench controller; live start fails closed until validated and frozen.')
    p.add_argument('command',choices=['status','verify-reference','isolation-check','ready','freeze','extend-freeze','start','emergency-stop','backup','reactivate-slot'])
    p.add_argument('--slot',choices=['slot-1','slot-2','slot-3','slot-4'])
    p.add_argument('--allowance-reset-confirmed',action='store_true')
    args=p.parse_args()
    if args.command=='verify-reference': result=verify_reference()
    elif args.command=='isolation-check':
        from bench.isolation import check_isolation
        result=check_isolation()
    elif args.command=='ready':
        from bench.readiness import readiness
        result=readiness()
    elif args.command in ('freeze','extend-freeze'):
        from bench.readiness import freeze
        result=freeze(extend=args.command=='extend-freeze')
    elif args.command=='start':
        from bench.controller import start
        start(); result={'controller_finished':True}
    elif args.command in ('emergency-stop','backup','reactivate-slot'):
        from bench.durable import Journal
        from bench.containers import emergency_stop
        from bench.metrics import export
        root=Path(__file__).resolve().parents[1]; journal=Journal(root/'results/journal.sqlite3')
        try:
            if args.command=='emergency-stop': result={'stopped_recorded_containers':emergency_stop(journal)}
            elif args.command=='reactivate-slot':
                if not args.slot or not args.allowance_reset_confirmed: p.error('Supply --slot and --allowance-reset-confirmed after actual provider allowance reset')
                from bench.lease import ControllerLease
                with ControllerLease(root/'results/controller.lock'): journal.reactivate_slot(args.slot)
                result={'reactivated':args.slot}
            else:
                journal.export(root/'results/checkpoints/manual-backup')
                result=export(journal,root/'results/exports',json.loads((root/'dataset/task_manifest.json').read_text()))
        finally: journal.close()
    else:
        root=Path(__file__).resolve().parents[1]
        tasks=json.loads((root/'dataset/task_manifest.json').read_text(encoding='utf-8'))
        plan=json.loads((root/'dataset/pilot_plan.json').read_text(encoding='utf-8'))
        translated_files=list((root/'tasks').glob('*/prompts/hi/*.txt'))+list((root/'tasks').glob('*/prompts/hinglish/*.txt'))
        result={'tasks':len(tasks),'candidates':sum(t['status']=='candidate' for t in tasks),
                'excluded_or_deferred':sum(t['status']!='candidate' for t in tasks),
                'validated_triplets':sum(t['validation']['release_eligible'] for t in tasks),
                'translated_prompt_files':len(translated_files),'translations_started':bool(translated_files),
                'planned_runs':plan['planned_runs'],
                'pilot_started':bool(list((root/'results').glob('**/run.json'))),
                'next_action':'Follow the stage handoff; no live runs until all validation gates pass.'}
    print(json.dumps(result,indent=2))
    if args.command=='isolation-check' and not result['passed']: raise SystemExit(1)
    if args.command=='ready' and not result['ready']: raise SystemExit(1)

if __name__=='__main__': main()
