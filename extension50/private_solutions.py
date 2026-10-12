"""Private oracle validation workspaces. EXECUTE ONLY in the no-network grader."""
import csv, json, math, shutil
from old_solutions import construct as old_construct

def write_csv(w, name, fields, rows):
    with (w/'out'/name).open('w', encoding='utf-8', newline='') as f:
        d=csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); d.writeheader(); d.writerows(rows)

def construct(task,w,gt,source,hook,state,hook_rounds):
    if task=='056-inventory-forecast':
        write_csv(w,'reorder_plan.csv',gt['header'],gt['rows'])
        keys=['high_risk_skus','missing_history_skus','skipped_history_skus','medium_boundary_skus','more_than_one_pack_low_skus','pack_rounding_cases']
        (w/'out/inventory_exceptions.json').write_text(json.dumps({k:gt[k] for k in keys}))
        (w/'out/forecast_notes.md').write_text('14 day forecast, pack rounding up to multiple. High risk: '+', '.join(gt['high_risk_skus'])+'. Missing history SKU-E. Skipped unknown SKU-Z.')
        return 'out/reorder_plan.csv'
    if task=='073-research-repro-package':
        sections={
            'CLAIM-1':'Main findings cannot be reproduced: raw trials bundle is missing and analyze_main.py has a syntax error; results.csv alone does not provide raw evidence.',
            'CLAIM-2':'retention_lift mismatch: paper 0.038 versus results.csv 0.031. Cannot rerun the broken analyze_main.py or verify the difference without raw trials.',
            'CLAIM-3':'The supplied results.csv is only an aggregate; missing raw inputs and invalid analyze_main.py prevent checking this claim.',
            'CLAIM-4':'Appendix D results/subgroup_ablation.csv is absent; subgroup evidence cannot be checked.'}
        (w/'out/reproducibility_report.md').write_text('\n\n'.join('### Claim '+c+'\n'+t for c,t in sections.items()))
        rows=[dict(item='raw trial inputs',type='missing data',impact='Main claims unverified',recommended_fix='Supply raw bundle'),dict(item='analyze_main.py',type='syntax error',impact='Driver cannot run',recommended_fix='Repair syntax and document dependencies'),dict(item='retention_lift CLAIM-2',type='mismatch',impact='Paper and CSV disagree',recommended_fix='Reconcile values with source evidence'),dict(item='subgroup_ablation.csv Appendix D',type='missing artifact',impact='Subgroup claim unverified',recommended_fix='Supply subgroup table')]
        write_csv(w,'missing_steps.csv',['item','type','impact','recommended_fix'],rows)
        return 'out/missing_steps.csv'
    if task=='089-ab-test-caveat-analysis':
        vals=[('A',1200,96,6,14400),('B',1180,132,10,20592)]
        rows=[dict(variant=v,eligible_users=n,conversions=c,conversion_rate=f'{c/n:.4f}',refund_rate=f'{r/c:.4f}',revenue_per_eligible_user=f'{rev/n:.4f}') for v,n,c,r,rev in vals]
        write_csv(w,'variant_metrics.csv',list(rows[0]),rows)
        pa=96/1200; pb=132/1180; pooled=(96+132)/(1200+1180); z=(pb-pa)/math.sqrt(pooled*(1-pooled)*(1/1200+1/1180)); p=math.erfc(abs(z)/math.sqrt(2))
        (w/'out/ab_summary.json').write_text(json.dumps(dict(control_variant='A',treatment_variant='B',alpha=.05,lift_absolute=round(pb-pa,4),lift_relative=round((pb-pa)/pa,4),z_stat=round(z,4),p_value=round(p,4),significant=True,recommendation='launch with caveats')))
        shutil.copyfile(w/'in/exclusions.csv',w/'out/exclusion_ledger.csv')
        (w/'out/recommendation.md').write_text(f'Launch with caveats. Statistically significant two-sided result, p={p:.4f}; mobile cohort underpowered; duplicate assignment cleanup needs review.')
        return 'out/variant_metrics.csv'
    if task=='106-release-approval-gate-plan':
        actions=[f'Pending approval from {r}' for r in gt['required_approvals']]
        packet=dict(release_id=gt['release_id'],decision=gt['decision'],blocker_ids=list(gt['expected_blockers']),required_approvals=gt['required_approvals'],pending_actions=actions,evidence_refs=gt['audit_tokens'],not_executed_statement='No production operations executed; planning only; not executed.')
        (w/'out/approval_packet.json').write_text(json.dumps(packet))
        rows=[dict(blocker_id=k,severity=v['severity'],owner_role=v['owner_role'],evidence_ref='; '.join(gt['audit_tokens']),required_approval_or_action='Pending approval from '+v['owner_role'],rationale='; '.join(v['keywords'])) for k,v in gt['expected_blockers'].items()]
        write_csv(w,'blockers.csv',list(rows[0]),rows)
        (w/'out/pending_actions.md').write_text('Pending approval only.\n'+'\n'.join(r['blocker_id']+': '+r['required_approval_or_action'] for r in rows))
        (w/'out/audit_trail.md').write_text('Decision blocked. Local evidence: '+', '.join(gt['audit_tokens'])+'\n'+'\n'.join(r['blocker_id']+': '+r['rationale']+'; '+r['evidence_ref'] for r in rows))
        return 'out/approval_packet.json'
    return old_construct(task,w,gt,source,hook,state,hook_rounds)
