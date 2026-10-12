from solutions import text,js,rows,quote
import json,shutil

def source_resolution(w,g):
    facts={k:v.get('value',' '.join(v.get('value_tokens',[]))) for k,v in g['resolved'].items()}
    facts['evidence']=[{'fact_key':k,'source_file':v['source_file'],'quote_or_signal':quote(w,v['source_file'],g['evidence_quote_terms'][k]),'priority_reason':'Higher authority and coverage_scope override lower-priority reporting; reject rumor for launch-day contract scope.'} for k,v in g['resolved'].items()]
    p=js(w,'out/resolved_facts.json',facts)
    text(w,'out/uncertainties.md','# Unconfirmed items\n\n'+'\n'.join('- '+s+': not established by the provided records.' for s in g['uncertainties'])+'\n')
    rows(w,'out/conflict_matrix.csv',g['conflict_matrix']['required_columns'],[{'fact_key':k,'winning_source':v['source_file'],'losing_sources':'press_release.md; social_digest.md','resolution_rationale':'Signed regulator defines launch and vendor; audited_finance_extract governs budget; operations_log governs customer count. Apply authority and scope to launch-day contract.','coverage_scope':'launch-day contract scope'} for k,v in g['resolved'].items()])
    order=['signed_regulator_notice','audited_finance_extract','operations_log','vendor_contract_addendum','press_release','social_digest']
    scopes=['Launch-day authorization, certified vendor and service scope','Approved budget','Recorded customer count','Contract-planned service; separate certification still required','Public announcement with lower priority','Unverified rumors with lowest priority']
    js(w,'out/source_reliability.json',[{'source_file':'briefs/'+name+'.md','priority_rank':i+1,'coverage_scope':scopes[i],
        'used_for':[k for k,v in g['resolved'].items() if name in v['source_file']],
        'rejected_claims':['Airport connector authorization at launch'] if i==3 else ['Conflicting launch date or budget'] if i==4 else ['Cancellation and vendor replacement rumors'] if i==5 else [],
        'reliability_note':'Apply the declared source priority only within coverage_scope; signed_regulator_notice overrides contract-planned launch authorization, audited_finance_extract controls budget, operations_log controls recorded count.'} for i,name in enumerate(order)])
    text(w,'out/decision_log.md','Use signed launch-day authority for contract and service scope. Reject low-priority rumor. The airport connector requires separate certification and remains outside launch authorization.\n')
    return p

def citations(w,g):
    values=[]
    for kind,keys in g['errors'].items():
        for key in keys:
            terms=g['evidence_span_terms'][kind+':'+key]
            values.append({'error_type':kind,'citation_key':key,'details':'Resolve against local draft and bibliography: '+'; '.join(terms),'evidence_span':'; '.join(terms),'expected_fix':'Correct key/metadata or remove orphan based on local evidence.'})
    p=rows(w,'out/citation_errors.csv',['error_type','citation_key','details','evidence_span','expected_fix'],values)
    old=json.loads((w/'in/bib.json').read_text()); bib={}
    if isinstance(old,dict): bib=old
    for key in g['corrected']['forbidden_keys']: bib.pop(key,None)
    for key in g['corrected']['required_keys']:
        exp=g['corrected']['field_expectations'].get(key,{})
        bib[key]={**(bib.get(key,{}) if isinstance(bib.get(key,{}),dict) else {}),**{k:v for k,v in exp.items() if k!='authors_contain'}}
        if 'authors_contain' in exp: bib[key]['authors']=exp['authors_contain']
        bib[key].setdefault('doi','UNKNOWN')
    js(w,'out/corrected_bib.json',bib)
    text(w,'out/audit_notes.md','No external sources were used. UNKNOWN marks fields lacking local evidence. Chen entries become 2024a and 2024b; unsupported Rao is omitted. All repairs use draft and bibliography evidence.\n')
    js(w,'out/citation_graph.json',{'in_text_citations':g['corrected']['required_keys'],'bibliography_entries':g['corrected']['required_keys'],'key_renames':{'Lin2022':'Lin2023','Ortega2018':'Ortega2020','Chen2024':['Chen2024a','Chen2024b']},'removed':g['corrected']['forbidden_keys'],'renamed':['Lin2023','Ortega2020','Chen2024a','Chen2024b']})
    return p

def architecture(w,g):
    p=js(w,'out/module_map.json',{'modules':[{'name':m,'path':m.replace('.','/')+'.py','purpose':'Runtime application module'} for m in g['expected_modules']],
        'entry_points':g['expected_entry_points'],'dependency_edges':[{'from':e['from'],'to':e['to'],'type':t} for e in g['expected_typed_edges'] for t in e['types']],
        'key_functions':g['expected_functions'],'runtime_flows':['cli -> load_settings -> init_schema','POST /orders -> create_order -> repo.save -> order_event']})
    text(w,'out/architecture.md','# Architecture\n\nThe CLI entry point loads settings and initializes SQLite through OrderRepository. register_routes binds API paths to create_order and retrieval handlers. The data flow reaches storage, while the runtime flow emits audit events after persistence.\n')
    rows(w,'out/doc_code_discrepancies.csv',g['discrepancy_required_columns'],[
        {'claim':'readonly storage','doc_source':'README.md','code_evidence':'repo.py writes to SQLite','assessment':'contradicted','risk':'Unexpected writes'},
        {'claim':'automatic retry','doc_source':'README.md','code_evidence':'repo.py has no retry loop','assessment':'contradicted','risk':'Failures propagate'},
        {'claim':'durable audit','doc_source':'README.md','code_evidence':'audit.py and handlers.py emit only available audit behavior','assessment':'contradicted','risk':'Unsupported audit guarantee'}])
    rows(w,'out/risk_register.csv',g['risk_register_required_columns'],[
        {'risk_id':'R1','area':'storage','evidence':'repo.py','impact':'Failed persistence','mitigation':'Test write failures','owner_hint':'storage'},
        {'risk_id':'R2','area':'audit','evidence':'audit.py','impact':'Missing trail','mitigation':'Verify event durability','owner_hint':'operations'},
        {'risk_id':'R3','area':'config and validation','evidence':'handlers.py','impact':'Invalid requests','mitigation':'Check inputs and config defaults','owner_hint':'API'},
        {'risk_id':'R4','area':'configuration','evidence':'config.py','impact':'Unexpected storage location from defaults','mitigation':'Test explicit settings before writes','owner_hint':'operations'}])
    text(w,'out/onboarding_plan.md','# Onboarding\n\nRead order: __init__ package markers, config, CLI, routes, handlers, storage and audit. Use local test runs before changes. A safe first edit is a focused test for validation. Debug the runtime with a breakpoint in create_order. Run `python -m pytest` locally before reviewing the diff.\n')
    return p

def analysis(n,w,g):
    if n==49:
        p=rows(w,g['outputs']['cleaned_csv'],g['cleaned_header'],g['cleaned_rows'])
        rows(w,g['outputs']['reject_ledger'],g['reject_header'],[{**r,'notes':'Rejected under the declared cleaning precedence.'} for r in g['reject_rows']])
        js(w,g['outputs']['reject_summary'],g['reject_summary_expected'])
        text(w,g['outputs']['report'],'Valid row count: 13; rejected row count: 12. Reject categories are missing_amount, duplicate_order_id, inactive_customer, invalid_quantity, unknown_customer, invalid_date and unsupported_currency. Duplicate orders retain the first eligible occurrence. Locale parsing uses de_DE before fx conversion; failures are recorded by source row. Total amount USD: 4047.52.\n')
    elif n==50:
        p=rows(w,g['output'],g['header'],g['rows']); js(w,g['region_summary'],g['region_summary_expected']); js(w,g['audit'],g['audit_expected'])
        text(w,g['notes'],'Use captured payments, remove duplicate P5002-DUP and P5008-DUP, and exclude orphan P5007/P5013 on O9999. Cancelled O1003 has no revenue. Refund R9006 has no_captured_payment; chargeback CB7003/CB7004 cases are reconciled by captured payment. Canonical aliases C006, C007 and C010 are merged before customer and region aggregation.\n')
    elif n==51:
        p=js(w,g['outputs']['json'],g['query_results']); js(w,g['outputs']['audit'],g['query_audit'])
        text(w,g['outputs']['analysis'],'Atlas Laptop and Nova Monitor tie in revenue; break the tie by product_id. North has the strongest region revenue. Include paid orders from 2025-01-01 through 2025-03-31 inclusive. Returned O1010 and cancelled orders are excluded, as are dates 2024-12-31 and 2025-04-01 outside the window.\n')
    elif n==52:
        p=rows(w,g['output'],g['header'],g['rows']); js(w,g['equivalence_audit'],g['equivalence_audit_expected'])
    else:
        p=rows(w,g['outputs']['csv'],g['header'],[{**r,'reason':r['rule_id']+'; secondary rules: '+', '.join(g['secondary_rules'].get(r['transaction_id'],[]))} for r in g['rows']])
        js(w,g['outputs']['audit'],g['rule_audit_expected'])
        text(w,g['outputs']['notes'],'18 suspicious transactions. R1_HIGH_VALUE and R2_GEO_AMOUNT take precedence over medium risk R3_CARD_VELOCITY and R4_COUNTRY_MISMATCH. Velocity groups by card and inclusive timestamp windows, preserving out-of-order detection. Highest-risk ties follow the declared rule order and retain secondary rules.\n')
    return p

def multiround(n,w,g,after):
    if n==57:
        first={'completed_ids':g['completed_after_round1'],'pending_ids':['C-104','C-105'],'per_item_results':{k:{'risk_score':g['risk_scores'][k]} for k in g['completed_after_round1']},'processing_log':[{'id':k,'step':'round1','status':'completed'} for k in g['completed_after_round1']]}
        js(w,'out/state.json',first); after(0)
        state={**first,'completed_ids':g['completed_final'],'pending_ids':[],'per_item_results':{k:{'risk_score':v} for k,v in g['risk_scores'].items()},'processing_log':first['processing_log']+[{'id':k,'step':'skipped_preexisting','status':'reused'} for k in g['completed_after_round1']]+[{'id':k,'step':'round2','status':'completed'} for k in ['C-104','C-105']]}
        js(w,'out/state.json',state)
        p=js(w,'out/final_result.json',{'run_id':'resume-drill-74','resumed_from_state':True,'completed_ids':g['completed_final'],'escalations':g['escalations'],'monitor_ids':g['monitor_ids'],'aggregate_risk_score':g['aggregate_risk_score'],'resume_audit':{'skipped_preexisting_ids':g['completed_after_round1'],'newly_processed_ids':['C-104','C-105']},'patch_audit':{'applied_patch_ids':g['applied_patch_ids'],'ignored_patch_ids':g['ignored_patch_ids']}})
        text(w,'out/resume_audit.md','Preserved round 1 results; P-1 and P-2 applied idempotent updates. Duplicate P-2 and unknown C-999 from P-3 were ignored. Only pending items were processed.\n'); after(1)
    elif n==58:
        for i in range(2):
            js(w,'out/final_plan.json',{'change_history':[{'day':d,'change':'Carry forward verified history'} for d in g['required_days'][:i+1]]}); after(i)
        p=js(w,'out/final_plan.json',{'change_history':[{'day':d,'change':'Retain chronological decision updates'} for d in g['required_days']], 'status_by_day':{d:'recorded' for d in g['required_days']},'risk_register':g['required_risks'],'final_budget':g['final_budget'],'launch_recommendation':g['launch_recommendation'],'owners':g['owner'],'conditions':g['required_conditions'],'removed_scope':g['removed_scope'],'conflict_resolution':'Stakeholder sales and privacy conflict resolved by retaining history and requiring signoff.'})
        text(w,'out/project_log.md','\n'.join(g['required_days']+g['required_risks'])+'\nRemoved in-app experimentation; launch remains conditional_go.\n')
        rows(w,g['decision_register'],['decision_id','day','decision','status','supersedes'],[{'decision_id':'D1','day':'Day 1','decision':'in-app experimentation','status':'reversed','supersedes':''},{'decision_id':'D3','day':'Day 3','decision':'conditional_go with removed in-app experimentation','status':'active','supersedes':'D1'}]); after(2)
    elif n==59:
        base=json.loads((w/'in/base_event.json').read_text())
        original={'event':base['event'],'blocks':[
            {'id':'setup','start':'09:00','end':'09:45','room':'Room A','assigned_people':['Ava','Ben']},
            {'id':'rehearsal','start':'10:00','end':'10:45','room':'Room A','assigned_people':['Ava','Chen']},
            {'id':'live_support','start':'13:00','end':'14:30','room':'Room A','assigned_people':['Chen','Dia']},
            {'id':'teardown','start':'14:45','end':'15:15','room':'Room A','assigned_people':['Ava','Ben']}]}
        js(w,'out/original_plan.json',original); after(0)
        blocks=original.get('blocks',[])
        if not blocks: raise ValueError('Expected original block schema')
        for b in blocks:
            if b['id']=='rehearsal': b.update(start='10:00',end='11:00')
            elif b['id']=='live_support': b.update(room='Room B',assigned_people=['Ben','Dia'])
        blocks=[b for b in blocks if b['id']!='accessibility_check']
        blocks.insert(next(i for i,b in enumerate(blocks) if b['id']=='live_support'),{'id':'accessibility_check','start':'12:45','end':'13:00','room':'Room B','assigned_people':['Ava']})
        p=js(w,'out/revised_plan.json',{**original,'blocks':blocks})
        text(w,'out/diff.md','Changed live support to Room B after 13:00; removed Chen from that block. Changed rehearsal to end at 11:00. Added accessibility_check for 15 minutes immediately before live support. Setup assignments remain preserved.\n'); after(1)
    else:
        js(w,'out/state.json',{'request_id':g['request_id'],'status':'running','final_export_created':False}); text(w,'out/tmp/preparation.csv','Draft temporary preparation\n'); after(0)
        shutil.rmtree(w/'out/tmp')
        p=js(w,'out/state.json',{'request_id':g['request_id'],'status':g['status'],'cancel_reason':g['cancel_reason'],'final_export_created':False})
        text(w,'out/audit.log','cancel-77 started; cancelled: Legal hold on renewal outreach data; removed temporary artifacts.\n')
        text(w,'out/cancellation_report.md','Request cancel-77 cancelled after Legal hold. Retained audit and inputs; removed temporary preparation. No final export created.\n'); after(1)
    return p

def construct_more(n,w,g,source,after):
    if n==35: return source_resolution(w,g)
    if n==36: return citations(w,g)
    if n==39: return architecture(w,g)
    if n in (40,41):
        from solutions_code import coverage,cart
        return coverage(w,g) if n==40 else cart(w,g)
    if n in (49,50,51,52,53): return analysis(n,w,g)
    if n in (57,58,59,60): return multiround(n,w,g,after)
    from solutions_ops import operations
    return operations(n,w,g)
