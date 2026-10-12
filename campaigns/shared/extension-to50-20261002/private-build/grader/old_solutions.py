"""Private AI-constructed solutions; never included in agent images."""
import csv,json,re,subprocess
from types import SimpleNamespace

def text(w,name,value):
    p=w/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(value,encoding='utf-8'); return name
def js(w,name,value): return text(w,name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def rows(w,name,header,values):
    p=w/name; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=header,lineterminator='\n',extrasaction='ignore'); wr.writeheader(); wr.writerows(values)
    return name
def quote(w,source,tokens):
    compact=lambda s: re.sub(r'[^a-z0-9]+','',s.lower())
    return ' '.join(l.strip() for l in (w/'in'/source).read_text().splitlines() if any(compact(t) in compact(l) for t in tokens))

def construct(task,w,g,source,hook,state,hook_rounds):
    def after(index):
        if hook and hasattr(hook,'after_round'):
            hook.after_round({'workspace':str(w),'task':SimpleNamespace(task_dir=source),'round_index':index},state,SimpleNamespace(ok=True))
        hook_rounds.append({'round':index+1,'after_round':'passed' if hook else 'not_applicable'})
    n=int(task[:3]); p=None
    if n in (28,32,37,44,48,54,55,65,66,68,79,80,96,103):
        from solutions_extension import construct_extension
        p=construct_extension(n,w,g,after)
        if n!=103: after(0)
        return p
    if n==1: p=text(w,'out/linecount.txt','4\n')
    elif n==2:
        subprocess.run(['sh','-c',"mkdir -p out/a/b; touch out/a/b/c.txt; echo $((6*7)) > out/step1.txt; basename out/a/b/c.txt > out/step2.txt; printf 'HELLO\\n' | tr '[:upper:]' '[:lower:]' > out/step3.txt"],cwd=w,check=True); p='out/step1.txt'
    elif n==4:
        p=text(w,g['summary_path'],'The Q2 OpenClaw discussion aligned the M1 milestone with a constrained budget and a staged rollout. The gateway remains a central dependency: its interfaces need verification before the team commits to later milestones. Participants discussed resource allocation and identified delivery risk where unresolved technical work could affect the schedule.\n\nThe agreed action is to clarify ownership, track open issues and check readiness against the milestone plan. Follow-ups should address the gateway questions and report remaining risk so the next planning decision is grounded in implementation evidence. The discussion does not support expanding the scope beyond the budget or treating unresolved questions as completed work.\n')
    elif n==5:
        p=js(w,'out/triage.json',{k:{'label':v,'reason_short':'Spam solicitation' if v=='spam' else 'Response requested' if v=='needs_reply' else 'Informational'} for k,v in g['labels'].items()})
        text(w,'out/delete_ids.txt','\n'.join(g['delete_ids'])+'\n')
        text(w,'out/replies/002.txt','I am available today after 14:00. Would that work for you?\n')
        text(w,'out/replies/005.txt','I will review the requested material and send an update today.\n')
    elif n==7:
        text(w,'out/phase1_done.txt',g['phase1_done_exact']+'\n'); after(0)
        p=text(w,'out/recalled.txt',g['memory_secret']+'\n'); after(1); return p
    elif n==12:
        p=js(w,'out/trustworthiness.json',{k:{'score':v,'reason':'Authority, direct evidence and corroboration determine reliability.'} for k,v in g['expected_trust_scores'].items()})
        js(w,'out/contradictions.json',{'contradictions':g['key_contradictions']})
        text(w,'out/final_report.md','# Incident synthesis\n\nThe official statement is the most credible anchor for the timeline: discovery occurred on March 14, with publication on March 16. News reporting and social media describe related events but do not establish the same sequence consistently. The event-date contradiction should be resolved by distinguishing discovery from publication rather than choosing an unverified post.\n\nAffected-user figures diverge widely across outlets. Expert analysis estimates approximately 100k users; this remains an estimate rather than a confirmed count. The news reports should be cited as competing accounts with uncertainty preserved. The evidence does not justify treating the highest circulated number as established fact.\n\nFor sensitive data, the official statement says no real PII was involved and mainly identifies test emails. Payment-card exposure is not confirmed. Social media assertions lack direct evidence sufficient to override the statement. A credible synthesis separates confirmed facts from allegations and identifies what would resolve the remaining contradiction.\n\nThe assessment gives greatest weight to the official statement and then expert analysis because their scope and evidence are more explicit. News reporting offers context, while social media has weaker verification. Further investigation should verify affected-user counts and sensitive-data claims against direct incident records. Uncertainty and the timeline must remain explicit in stakeholder communications. The report should be updated when new verifiable evidence becomes available rather than presenting unresolved claims as settled facts.\n')
    elif n==16:
        original=(w/'in/app/config_manager.py').read_text()
        replacement='if type(value) is dict and type(base_dict.get(key)) is dict:\n            deep_update(base_dict[key], value)\n        else:\n            base_dict[key] = value'
        p=text(w,'in/app/config_manager.py',original.replace('base_dict[key] = value',replacement))
        text(w,'out/progress.md','Ran the test suite, identified shallow replacement in deep_update, implemented recursive nested merging, and re-ran pytest without changing test_config.py.\n')
    elif n==17:
        h=['Source_A','Source_B','Config_Key','Value_A','Value_B','Issue_Type']; v=[]
        for k,a,b in [('max_db_connections','500','200'),('api_rate_limit','100','500'),('worker_timeout','30','120'),('db_connection_pool_size','150','300'),('log_level','INFO','WARN')]: v.append(dict(zip(h,['db_global','deployment_guide',k,a,b,'config_mismatch'])))
        v.append(dict(zip(h,['db_global','configmap_production','session_timeout_min','15','30','env_override_mismatch'])))
        for node in ['web-01','web-02']: v.append(dict(zip(h,['db_cluster_nodes','deployment_guide',node+'.cpu_cores','8','4','hardware_mismatch'])))
        for node in ['db-replica-01','worker-01']: v.append(dict(zip(h,['db_cluster_nodes','deployment_guide',node+'.region','us-west-2','us-east-1','region_mismatch'])))
        p=rows(w,'out/audit_report.csv',h,v)
        text(w,'out/progress.md','Parsed backup.sql and deployment_guide, checked environment.yml and node_inventory, and produced audit_report. Production session timeout differs from the global value. Staging overrides and DB/inventory agreement create no conflict.\n')
    elif n==19:
        e=g['expected']; timeline=[json.loads(l) for l in (w/'in/alerts.jsonl').read_text().splitlines() if l.strip()]
        p=js(w,'out/incident_report.json',{'incident_id':g['incident_id'],'severity':e['severity'],'root_cause_service':e['root_cause_service'],'primary_change_id':e['primary_change_id'],'blast_radius':'APAC checkout, cart, inventory and payment dependency symptoms','timeline':timeline,'evidence':[{'source_file':s,'finding':'Corroborates change, topology and alert ordering'} for s in g['evidence_required_sources']+['alerts.jsonl']],'recommended_actions':['request approval for rollback','verify recovery metrics','monitor downstream services'],'approval_required_actions':['production rollback'],'stakeholder_messages':{'customer_support':'APAC checkout affected; update follows verification','engineering_manager':'Investigate CHG-8842 on inventory-api'}})
        text(w,'out/rollback_plan.md','First request approval, then execute the production change. Roll back CHG-8842 for inventory-api after approval. Verification metrics cover checkout success and inventory errors. Stop conditions include worsening errors or unsafe state. Rollback trigger conditions require corroborated degradation. Monitor before declaring recovery.\n')
        rows(w,'out/evidence_matrix.csv',['claim','source_file','evidence','confidence'],[{'claim':'Inventory deployment precedes checkout degradation','source_file':s,'evidence':'Corroborating change, topology or alert record','confidence':'high'} for s in g['evidence_required_sources']]+[{'claim':'Inventory error alerts precede downstream payment symptoms','source_file':'alerts.jsonl','evidence':json.dumps(timeline[0]),'confidence':'high'},{'claim':'Downstream impact requires recovery verification','source_file':'alerts.jsonl','evidence':json.dumps(timeline[-1]),'confidence':'high'}])
        text(w,'out/status_update.md','Impact scope: APAC checkout and inventory dependency degradation (SEV2). Current handling status: investigating inventory-api and requesting approval. Next steps: verify recovery and monitor payment/cart symptoms. Estimated update time: after the next verification checkpoint.\n')
    elif n==20:
        p=js(w,'out/manifest.json',{'files':sorted(g['manifest_files'],key=lambda x:(x['archive'],x['path']))}); text(w,'out/mismatches.txt','\n'.join(g['mismatches'])+'\n')
    elif n==21:
        for path,value in g['outputs'].items(): text(w,path,value) if isinstance(value,str) else js(w,path,value)
        p=rows(w,'out/rename_log.csv',['source','target','action'],g['rename_log_rows'])
        rows(w,'out/error_report.csv',['source','row_or_record','error_type','details'],[{**r,'details':'Input violates conversion rule; source preserved.'} for r in g['error_rows']])
    elif n==22:
        p=js(w,'out/api_summary.json',{'source_base_url':'http://127.0.0.1:8081',**{k:g[k] for k in ['project_count','active_budget_usd','open_incidents','projects']}})
        text(w,'out/data_quality_report.md','Deduplicated duplicate p-300 records. Missing owner u-404 remains null; orphan p-999 incidents count globally but not per listed project. Retried 429 and 503 and followed pagination.\n')
    elif n==24:
        p=js(w,'out/proposed_slots.json',{'slots':[{**s,'timezone':'America/New_York','participants':g['required_participants'],'rationale':'All required calendars admit this interval.'} for s in g['allowed_slots']]})
        text(w,'out/invite_draft.txt','Please confirm availability. '+' '.join(g['invite_must_contain'])+'. These draft options require participant confirmation.\n')
    elif n==25:
        p=rows(w,'out/action_items.csv',['action_id','owner','task','deadline','status','source'],[{**r,'task':r['task_contains'],'source':r['source_matches'][0]} for r in g['expected_actions']])
        text(w,'out/owner_followups.md','\n'.join(f"## {r['owner']}\n{r['action_id']}: {r['task_contains']}; deadline {r['deadline']}; status {r['status']}." for r in g['expected_actions'])+'\nAT-106 is pending and blocked by a dependency.\n')
        text(w,'out/merge_rationale.md','AT-101 reassign follows followup emails and the latest transcript. AT-103 cancel remains in history. AT-104 deadline changed through a dependency. AT-105 complete is excluded. Jules rolling off caused bulk cancellation unless a later source explicitly took ownership. AT-106 remains pending and blocked. Sources: followup_emails.md, transcript_part3.txt, project_dependencies.json.\n')
    elif n==26:
        bullets=[['HelioDesk Q3 adds guided onboarding, policy-based admin controls and enterprise audit export.'],['Workspace administrators face setup friction and repetitive support tickets.'],['Guided onboarding, redesigned help panel, role templates, audit export and data retention settings.'],['Onboarding completion improvement: 28%.','Support ticket reduction: 17%.','Enterprise admins requesting controls: 64%.'],['Renewal expansion pipeline influenced: $1.8M; connect controls to regulated-account needs.'],['Review the approved release brief and align sales next steps with renewal expansion.']]
        refs=[[],[],[],['M-ONBOARD','M-TICKET','M-ADMIN'],['M-RENEW'],[]]
        p=js(w,'out/slides_outline.json',{'slides':[{'slide_number':i,'title':title,'bullets':bullets[i-1],'metric_refs':refs[i-1]} for i,title in enumerate(g['titles_in_order'],1)]})
        text(w,'out/speaker_notes.md','\n'.join(f'## Slide {i}: {title}\n'+ ' '.join(bullets[i-1]) for i,title in enumerate(g['titles_in_order'],1))+'\nFaster onboarding reduces setup friction. Lower ticket volume reflects the help panel. Enterprise controls support regulated accounts and renewal expansion. The $1.8M measure is influenced pipeline, without claiming guaranteed renewals.\n')
    elif n==27:
        contract=(w/'in/contract.md').read_text()
        risk_rows=[]
        for r in g['expected_risks']:
            clause=next(line for line in contract.splitlines() if line.startswith('Clause '+r['clause_id']))
            risk_rows.append({'clause_id':r['clause_id'],'risk_type':r['risk_type'],'quote':clause,'recommended_action':'Business review: negotiate '+r['action_contains']+' under company policy.','severity':'High' if r['risk_type'] in ('data residency','liability','security notice') else 'Medium'})
        p=rows(w,'out/risk_clauses.csv',['clause_id','risk_type','quote','recommended_action','severity'],risk_rows)
        text(w,'out/contract_summary.md','# Contract summary\n\nAcme Analytics provides analytics services to Baxter Retail. The initial term is 24 months and auto-renews for successive 12 month terms unless 30 days notice is given. Payment is net 60. Data may be held in any region; a security incident is reported within 10 business days. Liability is unlimited. Baxter termination for convenience requires 15 days notice; Acme may suspend for non-payment after 20 days. Publicity requires written approval.\n\n## Policy risks\n\nBusiness owners should review renewal notice against 60 days, seek a CFO payment exception or acceptable payment terms, restrict storage to approved regions, require 72 hours security notice, negotiate the liability cap and require 30 days termination notice. These are recommended business review actions.\n')
    elif n==33:
        p=js(w,'out/answers.json',[{'question_id':k,'answer':'insufficient_evidence' if v.get('insufficient') else ' '.join(v['facts']),'source_file':v.get('source_file',''),'quote_or_signal':'Missing finance approver signal' if v.get('insufficient') else quote(w,v['source_file'],v['quote_tokens'])} for k,v in g['answers'].items()])
    elif n==34:
        with (w/'in/claims.csv').open(newline='') as f: claims={r['claim_id']:r['claim'] for r in csv.DictReader(f)}
        p=rows(w,'out/evidence_matrix.csv',['claim_id','claim','classification','source_file','evidence_phrase'],[{'claim_id':k,'claim':claims[k],'classification':v['classification'],'source_file':v['source_file'],'evidence_phrase':quote(w,v['source_file'],v['tokens'])} for k,v in g['claims'].items()])
    else:
        from solutions_more import construct_more
        p=construct_more(n,w,g,source,after)
        if n in (57,58,59,60): return p
    after(0); return p
