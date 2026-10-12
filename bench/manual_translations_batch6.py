"""Hand-written Hindi and Hinglish variants for operational and review tasks."""
TRANSLATIONS = {
('062-k8s-config-audit','prompt.txt'):(r'''Aap offline Kubernetes service configuration ka audit kar rahe hain.

Inputs:
- $WORKSPACE/in/deployment.yaml
- $WORKSPACE/in/service.yaml
- $WORKSPACE/in/policy.md

Bilkul ye output file banayein:
- $WORKSPACE/out/k8s_audit.csv

CSV requirements:
- Header mein ye fields hon: check_id,resource,status,severity,evidence,recommendation
- Har relevant finding ke liye ek row ho.
- status inmein se ek ho: pass, fail, warn.
- Finding par lagu hone par exact check_id values use karein:
  cpu_memory_limits, readiness_probe, liveness_probe, service_selector, service_target_port, image_tag_policy, privileged_container, service_type_policy

Audit expectations:
- Container CPU aur memory requests/limits check karein.
- Readiness aur liveness probes check karein.
- Deployment labels aur Service selector check karein.
- Service port/targetPort ko declared container ports ke against check karein.
- policy.md mein har forbidden ya required item apply karein.

Input files modify na karein. Network call ya live cluster tools use na karein. Jawab sirf di gayi files par aadharit ho.
''',r'''Tum offline Kubernetes service configuration audit kar rahe ho.

Inputs:
- $WORKSPACE/in/deployment.yaml
- $WORKSPACE/in/service.yaml
- $WORKSPACE/in/policy.md

Exactly ye output file banao:
- $WORKSPACE/out/k8s_audit.csv

CSV requirements:
- Header mein ye fields hon: check_id,resource,status,severity,evidence,recommendation
- Har relevant finding ke liye ek row ho.
- status inmein se ek ho: pass, fail, warn.
- Finding par apply hone par exact check_id values use karo:
  cpu_memory_limits, readiness_probe, liveness_probe, service_selector, service_target_port, image_tag_policy, privileged_container, service_type_policy

Audit expectations:
- Container CPU aur memory requests/limits check karo.
- Readiness aur liveness probes check karo.
- Deployment labels aur Service selector check karo.
- Service port/targetPort ko declared container ports se check karo.
- policy.md ke har forbidden ya required item ko apply karo.

Input files modify mat karo. Network call ya live cluster tools use mat karo. Apna jawab sirf supplied files par base karo.
'''),
('063-alert-dedup-noise','prompt.txt'):(r'''Offline alert storm ko actionable incidents mein reduce karein.

Inputs:
- $WORKSPACE/in/alerts.jsonl
- $WORKSPACE/in/topology.json

Bilkul ye output files banayein:
- $WORKSPACE/out/deduped_incidents.json
- $WORKSPACE/out/noise_report.md

deduped_incidents.json requirements:
- Top-level object mein `incidents` key ho.
- `incidents`, objects ki list ho.
- Har incident mein ye fields hon: incident_id, root_alert_id, root_service, cluster_alert_ids, impact_services, summary, evidence.
- cluster_alert_ids mein root alert aur downstream symptom alerts shamil hon.
- impact_services mein customer-facing ya dependent services ke naam hon jo usi root problem se affected hon.

noise_report.md requirements:
- Noise ke roop mein filter kiye alerts list karein aur wajah samjhayen.
- Duplicates/downstream symptoms ko actual noise se alag karein.
- Jahan lagu ho, maintenance windows, synthetic heartbeat flaps, aur sirf staging ke alerts ka zikr karein.

Input files modify na karein. External services use na karein. Result sirf diye gaye alerts aur topology par base karein.
''',r'''Offline alert storm ko actionable incidents mein reduce karo.

Inputs:
- $WORKSPACE/in/alerts.jsonl
- $WORKSPACE/in/topology.json

Exactly ye output files banao:
- $WORKSPACE/out/deduped_incidents.json
- $WORKSPACE/out/noise_report.md

deduped_incidents.json requirements:
- Top-level object mein `incidents` key ho.
- `incidents`, objects ki list ho.
- Har incident mein ye fields include hon: incident_id, root_alert_id, root_service, cluster_alert_ids, impact_services, summary, evidence.
- cluster_alert_ids mein root alert aur downstream symptom alerts include hon.
- impact_services mein customer-facing ya dependent services ke naam hon jo same root problem se affected hain.

noise_report.md requirements:
- Noise ke taur par filter kiye alerts list karo aur reason samjhao.
- Duplicates/downstream symptoms ko real noise se distinguish karo.
- Applicable hone par maintenance windows, synthetic heartbeat flaps aur staging-only alerts mention karo.

Input files modify mat karo. External services use mat karo. Result ko sirf supplied alerts aur topology par base karo.
'''),
('064-service-dependency-triage','prompt.txt'):(r'''Offline evidence se production checkout incident triage karein.

Inputs:
- $WORKSPACE/in/topology.json
- $WORKSPACE/in/metrics/service_metrics.csv
- $WORKSPACE/in/logs/checkout-web.log
- $WORKSPACE/in/logs/payment-api.log
- $WORKSPACE/in/logs/auth-gateway.log
- $WORKSPACE/in/logs/orders-db.log

Bilkul ye output files banayein:
- $WORKSPACE/out/root_cause.json
- $WORKSPACE/out/triage_notes.md

root_cause.json requirements:
- Top-level object mein ye fields hon: incident_id, root_cause_service, root_cause_change_id, confidence, affected_services, evidence, excluded_red_herrings, recommended_next_steps.
- evidence, objects ki list ho jisme source_file aur observation hon.
- excluded_red_herrings mein misleading signals ke naam aur woh primary cause kyon nahi hain, ye samjhaya ho.

triage_notes.md requirements:
- User impact se root cause tak dependency path summarize karein.
- Kam-se-kam three fixture files ko path se cite karein.
- Turant mitigation aur verification steps include karein.
- Inferences ko directly observed facts se spasht roop se alag mark karein.

Input files modify na karein. Live services ya external APIs use na karein.
''',r'''Offline evidence se production checkout incident triage karo.

Inputs:
- $WORKSPACE/in/topology.json
- $WORKSPACE/in/metrics/service_metrics.csv
- $WORKSPACE/in/logs/checkout-web.log
- $WORKSPACE/in/logs/payment-api.log
- $WORKSPACE/in/logs/auth-gateway.log
- $WORKSPACE/in/logs/orders-db.log

Exactly ye output files banao:
- $WORKSPACE/out/root_cause.json
- $WORKSPACE/out/triage_notes.md

root_cause.json requirements:
- Top-level object mein ye fields hon: incident_id, root_cause_service, root_cause_change_id, confidence, affected_services, evidence, excluded_red_herrings, recommended_next_steps.
- evidence, objects ki list ho jisme source_file aur observation hon.
- excluded_red_herrings mein misleading signals ke naam aur woh primary cause kyun nahi hain, ye batao.

triage_notes.md requirements:
- User impact se root cause tak ka dependency path summarize karo.
- Kam-se-kam three fixture files ko path se cite karo.
- Immediate mitigation aur verification steps include karo.
- Inferences ko directly observed facts se clearly alag mark karo.

Input files modify mat karo. Live services ya external APIs use mat karo.
'''),
('067-canary-release-check','prompt.txt'):(r'''Offline metric snapshots ke basis par assess karein ki canary release continue, pause, ya rollback honi chahiye.

Inputs:
- $WORKSPACE/in/baseline_metrics.csv
- $WORKSPACE/in/canary_metrics.csv
- $WORKSPACE/in/thresholds.json

Bilkul ye output file banayein:
- $WORKSPACE/out/canary_decision.json
- $WORKSPACE/out/metric_evidence.csv

canary_decision.json requirements:
- Top-level object mein ye hon: release_id, decision, breached_metrics, calculations, rationale, next_actions.
- decision inmein se ek ho: continue, pause, rollback.
- breached_metrics mein threshold exceed karne wale metric names list hon.
- calculations mein har evaluated metric ke liye baseline_value, canary_value, delta, threshold, direction, sample_count, aur evidence_status hon.
- Delta calculate karne se pehle ek metric ki sab available rows ka average lein.
- Direction sahi apply karein:
  - increase_bad ka matlab hai canary - baseline threshold se upar ho toh bura hai.
  - decrease_bad ka matlab hai baseline - canary threshold se upar ho toh bura hai.
- thresholds.json ka koi metric baseline ya canary mein missing ho, toh evidence_status ko missing_data mark karein, use breached na ginein, aur caveat include karein.
- thresholds.json ke min_sample_count se sample_count kam ho, toh evidence_status ko low_sample mark karein aur caveat include karein.
- next_actions safe operational recommendations hon; rollback execute karne ka daava na karein.

metric_evidence.csv requirements:
- Exact header:
  metric,baseline_value,canary_value,delta,threshold,direction,severity,evidence_status,breached
- thresholds.json ke har metric ke liye ek row include karein.

thresholds.json ke har metric ka evaluation karein. Input files modify na karein. Monitoring APIs call na karein aur live data use na karein.
''',r'''Offline metric snapshots ke basis par decide karo ki canary release continue, pause, ya rollback karni chahiye.

Inputs:
- $WORKSPACE/in/baseline_metrics.csv
- $WORKSPACE/in/canary_metrics.csv
- $WORKSPACE/in/thresholds.json

Exactly ye output file banao:
- $WORKSPACE/out/canary_decision.json
- $WORKSPACE/out/metric_evidence.csv

canary_decision.json requirements:
- Top-level object mein ye hon: release_id, decision, breached_metrics, calculations, rationale, next_actions.
- decision inmein se ek ho: continue, pause, rollback.
- breached_metrics mein woh metric names list hon jinhone thresholds exceed kiye.
- calculations mein har evaluated metric ke liye baseline_value, canary_value, delta, threshold, direction, sample_count aur evidence_status hon.
- Delta calculate karne se pehle same metric ki saari available rows ka average lo.
- Direction correctly apply karo:
  - increase_bad ka matlab canary - baseline threshold se upar ho toh bad hai.
  - decrease_bad ka matlab baseline - canary threshold se upar ho toh bad hai.
- thresholds.json ka koi metric baseline ya canary mein missing ho toh evidence_status ko missing_data mark karo, use breached mat count karo, aur caveat include karo.
- thresholds.json ke min_sample_count se sample_count kam ho toh evidence_status ko low_sample mark karo aur caveat include karo.
- next_actions safe operational recommendations hon; rollback execute karne ka claim mat karo.

metric_evidence.csv requirements:
- Exact header:
  metric,baseline_value,canary_value,delta,threshold,direction,severity,evidence_status,breached
- thresholds.json ke har metric ke liye ek row include karo.

thresholds.json ke har metric ko evaluate karo. Input files modify mat karo. Monitoring APIs call mat karo aur live data use mat karo.
'''),
('070-hr-resume-screening','prompt.txt'):(r'''Aap work-sample interview ke liye candidates screen kar rahe hain. Sirf job-related criteria apply karein.

Padhein:
- $WORKSPACE/in/job_description.md
- $WORKSPACE/in/fairness_policy.md
- $WORKSPACE/in/resumes/*.md

Banayein:
- $WORKSPACE/out/candidate_matrix.csv
- $WORKSPACE/out/screening_notes.md

candidate_matrix.csv requirements:
- Header bilkul ye ho: candidate_id,skills_score,evidence_score,shortlist,rank,reason
- Har resume ke liye ek row include karein.
- skills_score aur evidence_score, 0 se 5 tak ke integers hon.
- shortlist yes ya no ho.
- Sabse strong candidate ka rank 1, agle ka 2, aur isi tarah ho.
- Sensitive attributes include ya infer na karein.

screening_notes.md requirements:
- Ranking ko sirf resumes aur job_description.md ke job-related evidence se samjhayen.
- Sensitive attributes ignore kiye gaye, is baare mein fairness note include karein.
- Age, gender, ethnicity, family status, disability, nationality, ya religion ka zikr na karein.

Network use na karein. Input files modify na karein.
''',r'''Work-sample interview ke liye candidates screen kar rahe ho. Sirf job-related criteria apply karo.

Padho:
- $WORKSPACE/in/job_description.md
- $WORKSPACE/in/fairness_policy.md
- $WORKSPACE/in/resumes/*.md

Banao:
- $WORKSPACE/out/candidate_matrix.csv
- $WORKSPACE/out/screening_notes.md

candidate_matrix.csv requirements:
- Header exactly ye ho: candidate_id,skills_score,evidence_score,shortlist,rank,reason
- Har resume ke liye ek row include karo.
- skills_score aur evidence_score, 0 se 5 ke integers hon.
- shortlist yes ya no ho.
- Strongest candidate ko rank 1, next ko 2, aur aage isi tarah rank do.
- Sensitive attributes include ya infer mat karo.

screening_notes.md requirements:
- Ranking ko sirf resumes aur job_description.md ke job-related evidence se explain karo.
- Sensitive attributes ignore kiye gaye, aisa fairness note include karo.
- Age, gender, ethnicity, family status, disability, nationality, ya religion mention mat karo.

Network use mat karo. Input files modify mat karo.
'''),
('071-ecommerce-support-routing','prompt.txt'):(r'''Aap ecommerce support tickets route kar rahe hain.

Padhein:
- $WORKSPACE/in/tickets.json
- $WORKSPACE/in/order_history.csv
- $WORKSPACE/in/policy.md

Har ticket mein `vip_flag`, `prior_ticket_refs` jaise optional fields hain. VIP-1 ka paalan karein: VIP se **information_request** ko tezi milti hai (`priority=high`), lekin INFO-1 evidence rules ya fraud holds kabhi skip nahi hote.

Banayein:
- $WORKSPACE/out/routing_decisions.json
- $WORKSPACE/out/reply_templates.md

routing_decisions.json requirements:
- Valid JSON array ho jisme tickets.json ke har ticket id ke liye **exactly one object** ho (IDs same hon; same ordering zaroori nahi).
- Har object mein ye keys **zaroor** hon (order id na diya ho toh empty string `""` use karein): ticket_id, action, policy_basis, order_id, priority, customer_reply_key.
- action ∈ { refund, reship, escalate_human, information_request }.
- policy_basis mein governing clause token ho (REFUND-1, SHIP-1, ESC-1, INFO-1, FRAUD-1, CONFLICT-1, DISPUTE-1). Semicolon text se multiple citations de sakte hain, par tooling checks ke liye listed primary clause id string zaroor honi chahiye.
- Conflicts ko conservatively resolve karein: fraud holds, carrier/system contradictions ke muqable warehouse facts, aur DISPUTE-1 window ke andar delivered-status POD disputes — VIP kuch aur kahe tab bhi escalate_human.
- Verification missing ho → information_request + INFO-1.
- priority ∈ { high, normal }. Har escalate_human ticket ke liye aur verification ke bina VIP-backed INFO-1 threads ke liye (policy VIP-1) **high** use karein.
- Har ticket ke liye `customer_reply_key` exactly ek stable snake_case identifier ho (templates mein wahi key use ho).

reply_templates.md requirements:
- Har ticket ke liye ek section dein, jiska exact heading ho: `### Template <ticket_id>` (example: `### Template T-1001`).
- Body empathetic ho aur automation se alag route kiye gaye outcomes ka binding promise na kare.
- Jab tak action guarantee na kare ki automation ne refund/reship/hold removal handle kar liya hai, unka promise kabhi na karein — escalation par language conditional rakhein.

Saath hi banayein:
- $WORKSPACE/out/escalation_notes.csv
  Pehli row bilkul ye ho: ticket_id,reason,policy_basis,human_team
  Sirf har escalate_human ticket ke liye ek row; reason concise ho (≥8 chars); policy_basis routing_decisions.json se consistent ho; human_team bilkul inmein se ek ho:
  - T-1003 → Logistics Escalations
  - T-1005 → Fraud Review
  - T-1006 → Trust and Safety
  - T-1008 → Carrier Claims
  - T-1009 → Logistics Integrity

Network use na karein. Input files modify na karein.
''',r'''Ecommerce support tickets route kar rahe ho.

Padho:
- $WORKSPACE/in/tickets.json
- $WORKSPACE/in/order_history.csv
- $WORKSPACE/in/policy.md

Har ticket mein `vip_flag`, `prior_ticket_refs` jaise optional fields hain. VIP-1 follow karo: VIP se **information_request** fast hoti hai (`priority=high`), lekin INFO-1 evidence rules ya fraud holds kabhi skip nahi hote.

Banao:
- $WORKSPACE/out/routing_decisions.json
- $WORKSPACE/out/reply_templates.md

routing_decisions.json requirements:
- Valid JSON array ho jisme tickets.json ke har ticket id ke liye **exactly one object** ho (IDs same hon; same order zaroori nahi).
- Har object mein ye keys **must** hon (order id supplied na ho toh empty string `""` use karo): ticket_id, action, policy_basis, order_id, priority, customer_reply_key.
- action ∈ { refund, reship, escalate_human, information_request }.
- policy_basis mein governing clause token ho (REFUND-1, SHIP-1, ESC-1, INFO-1, FRAUD-1, CONFLICT-1, DISPUTE-1). Semicolon text se multiple citations de sakte ho, lekin tooling checks ke liye listed primary clause id string zaroor honi chahiye.
- Conflicts conservatively resolve karo: fraud holds, carrier/system contradictions ke against warehouse facts, aur DISPUTE-1 window ke andar delivered-status POD disputes — VIP kuch aur maange tab bhi escalate_human.
- Verification missing ho → information_request + INFO-1.
- priority ∈ { high, normal }. Har escalate_human ticket aur verification ke bina VIP-backed INFO-1 threads ke liye (policy VIP-1) **high** use karo.
- Har ticket ke liye `customer_reply_key` exactly ek stable snake_case identifier ho (templates bhi same key use karein).

reply_templates.md requirements:
- Har ticket ke liye ek section do, jiska exact heading ho: `### Template <ticket_id>` (example: `### Template T-1001`).
- Body empathetic ho aur automation se doosri taraf route hue outcomes par binding promise na kare.
- Jab tak action guarantee na kare ki automation ne refund/reship/hold removal handle kar diya hai, inka promise mat karo — escalation par language conditional rakho.

Saath mein banao:
- $WORKSPACE/out/escalation_notes.csv
  First row exactly ye ho: ticket_id,reason,policy_basis,human_team
  Sirf har escalate_human ticket ke liye ek row; reason concise ho (≥8 chars); policy_basis routing_decisions.json se consistent ho; human_team exactly inmein se ek ho:
  - T-1003 → Logistics Escalations
  - T-1005 → Fraud Review
  - T-1006 → Trust and Safety
  - T-1008 → Carrier Claims
  - T-1009 → Logistics Integrity

Network use mat karo. Input files modify mat karo.
'''),
('072-logistics-delay-response','prompt.txt'):(r'''Logistics delay response plan taiyar kar rahe hain.

Padhein:
- $WORKSPACE/in/shipments.csv
- $WORKSPACE/in/carrier_updates.json
- $WORKSPACE/in/customer_tiers.csv

Banayein:
- $WORKSPACE/out/delay_actions.csv
- $WORKSPACE/out/customer_messages.md

delay_actions.csv requirements:
- Header bilkul ye ho: shipment_id,delay_status,customer_tier,action,compensation,reason
- Har shipment ke liye ek row include karein.
- delay_status delayed ya on_track ho.
- action inmein se ek ho: monitor, notify, offer_credit, expedite_replacement.
- Customer tier rules ko consistently apply karein.

customer_messages.md requirements:
- Har delayed shipment id ke liye ek message include karein.
- Thos action aur compensation ya alternative plan ka zikr karein.
- Customer ko blame na karein aur internal carrier notes reveal na karein.

Network use na karein. Input files modify na karein.
''',r'''Logistics delay response plan prepare kar rahe ho.

Padho:
- $WORKSPACE/in/shipments.csv
- $WORKSPACE/in/carrier_updates.json
- $WORKSPACE/in/customer_tiers.csv

Banao:
- $WORKSPACE/out/delay_actions.csv
- $WORKSPACE/out/customer_messages.md

delay_actions.csv requirements:
- Header exactly ye ho: shipment_id,delay_status,customer_tier,action,compensation,reason
- Har shipment ke liye ek row include karo.
- delay_status delayed ya on_track ho.
- action inmein se ek ho: monitor, notify, offer_credit, expedite_replacement.
- Customer tier rules consistently apply karo.

customer_messages.md requirements:
- Har delayed shipment id ke liye ek message include karo.
- Concrete action aur compensation ya alternative plan mention karo.
- Customer ko blame mat karo aur internal carrier notes reveal mat karo.

Network use mat karo. Input files modify mat karo.
'''),
('074-education-grading-feedback','prompt.txt'):(r'''Fixed rubric se chhote student responses grade karein.

Padhein:
- $WORKSPACE/in/rubric.md
- $WORKSPACE/in/submissions/*.txt

Banayein:
- $WORKSPACE/out/grades.csv
- $WORKSPACE/out/feedback/*.md

$WORKSPACE/out/grades.csv requirements:
- Header bilkul ye ho: submission_id,concept_score,evidence_score,clarity_score,total_score
- Har submission ke liye ek row include karein.
- Scores rubric.md ke mutabik hon. concept_score ka max 4, evidence_score ka max 3, clarity_score ka max 3, aur total ka max 10 hai.

$WORKSPACE/out/feedback/*.md requirements:
- Har submission id ke liye ek feedback Markdown file banayein, jaise $WORKSPACE/out/feedback/submission_1.md.
- Har file mein kam-se-kam ek strength aur ek improvement ka zikr ho.
- Feedback us specific submission ke liye ho.

Network use na karein. Input files modify na karein.
''',r'''Fixed rubric se short student responses grade karo.

Padho:
- $WORKSPACE/in/rubric.md
- $WORKSPACE/in/submissions/*.txt

Banao:
- $WORKSPACE/out/grades.csv
- $WORKSPACE/out/feedback/*.md

$WORKSPACE/out/grades.csv requirements:
- Header exactly ye ho: submission_id,concept_score,evidence_score,clarity_score,total_score
- Har submission ke liye ek row include karo.
- Scores rubric.md ke according hon. concept_score max 4, evidence_score max 3, clarity_score max 3, aur total max 10 hai.

$WORKSPACE/out/feedback/*.md requirements:
- Har submission id ke liye ek feedback Markdown file banao, jaise $WORKSPACE/out/feedback/submission_1.md.
- Har file mein kam-se-kam ek strength aur ek improvement mention ho.
- Feedback usi submission ke liye specific ho.

Network use mat karo. Input files modify mat karo.
'''),
('075-platform-appeal-review','prompt.txt'):(r'''Platform policy bundle ke against moderation appeals review kar rahe hain.

**Mandatory execution constraint:** Inputs padhna khatam karne ke baad, run khatam hone se **pehle**, `$WORKSPACE/out/` ke andar teeno deliverables disk par likhna **anivarya** hai:
1. `appeal_decisions.csv`
2. `explanations.md`
3. `redaction_audit.csv`

File-writing tools ya shell redirection use karein, taaki in paths par real content wali files maujood hon; sirf chat mein unka varnan na karein. Agar `$WORKSPACE/out/` missing ho, toh use banayein, phir files likhein.

Decision lene se pehle neeche diye har input ko padhein:
- $WORKSPACE/in/moderation_policy.md
- $WORKSPACE/in/policy_amendments.md
- $WORKSPACE/in/case_files/*.json

Jahan noted ho, amendments 2026-01-01 ya uske baad file ki gayi appeals par lagu hote hain; jab case JSON mein `appeal_filed` is date se pehle ho, toh elevated `prior_harass_strikes` ke bawajood META-2, PRECVIO-1 ko block karta hai—qualifying harassment-tier appeals ke liye EDGE-1 apply karein.

Banayein:
- $WORKSPACE/out/appeal_decisions.csv
- $WORKSPACE/out/explanations.md

appeal_decisions.csv requirements:
- Header row ke columns bilkul ye naam aur order hon: case_id,decision,final_action,policy_basis,confidence
- case_files/ ke andar maujood har case JSON file ke liye exactly ek row ho.
- decision inmein se ek ho: uphold, overturn, downgrade.
- final_action, decision aur policy bundle (amendments samet) ke saath consistent ho.
- policy_basis mein har applicable clause ID shamil ho; multiple IDs ko semicolons se alag karein (jaise PRECVIO-1;EDGE-1). IDs policy documents se match honi chahiye.
- Har row ke liye confidence calibration se **exactly** match kare; sirf **high**, **medium**, ya **low** use karein: clear-cut hate/counterspeech → **high**; compromise narratives, EDGE/PRECVIO/MISLABEL interplay, PRECVIO vs EDGE/META-2 date logic, ya advisory automation conflicts → aam taur par **medium**; sach mein ambiguous fact patterns → **low**.

explanations.md requirements:
- **Har** case id cover karein, har ek ke liye ek Markdown section ho jiska exact heading `### Case <case_id>` ho (example: `### Case A-01`).
- **Har** section ke andar us case ke appeal_decisions.csv mein listed **har** clause ID cite karein, facts summarize karein (jahan relevant ho advisory automation samet), aur poori file mein sirf ek baar nahi, **har** section mein `rather than` ya `instead of` include karein.

Saath hi banayein:
- $WORKSPACE/out/redaction_audit.csv
  Header columns ke naam aur order bilkul ye hon: case_id,redacted_field,redaction_reason
  Sensitive payload paths ko explicit karne ke liye paryapt rows dein—jab case JSON mein multiple sensitive keys (`reporter`, `reporter_email`, `reporter_alias`, …) hon, toh un paths ke naam alag-alag rows mein dein (har case id ke liye minimum **one row**, aur multiple fields lagu hon toh zyada rows).

Network use na karein. Input files modify na karein.
''',r'''Platform policy bundle ke against moderation appeals review kar rahe ho.

**Mandatory execution constraint:** Inputs padhne ke baad, run end hone **se pehle**, `$WORKSPACE/out/` ke andar saare three deliverables disk par likhna **non-negotiable** hai:
1. `appeal_decisions.csv`
2. `explanations.md`
3. `redaction_audit.csv`

File-writing tools ya shell redirection use karo taaki in paths par real content wali files hon; sirf chat mein describe mat karo. `$WORKSPACE/out/` missing ho toh pehle banao, phir files likho.

Decision lene se pehle neeche ka har input padho:
- $WORKSPACE/in/moderation_policy.md
- $WORKSPACE/in/policy_amendments.md
- $WORKSPACE/in/case_files/*.json

Jahan noted ho, amendments 2026-01-01 ya uske baad filed appeals par apply hote hain; case JSON mein `appeal_filed` is date se pehle ho toh elevated `prior_harass_strikes` ke bawajood META-2, PRECVIO-1 ko block karta hai—qualifying harassment-tier appeals ke liye EDGE-1 apply karo.

Banao:
- $WORKSPACE/out/appeal_decisions.csv
- $WORKSPACE/out/explanations.md

appeal_decisions.csv requirements:
- Header row ke column names aur order exactly ye hon: case_id,decision,final_action,policy_basis,confidence
- case_files/ ke andar present har case JSON file ke liye exactly ek row ho.
- decision inmein se ek ho: uphold, overturn, downgrade.
- final_action, decision aur policy bundle (amendments samet) ke saath consistent ho.
- policy_basis mein har applicable clause ID include karo; multiple IDs ko semicolons se separate karo (jaise PRECVIO-1;EDGE-1). IDs policy documents ke exact hone chahiye.
- Har row ka confidence calibration se **exactly** match kare aur sirf **high**, **medium**, ya **low** ho: clear-cut hate/counterspeech → **high**; compromise narratives, EDGE/PRECVIO/MISLABEL interplay, PRECVIO vs EDGE/META-2 date logic, ya advisory automation conflicts → aam taur par **medium**; truly ambiguous fact patterns → **low**.

explanations.md requirements:
- **Har** case id cover karo, har ek ke liye ek Markdown section ho jiska exact heading `### Case <case_id>` ho (example: `### Case A-01`).
- **Har** section mein us case ke appeal_decisions.csv mein listed **har** clause ID cite karo, facts summarize karo (relevant hone par advisory automation bhi), aur `rather than` ya `instead of` ko sirf poori file mein ek baar nahi, **har** section mein include karo.

Saath hi banao:
- $WORKSPACE/out/redaction_audit.csv
  Header ke column names aur order exactly ye hon: case_id,redacted_field,redaction_reason
  Sensitive payload paths explicit karne ke liye enough rows do—case JSON mein multiple sensitive keys (`reporter`, `reporter_email`, `reporter_alias`, …) hon toh un paths ko alag rows mein name karo (har case id ke liye minimum **one row**, multiple fields apply hon toh aur rows).

Network use mat karo. Input files modify mat karo.
'''),
}
