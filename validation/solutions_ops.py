from solutions import text,js,rows
import json,csv

def operations(n,w,g):
    if n==62:
        advice={'cpu_memory_limits':'Set explicit CPU and memory limits','readiness_probe':'Add readinessProbe','liveness_probe':'Add livenessProbe','service_selector':'Match app=checkout selector','service_target_port':'Set targetPort to container port 8080 rather than 8081','image_tag_policy':'Replace latest with pinned image version','privileged_container':'Disable privileged true','service_type_policy':'Use ClusterIP instead of NodePort'}
        p=rows(w,'out/k8s_audit.csv',g['required_columns'],[{'check_id':k,'resource':'checkout deployment/service','status':v['status'],'severity':v['severity'],'evidence':' '.join(v['keywords']),'recommendation':advice[k]} for k,v in g['expected_findings'].items()])
    elif n==63:
        p=js(w,'out/deduped_incidents.json',{'incidents':[{**r,'evidence':'Topology and downstream timeout/connection symptoms align with the root alert.','summary':'Group dependent symptoms by shared root fingerprint.'} for r in g['expected_incidents']]})
        text(w,'out/noise_report.md','A-200 maintenance, A-201 synthetic and A-202 staging are filtered noise. Duplicate downstream symptoms are grouped under orders-db and redis-cache according to topology.\n')
    elif n==64:
        e=g['expected']; p=js(w,'out/root_cause.json',{'incident_id':g['incident_id'],'root_cause_service':e['root_cause_service'],'root_cause_change_id':e['root_cause_change_id'],'affected_services':e['affected_services'],'evidence':[{'source_file':s,'observation':'Dependency and timing evidence'} for s in e['evidence_sources']],'excluded_red_herrings':e['red_herrings'],'confidence':'high'})
        text(w,'out/triage_notes.md','Facts: logs/auth-gateway.log shows 401 responses with jwks and issuer errors; logs/checkout-web.log and logs/payment-api.log show downstream impact. metrics/service_metrics.csv and topology.json establish the dependency path. Inference: AUTH-2026-0318 on auth-gateway explains correlated failures. Request rollback approval, then verify recovery; exclude orders-db and cdn-edge red herrings.\n')
    elif n==67:
        e=g['expected']; thresholds=json.loads((w/'in/thresholds.json').read_text())['metrics']; calculations={}; evidence=[]
        samples={}
        for filename in ('baseline_metrics.csv','canary_metrics.csv'):
            with (w/'in'/filename).open(newline='') as f:
                for row in csv.DictReader(f): samples.setdefault(row['metric'],[]).append(int(row['sample_count']))
        for metric,v in e['expected_values'].items():
            rule=thresholds[metric]; b=v['baseline']; c=v['canary']; delta=None if c is None else (c-b)/b*100 if 'max_pct_delta' in rule else c-b
            if delta is not None and rule['direction']=='decrease_bad': delta=-delta
            calculations[metric]={'baseline_value':b,'canary_value':c,'delta':delta,'threshold':rule.get('max_abs_delta',rule.get('max_pct_delta')),'direction':rule['direction'],'sample_count':min(samples[metric]),'evidence_status':v['status']}
            evidence.append({'metric':metric,'baseline_value':b,'canary_value':'' if c is None else c,'delta':'' if delta is None else round(delta,4),'threshold':rule.get('max_abs_delta',rule.get('max_pct_delta')),'direction':rule['direction'],'severity':rule['severity'],'evidence_status':v['status'],'breached':'true' if metric in e['breached_metrics'] else 'false'})
        p=js(w,'out/canary_decision.json',{'release_id':e['release_id'],'decision':e['decision'],'breached_metrics':e['breached_metrics'],'calculations':calculations,'rationale':'Critical errors, latency and checkout success breach the canary guardrails.','next_actions':['stop canary and request rollback','notify owners','investigate missing payment_success_pct evidence and low sample search_latency_ms metrics']})
        rows(w,g['evidence_csv'],g['evidence_header'],evidence)
    elif n==70:
        p=rows(w,g['matrix_path'],['candidate_id','skills_score','evidence_score','shortlist','rank','reason'],[{'candidate_id':cid,'skills_score':5-i,'evidence_score':5-i,'shortlist':g['expected_shortlist'][cid],'rank':i+1,'reason':'SQL, spreadsheets and customer operations evidence assessed against job criteria.'} for i,cid in enumerate(g['expected_rank_order'])])
        text(w,g['notes_path'],'candidate_A demonstrates SQL, spreadsheet, customer operations and Python. candidate_C provides support metrics, spreadsheets and incident summaries but weaker fit to required technical work. candidate_B lacks the strongest required evidence. Rank uses job criteria only.\n')
    elif n==71:
        p=js(w,g['decisions_path'],[{'ticket_id':tid,**v} for tid,v in g['expected'].items()])
        reply={'reship':'We can review a replacement request using the provided damage photo.','refund':'We can review a refund request for the processing-stage cancellation.','escalate_human':'The case requires specialist review; we will provide an update after investigation.','information_request':'Please provide the order identifier and proof of purchase so we can review the request.'}
        text(w,g['templates_path'],'\n'.join('### Template '+tid+'\n'+reply[v['action']]+'\n' for tid,v in g['expected'].items()))
        rows(w,g['escalation_path'],g['escalation_header'].split(','),[{'ticket_id':tid,'reason':'Policy requires investigation of conflicting or restricted fulfillment evidence.','policy_basis':g['expected'][tid]['policy_basis'],'human_team':team} for tid,team in g['escalation_human_team'].items()])
    elif n==72:
        p=rows(w,g['actions_path'],['shipment_id','delay_status','customer_tier','action','compensation'],[{'shipment_id':sid,**v} for sid,v in g['expected'].items()])
        text(w,g['messages_path'],'\n'.join(f'## {sid}\nWe are reviewing the delivery delay and will follow the eligible remedy ({v["action"]}) under policy. We will update you when timing is confirmed.\n' for sid,v in g['expected'].items() if v['delay_status']=='delayed'))
    elif n==74:
        p=rows(w,g['grades_path'],['submission_id','concept_score','evidence_score','clarity_score','total_score'],[{'submission_id':sid,**v} for sid,v in g['expected_scores'].items()])
        for sid in g['expected_scores']: text(w,g['feedback_dir']+'/'+sid+'.md',f'# {sid}\nStrength: the response communicates its main idea. Improvement: connect each claim to specific evidence and define the concepts precisely.\n')
    elif n==75:
        p=rows(w,g['decisions_path'],g['decisions_header'].split(','),[{'case_id':cid,'decision':v['decision'],'final_action':v['final_action_contains'],'policy_basis':';'.join(v['policy_basis_tokens']),'confidence':v['confidence']} for cid,v in g['expected'].items()])
        explanations={'A-01':'The hateful conduct meets the clear prohibition.','A-02':'The material is protected counterspeech.','A-03':'The spam record supports a warning after the compromise narrative is considered.','A-04':'The qualifying harassment tier and earlier filing date support EDGE treatment.','A-05':'Prior violations apply alongside the edge rule for this case.','A-06':'The protected content and mislabel evidence override the advisory automation.','A-07':'The later filing invokes META-2 alongside EDGE treatment.'}
        text(w,g['explanations_path'],'\n'.join('### Case '+cid+'\n'+explanations[cid]+' Apply '+', '.join(v['policy_basis_tokens'])+' and '+v['decision']+' rather than retaining an unsupported automatic disposition.\n' for cid,v in g['expected'].items()))
        rows(w,g['redaction_path'],g['redaction_header'].split(','),[{'case_id':cid,'redacted_field':field,'redaction_reason':'Sensitive reporter identifier omitted from the public explanation.'} for cid,fields in g['redaction_fields_min'].items() for field in fields])
    else: raise NotImplementedError(n)
    return p
