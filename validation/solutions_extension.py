"""Private constructed validation workspaces for the 14-task extension.

Executed only in the network-isolated grader image; never sent to an agent.
"""
import copy
import json
import re
import yaml
from solutions import text, js, rows, quote


def construct_extension(n,w,g,after):
    if n==28:
        emails=[json.loads(f.read_text()) for f in sorted((w/'in/emails').glob('*.json'))]
        north=[e for e in emails if e['message_id'] in g['northwind_unique_message_ids'] and not e['subject'].startswith('Fwd:')]
        p=js(w,'out/thread_summary.json',{'threads':[
            {'subject':'Northwind onboarding pilot','timeline':[{'message_id':e['message_id'],'timestamp':e['timestamp'],'summary':e['body']} for e in north],
             'final_todos':g['final_todos'],'status':'Kickoff date agreed by onboarding; procurement not approved'},
            {'subject':'Invoice 8841 posted','timeline':[{'message_id':'m-200','timestamp':emails[-1]['timestamp'],'summary':emails[-1]['body']}],'final_todos':[]}]})
        text(w,'out/reply_draft.txt','Hi Morgan, August 18 works for our onboarding team. I will send the security questionnaire today. Procurement is not approved yet; please confirm its status after the review. Thanks, Sam.\n')
        return p
    if n==32:
        p=text(w,'out/followup_email.txt','Hi Elena,\n\nThank you for considering Professional for Brightline Labs and your 42 seats. We can discuss a first-year discount of up to 15%, subject to manager approval. The requested higher discount requires VP approval before an offer. Custom SSO terms are not available on Professional; standard SSO terms are available on Enterprise. We cannot promise acceptance of legal redlines. Could we schedule a 30-minute security review with solutions engineering next week? Please send suitable times.\n\nBest, Maya\n')
        text(w,'out/account_risk_notes.md','Brightline Labs: Elena requests security review while SSO timing, legal redlines and budget approval remain blockers. TaskHive is the competitor. Maya owns scheduling a 30-minute security review with solutions engineering. The 15% cap requires manager approval; higher discounts need VP approval, and no such approval is recorded. Keep SSO and legal commitments within policy.\n')
        return p
    if n==37:
        facts={v['case_id']:v for v in json.loads((w/'in/cases.json').read_text())}
        def ruling(key,exp,fact):
            signal=quote(w,'policy_manual.md',exp['tokens'])+' '+quote(w,'policy_amendment.md',exp['tokens'])+' Case evidence: '+json.dumps(fact)
            return {'case_id':key,'applicable_clause':exp['applicable_clause'],'decision':exp['decision'],
                    'reason_code':exp['reason_code'],'quote_or_signal':signal,'secondary_clauses':exp['secondary_clauses'],
                    'blocking_condition':'Policy review/denial condition: '+'; '.join(group[0] for group in exp.get('blocking_token_groups',[])),
                    'missing_information':exp['missing_terms']}
        rulings=[]; summary=[]
        for key,exp in g['cases'].items():
            r=ruling(key,exp,facts[key]); lines=[]
            for fact in facts[key].get('line_items',[]):
                line=ruling(key,g['line_items'][key+':'+fact['line_id']],fact);line['line_id']=fact['line_id'];lines.append(line)
            if lines:r['line_item_rulings']=lines
            rulings.append(r)
            summary.append({'case_id':key,'case_decision':exp['decision'],'denied_lines':sum(x['decision']=='deny' for x in lines),
                'review_lines':sum(x['decision']=='needs_review' for x in lines),'approved_lines':sum(x['decision']=='approve' for x in lines),
                'controlling_clause':exp['applicable_clause'],'summary_reason':exp['reason_code']+'; denied lines control, review lines remain pending, approved lines counted separately' if lines else exp['reason_code']})
        p=js(w,'out/case_rulings.json',rulings)
        rows(w,'out/ruling_summary.csv',['case_id','case_decision','denied_lines','review_lines','approved_lines','controlling_clause','summary_reason'],summary)
        return p
    if n==44:
        workflow={'name':'CI','on':{'push':{'paths':['app/**','test*.py','requirements.txt','.github/workflows/**','CI_NOTES.md']},
            'pull_request':{'paths':['app/**','test*.py','requirements.txt','.github/workflows/**','CI_NOTES.md']},'workflow_dispatch':{}},
            'permissions':{'contents':'read'},'concurrency':{'group':'${{ github.workflow }}-${{ github.ref }}','cancel-in-progress':True},
            'jobs':{'test':{'runs-on':'ubuntu-latest','timeout-minutes':10,'strategy':{'fail-fast':False,'matrix':{'python-version':['3.10','3.11']}},
                'steps':[{'uses':'actions/checkout@v4'},{'uses':'actions/setup-python@v5','with':{'python-version':'${{ matrix.python-version }}','cache':'pip'}},
                    {'run':'pip install -r requirements.txt'},{'run':'python -m pytest'},
                    {'run':'python -c "from app.mathutil import normalize_percent; assert normalize_percent(50) == 0.5"'}]}}}
        p=text(w,'in/project/.github/workflows/ci.yml',yaml.safe_dump(workflow,sort_keys=False))
        text(w,'in/project/ci_design_notes.md','CI_NOTES.md defines the constraints. A pull request runs the same explicit Python matrix as a push. Path filters cover app, tests, requirements, workflows and CI_NOTES.md. The smoke import checks app.mathutil without external service calls. Read-only contents, no secrets, no deployment, a bounded timeout and concurrency cancellation limit exposure and wasted work. Fail-fast is false to observe both Python versions.\n')
        return p
    if n==48:
        changelog='''# Changelog: 2.4.0 — 2025-10-14

## Added
- ISSUE-101: Add webhook signatures, verified through X-Webhook-Signature.
- ISSUE-110: Replace the earlier X-Signature header with X-Webhook-Signature.
## Changed
- ISSUE-103: Billing usage field changes to billable_units; update client integrations.
- ISSUE-104: Remove legacy token authentication; migrate to the Authorization header.
- ISSUE-106: rate limit responses use retry_after_ms in milliseconds.
## Fixed
- ISSUE-102: Remove duplicate invoice rows from CSV export.
## Security
- SEC-PUBLIC-4: Public advisory included. SEC-EMBARGO-9 remains under embargo; no technical details disclosed.
## Breaking Changes
- Migrate ISSUE-103, ISSUE-104, ISSUE-106 and ISSUE-110 before upgrading.
## Release accounting
- ISSUE-105 and ISSUE-107 were reverted and not shipped.
- ISSUE-108 is deferred; ISSUE-109 is supporting documentation only.
- Duplicate commits for ISSUE-101 and ISSUE-102 count once each; six product issues shipped.
'''
        p=text(w,'out/CHANGELOG.md',changelog)
        js(w,'out/release_summary.json',{'version':g['version'],'date':g['date'],'highlights':[
            'webhook signatures: X-Webhook-Signature','Remove duplicate invoice rows from CSV export'],
            'breaking_changes':['billable_units replaces the usage field','legacy token removal: use Authorization header',
                'rate limit: retry_after_ms is milliseconds','X-Signature changes to X-Webhook-Signature'],
            'issue_count':6,'risk_notes':['SEC-PUBLIC-4 public advisory; SEC-EMBARGO-9 remains under embargo',
                'Reverted ISSUE-105 and ISSUE-107 are not shipped; defer ISSUE-108; documentation ISSUE-109 is not counted']})
        text(w,'out/upgrade_notes.md','Before 2.4.0, update billing clients to billable_units (ISSUE-103); migrate legacy token clients to the Authorization header (ISSUE-104); interpret retry_after_ms as milliseconds in rate limit responses (ISSUE-106); replace X-Signature with X-Webhook-Signature for webhook signatures (ISSUE-110). Test all four migrations. The revert of ISSUE-105 and ISSUE-107 removes them from this release; defer ISSUE-108. SEC-EMBARGO-9 remains under embargo; consult SEC-PUBLIC-4 for public security information.\n')
        js(w,'out/release_decisions.json',g['release_decisions']);js(w,'out/release_audit.json',g['release_audit'])
        return p
    if n==54:
        p=rows(w,g['outputs']['csv'],g['header'],g['rows']);rows(w,g['outputs']['rollup'],g['rollup_header'],g['rollup_rows'])
        drivers={'Marketing Ads':'Actual ad spending exceeds plan by 12000.00 (24.00%).','Marketing Events':'Event spending is 4000.00 below budget (-13.33%).',
            'Operations Logistics':'Logistics spending exceeds budget by 6000.00 (24.00%).','Product Research':'Unplanned research actuals of 3500.00 have no budget row.',
            'R&D Tools':'Tool spending is 3000.00 below budget (-15.00%).','Security Tools':'Budget exists but actual spending is missing; confirm the missing actual row.',
            'Support Escalations':'Zero-budget category has actual spending of 1200.00.'}
        js(w,g['outputs']['review_reasons'],{k:{**v,'primary_driver':drivers[k]} for k,v in g['review_reasons'].items()})
        text(w,g['outputs']['summary'],'# Budget variance\n\nLargest overrun: Marketing Ads.\n\n'+'\n'.join(k+': '+drivers[k] for k in g['review_items'])+'\nSales Travel is exactly 10.00% and remains ok: only absolute variance above 10% triggers review. Product Research is unplanned; Support Escalations has zero budget; Security Tools has a missing actual. Keep those distinctions explicit.\n')
        return p
    if n==55:
        p=js(w,g['outputs']['json'],{k:g[k] for k in ['stages','largest_dropoff','excluded_bot_users','data_quality']})
        rows(w,g['outputs']['cohort'],g['cohort_header'],g['cohort_rows']);js(w,g['outputs']['stage_user_sets'],g['stage_user_sets'])
        text(w,g['outputs']['insights'],'The largest proportional dropoff is trial_start to purchase: 3 of 8 users (37.5%). Control converts 3/6 (50%); variant 2/6 (33.33%); beta 0/2. These small sample sizes do not support a causal conclusion. Event order was enforced using timestamps, repeated stage events were deduplicated, and bots excluded. Investigate the trial-to-purchase flow with a follow-up experiment and user survey; verify sequence instrumentation first.\n')
        return p
    if n==65:
        p=js(w,'out/capacity_plan.json',{'services':[
            {'service':'checkout-api','forecast_peak_rps':2391.2,'required_capacity_rps':3108.56,'required_headroom_pct':0.3,'selected_instance_type':'c7g.large',
             'instance_count':6,'on_demand_count':6,'spot_count':0,'provided_capacity_rps':3720,'hourly_cost_usd':0.456,'zones':2},
            {'service':'pricing-worker','forecast_peak_rps':575,'required_capacity_rps':690,'required_headroom_pct':0.2,'selected_instance_type':'c7g.large',
             'on_demand_count':1,'spot_count':1,'provided_capacity_rps':1240,'hourly_cost_usd':0.108,'zones':1}], 'total_hourly_cost_usd':0.564})
        text(w,'out/cost_notes.md','Checkout: historical maximum 1960 × 1.22 = 2391.2 forecast; add 30% headroom = 3108.56. Six c7g.large provide 3720 RPS across two zones for 0.456 per hour. Five m7i.large provide 3500 for 0.480; three c7g.xlarge provide 3660 for 0.456, tied in cost. Pricing: 500 × 1.15 = 575; add 20% = 690. One on-demand plus one spot c7g.large provide 1240 at 0.108, respecting 50% spot share. Total 0.564 is below the 0.78 total budget and both service caps. t3.large is incompatible.\n')
        rows(w,'out/risk_tradeoffs.csv',['service','tradeoff','risk','mitigation'],[
            {'service':'checkout-api','tradeoff':'Six small instances versus three larger at equal budget','risk':'Lost zone may consume headroom','mitigation':'Distribute across zones; verify load before launch'},
            {'service':'pricing-worker','tradeoff':'50% spot saves cost','risk':'spot interruption','mitigation':'Use one on-demand instance and queue retries'},
            {'service':'both','tradeoff':'Reject incompatible burstable t3.large','risk':'Launch SLO headroom','mitigation':'Keep compatible arm64 images and respect budget'}])
        return p
    if n==66:
        owners={'missing_down_migration':'database owner','missing_sre_approval':'SRE','missing_kill_switch':'payment service owner',
            'incomplete_health_checks':'SRE','rollback_duration_risk':'incident commander'}
        findings={'missing_down_migration':'ledger_entries_v4 has no down migration.', 'missing_sre_approval':'SRE approval is missing.',
            'missing_kill_switch':'payment_routing_v2 kill flag is absent.', 'incomplete_health_checks':'auth_401_rate threshold is missing.',
            'rollback_duration_risk':'Estimated duration 18 minutes exceeds the 15 minute window.'}
        p=rows(w,'out/blockers.csv',['blocker_id','severity','owner','evidence','required_action'],[
            {'blocker_id':k,'severity':v['severity'],'owner':owners[k],'evidence':findings[k],'required_action':'Resolve and verify '+findings[k]} for k,v in g['expected_blockers'].items()])
        text(w,'out/rollback_readiness.md','# Rollback readiness: blocked\n\nDo not execute the rollback. The incident commander must obtain SRE approval, the database owner must supply a verified down migration for ledger_entries_v4, and the payment owner must supply the payment_routing_v2 kill flag. The incident commander declares rollback after blockers are resolved; the release manager restores traffic to the previous stable version, disabling card_bin_cache_v3 if triggered. Explicit database owner approval is required before any schema reversal. Verify p95_latency_ms below 850 over 5m, error_rate_pct below 1.5 over 5m and ledger_write_success_pct above 99.95 over 10m. auth_401_rate has no threshold and requires one before readiness; monitor for 20 minutes per the runbook. Rehearse duration: the 18 minute estimate exceeds the 15 minute window. Reassess only after all blockers have evidence of resolution; no rollback actions are performed by this plan.\n')
        return p
    if n==68:
        p=text(w,'out/launch_plan.md','''# Objectives
Plan AtlasFlow Teams availability on 2026-05-20; convert existing trial admins into paid workspace pilots. Cross-document action extraction remains beta for existing trial admins only.
## Audience
Operations Directors need operational clarity, Product Marketers need campaign workflows, and IT Admins need controlled administration. Do not target Agency Partners: the mobile app is unavailable.
## Budget
Total USD 5800: creative 1800; webinar 1200; paid social 1500; sales enablement 700; compliance 600.
## Timeline
2026-05-01: start creative and draft claims list. 2026-05-10: compliance_review before publication. 2026-05-15: webinar registration and sales readiness. 2026-05-20: launch day after approval.
## Dependencies
The final claims list needs compliance_review. Customer email requires compliance approval; sales enablement depends on the approved claims list. Paid social depends on the webinar registration page. Reserve compliance funding before expanding paid social. Launch depends on readiness of all channels.
## Compliance
Use only approved claims. No promise of an unavailable mobile app or unapproved integrations. Availability statements follow the launch date and actual approval.
## Risks
Approval delay blocks publication; registration dependency may delay the offline webinar. Maintain owner checkpoints and defer launch if review is incomplete.
''')
        js(w,'out/content_pack.json',{'tagline':'Clear workflows for coordinated teams','email_subjects':['Prepare for the workflow launch','Join our workflow webinar','Your launch readiness checklist'],
            'social_posts':['Meet coordinated workflows on launch day.','Register for the approved workflow webinar.','Explore practical team workflows after launch approval.'],
            'webinar_agenda':['Introductions','Approved product walkthrough','Role-specific examples','Questions and next steps'],
            'segment_messages':{'ops_directors':'Coordinate operational workflows.','product_marketers':'Plan approved campaign workflows.',
                'it_admins':'Review administration controls.','agency_partners':'Excluded: mobile app unavailable; do not target this segment.'}})
        rows(w,'out/launch_checklist.csv',['item','owner','due_date','dependency','status'],[
            {'item':'claims list','owner':'Marketing','due_date':'2026-05-01','dependency':'approved brief','status':'planned'},
            {'item':'compliance_review','owner':'Compliance','due_date':'2026-05-10','dependency':'claims list','status':'planned'},
            {'item':'webinar registration','owner':'Marketing','due_date':'2026-05-15','dependency':'compliance_review','status':'planned'},
            {'item':'sales enablement','owner':'Sales','due_date':'2026-05-15','dependency':'compliance_review','status':'planned'},
            {'item':'launch day','owner':'Launch owner','due_date':'2026-05-20','dependency':'compliance_review; webinar registration; sales enablement','status':'planned'}])
        return p
    if n==79:
        for name,value in g['outputs'].items():js(w,'out/normalized/'+name,value)
        p=rows(w,'out/index.csv',['source_path','target_path','record_type','record_id','status'],g['index_rows'])
        rows(w,'out/reject_ledger.csv',['source_path','error_type','details'],g['reject_rows']);js(w,'out/batch_summary.json',g['summary']);return p
    if n==80:
        p=js(w,'out/canonical_records.json',g['canonical_records'])
        text(w,'out/canonical_records.yaml',yaml.safe_dump(g['canonical_records'],sort_keys=False,allow_unicode=True))
        text(w,'out/canonical_records.csv',g['canonical_csv'])
        js(w,'out/conversion_report.json',{'sources':['json','yaml','csv','markdown'],'priority':['json','yaml','csv','markdown'],'conflicts':g['conflicts'],
            'preservation':'String record IDs, null notes, array tags and escaped Markdown pipes preserved.'});return p
    if n==96:
        answers=[]
        for key,v in g['answers'].items():
            sources=[]
            for s in v['sources']:
                raw=(w/'in'/s).read_text(); pieces=re.split(r'(?<=[.!?])\s+',raw)
                signal=' '.join(piece.strip() for piece in pieces if any(t.lower() in piece.lower() for t in v['evidence_tokens'])
                    and not any(token.lower() in piece.lower() for token in g['forbidden_answer_tokens'].get(key,[])))
                offset=next((raw.lower().find(t.lower()) for t in v['evidence_tokens'] if t.lower() in raw.lower()),len(raw))
                identifiers=list(re.finditer(r'(?:Section )?((?:PM|RN|SB|FAQ)-[\w.-]+)',raw[:offset]))
                identifier=identifiers[-1].group(1).rstrip(':') if identifiers else ''
                sources.append({'source_file':s,'evidence_id':identifier,'quote_or_signal':signal})
            answers.append({'question_id':key,'status':v['status'],'answer':'insufficient_evidence' if v['status']=='insufficient_evidence' else ' '.join(v['facts']),
                'sources':sources,'missing_evidence':v['missing']})
        return js(w,'out/answers.json',{'answers':answers})
    if n==103:
        original={'request_id':'PCR-2026-05-REFUND-17','plan_version':1,'decisions':[]}
        zones={'AMER':'-07:00','EU':'+02:00','APAC':'+08:00'};owners={'AMER':'Marta','EU':'Lena','APAC':'Priya'}
        launches={'AMER':'2026-05-20T16:00:00','EU':'2026-05-19T16:00:00','APAC':'2026-05-22T12:00:00'}
        comms={'AMER':'2026-05-18T16:00:00','EU':'2026-05-17T16:00:00','APAC':'2026-05-20T12:00:00'}
        for region in g['required_regions']:
            for stream in g['required_workstreams']:
                date=launches[region] if stream=='launch_gate' else comms[region] if stream=='customer_comms' else '2026-05-16T10:00:00' if stream=='legal_review' else '2026-05-17T10:00:00'
                deps=[] if stream=='legal_review' else [region+'-legal_review'] if stream=='support_training' else [region+'-legal_review'] if stream=='customer_comms' else [region+'-support_training',region+'-customer_comms']
                original['decisions'].append({'decision_id':region+'-'+stream,'region':region,'workstream':stream,
                    'owner':'Noah' if stream=='support_training' else 'Iris' if stream=='customer_comms' else owners[region],
                    'planned_start':date+zones[region],'planned_end':date+zones[region],
                    'channel_or_artifact':'lms_module' if stream=='support_training' else 'email' if stream=='customer_comms' else 'approval review' if stream=='legal_review' else 'readiness gate',
                    'dependencies':deps,'evidence_refs':['in/policy_change_request.json','in/regional_constraints.csv','in/team_capacity.json','in/communications_matrix.csv']})
        p=js(w,'out/original_plan.json',original); original_bytes=(w/p).read_bytes()
        js(w,'out/state.json',{'round':1,'plan_version':1,'decisions':original['decisions'],'source_files_read':original['decisions'][0]['evidence_refs']})
        assert not (w/'out/revised_plan.json').exists() and not (w/'out/diff.md').exists()
        after(0)
        revised=copy.deepcopy(original);revised['plan_version']=2;changed=[];unchanged=[]
        for item in revised['decisions']:
            if item['region']=='EU' and item['workstream'] in ['launch_gate','customer_comms']:
                old=item['planned_start'];new=old.replace('2026-05-19','2026-05-21') if item['workstream']=='launch_gate' else old.replace('2026-05-17','2026-05-19');item['planned_start']=item['planned_end']=new
            if item['region']=='APAC' and item['owner']=='Priya':item['owner']='Ken'
            if item['workstream']=='support_training':item['channel_or_artifact']=['lms_module','refund exception drill']
            original_item=next(x for x in original['decisions'] if x['decision_id']==item['decision_id'])
            (changed if item!=original_item else unchanged).append(item['decision_id'])
        js(w,'out/revised_plan.json',revised)
        js(w,'out/state.json',{'round':2,'plan_version':2,'decisions':revised['decisions'],
            'source_files_read':original['decisions'][0]['evidence_refs']+['in/round2_update_notice.json'],
            'changed_decision_ids':changed,'unchanged_decision_ids':unchanged})
        text(w,'out/diff.md','# Added\nThe refund exception drill is added to support training for every region.\n# Removed\nPriya is removed as APAC owner; stable decision IDs retained.\n# Changed\nEU launch and customer communications move 48 hours later, avoiding the blackout. Ken replaces Priya on APAC regional decisions.\n# Unchanged\nAMER legal review, customer communications and launch gate retain their original schedule and owners; training alone adds the drill. Inputs are preserved. These are plans only.\n')
        assert (w/p).read_bytes()==original_bytes
        after(1);return p
    raise ValueError('Unrecognized extension task')
