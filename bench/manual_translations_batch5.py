"""Hand-written Hindi and Hinglish variants for SQL and stateful tasks."""
TRANSLATIONS = {
('051-sql-query-report','prompt.txt'):(r'''Chhoti BI report banane ke liye offline SQL fixture use karein.

Input:
- $WORKSPACE/in/schema_data.sql

Banayein:
- $WORKSPACE/out/query_results.json
- $WORKSPACE/out/analysis.md
- $WORKSPACE/out/query_audit.json

Requirements:
1. schema_data.sql ko local SQLite database mein load karein, ya equivalent SQL locally execute karein.
2. Sirf un orders par vichar karein jinka status = 'paid' ho aur order_date 2025-01-01 se 2025-03-31 tak inclusive ho.
3. query_results.json valid JSON ho aur ismein exactly ye top-level keys hon:
   - top_products_by_revenue
   - revenue_by_region
   - category_summary
4. top_products_by_revenue mein revenue ke descending order mein top 3 products hon, in fields ke saath:
   product_id, product_name, revenue
   Revenue tie ho toh product_id ascending order se tie break karein.
5. revenue_by_region mein har customer region ki ek row ho, in fields ke saath:
   region, order_count, revenue
   Region rows ko ascending order mein sort karein.
6. category_summary mein har product category ki ek row ho, in fields ke saath:
   category, units_sold, revenue
   Category rows ko ascending order mein sort karein.
7. Revenue values two decimal places tak rounded numbers ya numeric strings honi chahiye.
8. analysis.md mein top product, highest revenue region, agar koi tie ho toh uska handling, aur excluded records rule ko briefly identify karein.
9. Date window mein 2025-01-01 aur 2025-03-31 dono shamil hain. Returned, cancelled, aur window ke bahar ke orders exclude karein, chahe unmein bade order_items hon.

query_audit.json requirements:
- `included_order_ids`, `excluded_status_order_ids`, `excluded_out_of_window_order_ids`, `boundary_included_order_ids`, `top_product_tie_order` keys wala valid JSON.
- Pehli chaar keys, ascending order mein sorted order_id strings ke arrays hon.
- top_product_tie_order mein revenue se tied product_ids, top_products_by_revenue ke liye use hue exact output order mein listed hon.

Fixtures modify na karein. Network access ya external APIs use na karein.
''',r'''Chhoti BI report banane ke liye offline SQL fixture use karo.

Input:
- $WORKSPACE/in/schema_data.sql

Banao:
- $WORKSPACE/out/query_results.json
- $WORKSPACE/out/analysis.md
- $WORKSPACE/out/query_audit.json

Requirements:
1. schema_data.sql ko local SQLite database mein load karo ya equivalent SQL locally execute karo.
2. Sirf woh orders consider karo jinka status = 'paid' ho aur order_date 2025-01-01 se 2025-03-31 tak inclusive ho.
3. query_results.json valid JSON ho aur exactly ye top-level keys hon:
   - top_products_by_revenue
   - revenue_by_region
   - category_summary
4. top_products_by_revenue mein revenue ke descending order mein top 3 products hon, in fields ke saath:
   product_id, product_name, revenue
   Revenue tie ho toh product_id ascending se tie break karo.
5. revenue_by_region mein har customer region ki ek row ho, in fields ke saath:
   region, order_count, revenue
   Region rows ko ascending order se sort karo.
6. category_summary mein har product category ki ek row ho, in fields ke saath:
   category, units_sold, revenue
   Category rows ko ascending order se sort karo.
7. Revenue values two decimal places tak rounded numbers ya numeric strings hon.
8. analysis.md mein top product, highest revenue region, koi tie ho toh uska handling, aur excluded records rule briefly identify karo.
9. Date window mein 2025-01-01 aur 2025-03-31 include hain. Returned, cancelled, aur window ke bahar ke orders exclude karo, chahe unke order_items bade hon.

query_audit.json requirements:
- `included_order_ids`, `excluded_status_order_ids`, `excluded_out_of_window_order_ids`, `boundary_included_order_ids`, `top_product_tie_order` keys wala valid JSON.
- Pehli chaar keys ascending order mein sorted order_id strings ke arrays hon.
- top_product_tie_order mein revenue se tied product_ids ko top_products_by_revenue ke exact output order mein list karo.

Fixtures modify mat karo. Network access ya external APIs use mat karo.
'''),
('052-metric-definition-audit','prompt.txt'):(r'''Approved metric definitions ke against dashboard export audit karein.

Inputs:
- $WORKSPACE/in/metric_definitions.md
- $WORKSPACE/in/dashboard_export.csv

Banayein:
- $WORKSPACE/out/metric_audit.csv
- $WORKSPACE/out/equivalence_audit.json

Output columns, isi exact order mein:
metric_name,dashboard_formula,approved_formula,affected_field,severity

Rules:
1. Fixtures modify na karein.
2. Sirf un metrics ko include karein jinka dashboard formula approved definition se conflict karta hai.
3. Jo metrics approved definition se semantically match karte hain unhe flag na karein. Metric conflict karta hai ya nahi, decide karne se pehle metric_definitions.md mein diye equivalent formula notes apply karein.
4. Revenue, conversion, ya cohort-retention denominator errors ke liye severity high honi chahiye; average/latency/window ya operational SLA denominator errors ke liye medium; baaki ke liye low.
5. Conflicting metrics ke `dashboard_formula`, `approved_formula`, aur `affected_field` text source files se seedha copy karein.
6. metric_audit.csv valid CSV hona chahiye. Comma wale fields ko quote karein.

equivalence_audit.json requirements:
- `mismatched_metrics`, `semantically_matching_metrics`, `severity_by_metric`, `reason_class_by_metric` keys wala valid JSON.
- mismatched_metrics, metric_audit.csv mein shamil sorted metric names hon.
- semantically_matching_metrics, dashboard export mein dikhne wale sorted metric names hon jine flag nahi karna chahiye kyunki woh equivalence notes lagane ke baad semantically match karte hain.
- severity_by_metric har mismatched metric name ko uski severity se map kare.
- reason_class_by_metric dashboard export ke har metric ko, semantically matching metrics samet, in labels mein se exactly ek se map kare:
  semantically_equivalent, revenue_formula_mismatch, denominator_mismatch, time_basis_mismatch, window_mismatch, field_mismatch, distinctness_mismatch, missing_filter.
- Jab average, latency, ya duration metric timestamp fields substitute karke galat lifecycle interval measure kare, tab `time_basis_mismatch` use karein, bhale isse field names bhi badalte hon. `field_mismatch` ko non-time fields, jaise opted_in_users versus email_opted_in_users, ke liye rakhein.

Network access ya external APIs use na karein.
''',r'''Approved metric definitions ke against dashboard export audit karo.

Inputs:
- $WORKSPACE/in/metric_definitions.md
- $WORKSPACE/in/dashboard_export.csv

Banao:
- $WORKSPACE/out/metric_audit.csv
- $WORKSPACE/out/equivalence_audit.json

Output columns, isi exact order mein:
metric_name,dashboard_formula,approved_formula,affected_field,severity

Rules:
1. Fixtures modify mat karo.
2. Sirf woh metrics include karo jinka dashboard formula approved definition se conflict karta hai.
3. Approved definition se semantically match karne wale metrics flag mat karo. Metric conflict karta hai ya nahi decide karne se pehle metric_definitions.md ke equivalent formula notes apply karo.
4. Revenue, conversion, ya cohort-retention denominator errors ki severity high ho; average/latency/window ya operational SLA denominator errors ki medium; baaki ki low.
5. Conflicting metrics ke `dashboard_formula`, `approved_formula`, aur `affected_field` ka text source files se directly copy karo.
6. metric_audit.csv valid CSV ho. Commas wale fields quote karo.

equivalence_audit.json requirements:
- `mismatched_metrics`, `semantically_matching_metrics`, `severity_by_metric`, `reason_class_by_metric` keys wala valid JSON.
- mismatched_metrics, metric_audit.csv mein shamil sorted metric names hon.
- semantically_matching_metrics, dashboard export ke sorted metric names hon jinhe flag nahi karna kyunki equivalence notes apply karne ke baad semantically match hote hain.
- severity_by_metric har mismatched metric name ko uski severity se map kare.
- reason_class_by_metric dashboard export ke har metric ko, semantically matching metrics samet, in labels mein se exactly ek se map kare:
  semantically_equivalent, revenue_formula_mismatch, denominator_mismatch, time_basis_mismatch, window_mismatch, field_mismatch, distinctness_mismatch, missing_filter.
- Average, latency, ya duration metric timestamp fields substitute karke galat lifecycle interval measure kare toh `time_basis_mismatch` use karo, bhale field names bhi badalte hon. `field_mismatch` ko non-time fields, jaise opted_in_users versus email_opted_in_users, ke liye rakho.

Network access ya external APIs use mat karo.
'''),
('053-anomalous-transaction-detect','prompt.txt'):(r'''Local rulebook se suspicious transactions detect karein.

Inputs:
- $WORKSPACE/in/transactions.csv
- $WORKSPACE/in/rules.md

Banayein:
- $WORKSPACE/out/suspicious_transactions.csv
- $WORKSPACE/out/rule_audit.json
- $WORKSPACE/out/case_notes.md

suspicious_transactions.csv ke columns, isi exact order mein:
transaction_id,customer_id,rule_id,risk_level,reason

Rules:
1. Fixtures modify na karein.
2. Sirf rules.md mein diye rules apply karein.
3. Har us transaction ko include karein jo kam-se-kam ek rule trigger kare.
4. Transaction multiple rules trigger kare, toh highest-risk rule use karein aur `reason` mein anya triggered rule ids ka zikr karein.
5. Koi rule trigger na karne wale transactions include na karein.
6. Card velocity ke liye transactions ko CSV row order ke bajay timestamp se evaluate karein.
7. case_notes.md mein suspicious transactions ki sankhya summarize karein aur har triggered rule_id ka zikr karein.

rule_audit.json requirements:
- `suspicious_transaction_ids`, `non_suspicious_transaction_ids`, `rule_counts`, `secondary_rule_ids` keys wala valid JSON.
- suspicious_transaction_ids aur non_suspicious_transaction_ids sorted arrays hon.
- rule_counts, har rule_id ko un suspicious transactions ki sankhya se map kare jahan woh primary rule_id hai.
- secondary_rule_ids sirf un multi-rule transaction_ids ko map kare jo CSV reason mein mention kiye gaye anya triggered rule ids ke sorted arrays se hon.

Network access ya external APIs use na karein.
''',r'''Local rulebook se suspicious transactions detect karo.

Inputs:
- $WORKSPACE/in/transactions.csv
- $WORKSPACE/in/rules.md

Banao:
- $WORKSPACE/out/suspicious_transactions.csv
- $WORKSPACE/out/rule_audit.json
- $WORKSPACE/out/case_notes.md

suspicious_transactions.csv ke columns, isi exact order mein:
transaction_id,customer_id,rule_id,risk_level,reason

Rules:
1. Fixtures modify mat karo.
2. Sirf rules.md mein diye rules apply karo.
3. Har transaction include karo jo kam-se-kam ek rule trigger karta hai.
4. Transaction multiple rules trigger kare toh highest-risk rule use karo aur `reason` mein baaki triggered rule ids mention karo.
5. Koi rule trigger na karne wale transactions include mat karo.
6. Card velocity ke liye transactions ko CSV row order se nahi, timestamp ke hisaab se evaluate karo.
7. case_notes.md mein suspicious transactions ki count summarize karo aur har triggered rule_id mention karo.

rule_audit.json requirements:
- `suspicious_transaction_ids`, `non_suspicious_transaction_ids`, `rule_counts`, `secondary_rule_ids` keys wala valid JSON.
- suspicious_transaction_ids aur non_suspicious_transaction_ids sorted arrays hon.
- rule_counts har rule_id ko un suspicious transactions ki count se map kare jahan woh primary rule_id hai.
- secondary_rule_ids sirf multi-rule transaction_ids ko CSV reason mein mentioned baaki triggered rule ids ke sorted arrays se map kare.

Network access ya external APIs use mat karo.
'''),
('057-interruption-resume','prompt_round1.txt'):(r'''Round 1 of 2: interrupted case review shuru karein.

Input files $WORKSPACE/in ke andar hain:
- case_queue.json mein saare review items unke required order mein hain.
- interruption_notice.json batata hai ki simulated interruption kahan hota hai.

Sirf $WORKSPACE/out/state.json banayein. Is round mein $WORKSPACE/out/final_result.json na banayein.

Queue ke bilkul pehle teen items, C-101 se C-103 tak, process karein. Har processed item ke liye calculate karein:
- risk_score = impact * likelihood
- jab risk_score >= 12 ho toh action = "escalate", warna "monitor"

$WORKSPACE/out/state.json valid JSON ho aur ismein ye hon:
- schema_version: 1
- run_id: "resume-drill-74"
- completed_ids: ["C-101", "C-102", "C-103"]
- queue ke baaki items ko order mein rakhne wala pending_ids
- teen completed items ke per_item_results
- Har completed item ke liye ek entry wala processing_log; har entry mein id, step: "round1", aur source_file: "case_queue.json" hon
- interrupted_after_id: "C-103"

Input files modify na karein.
''',r'''Round 1 of 2: interrupted case review start karo.

Input files $WORKSPACE/in mein hain:
- case_queue.json mein saare review items required order mein hain.
- interruption_notice.json batata hai simulated interruption kahan aata hai.

Sirf $WORKSPACE/out/state.json banao. Is round mein $WORKSPACE/out/final_result.json mat banao.

Queue ke exactly pehle three items, C-101 se C-103 tak, process karo. Har processed item ke liye calculate karo:
- risk_score = impact * likelihood
- risk_score >= 12 ho toh action = "escalate", warna "monitor"

$WORKSPACE/out/state.json valid JSON ho aur ismein ye hon:
- schema_version: 1
- run_id: "resume-drill-74"
- completed_ids: ["C-101", "C-102", "C-103"]
- Queue ke remaining items ko order mein rakhne wala pending_ids
- Completed teen items ke per_item_results
- Har completed item ke liye ek entry wala processing_log; har entry mein id, step: "round1", aur source_file: "case_queue.json" hon
- interrupted_after_id: "C-103"

Input files modify mat karo.
'''),
('057-interruption-resume','prompt_round2.txt'):(r'''Round 2 of 2: saved state se resume karein.

Round 1 ka existing $WORKSPACE/out/state.json, $WORKSPACE/in/case_queue.json, aur $WORKSPACE/in/operator_patch.json padhein. Saved pending_ids se aage badhein; pehle complete kiye gaye C-101 se C-103 tak ke kaam ko carry forward karne ke alawa dobara calculate ya rewrite na karein.

Banayein ya update karein:
- $WORKSPACE/out/state.json
- $WORKSPACE/out/final_result.json

$WORKSPACE/out/state.json mein ab paanchon completed ids aur empty pending_ids list honi chahiye. Scoring se pehle pending items par valid operator patches apply karein. Duplicate patch_id values ko pehli application ke baad ignore karein aur unknown ids ke patches ignore karein. Iske processing_log mein reused/skipped preexisting work, applied patches, ignored patches, aur newly processed round2 work alag-alag dikhna chahiye.

$WORKSPACE/out/final_result.json valid JSON ho aur ismein ye hon:
- run_id: "resume-drill-74"
- resumed_from_state: true
- total_items: 5
- Queue order mein completed_ids
- risk_score >= 12 wale ids ke escalations
- risk_score < 12 wale ids ke monitor_ids
- aggregate_risk_score: sabhi item risk scores ka sum
- skipped_preexisting_ids aur newly_processed_ids wala resume_audit
- applied_patch_ids, ignored_patch_ids, aur ignored_reasons wala patch_audit

Saath hi $WORKSPACE/out/resume_audit.md banayein, jisme preserved history, patch handling, aur idempotent resume behavior summarize ho.

Input files modify na karein. Network-dependent output na banayein.
''',r'''Round 2 of 2: saved state se resume karo.

Round 1 ka existing $WORKSPACE/out/state.json, $WORKSPACE/in/case_queue.json aur $WORKSPACE/in/operator_patch.json padho. Saved pending_ids se continue karo; pehle complete hue C-101 se C-103 ke kaam ko carry forward karne ke alawa dobara compute ya rewrite mat karo.

Banao ya update karo:
- $WORKSPACE/out/state.json
- $WORKSPACE/out/final_result.json

$WORKSPACE/out/state.json mein ab saare five completed ids aur empty pending_ids list honi chahiye. Scoring se pehle pending items par valid operator patches apply karo. Duplicate patch_id values ko first application ke baad ignore karo aur unknown ids ke patches ignore karo. Iske processing_log mein reused/skipped preexisting work, applied patches, ignored patches aur newly processed round2 work ko alag-alag identify karo.

$WORKSPACE/out/final_result.json valid JSON ho aur ismein ye hon:
- run_id: "resume-drill-74"
- resumed_from_state: true
- total_items: 5
- Queue order mein completed_ids
- risk_score >= 12 wale ids ke escalations
- risk_score < 12 wale ids ke monitor_ids
- aggregate_risk_score: sab item risk scores ka sum
- skipped_preexisting_ids aur newly_processed_ids wala resume_audit
- applied_patch_ids, ignored_patch_ids aur ignored_reasons wala patch_audit

Saath mein $WORKSPACE/out/resume_audit.md banao, jisme preserved history, patch handling aur idempotent resume behavior summarize ho.

Input files modify mat karo. Network-dependent output mat banao.
'''),
('058-multiday-project-state','prompt_day1.txt'):(r'''Day 1 of 3: project state initialize karein.

$WORKSPACE/in/day1_brief.json padhein. Ye files banayein ya update karein:
- $WORKSPACE/out/project_log.md
- $WORKSPACE/out/final_plan.json

Day 1 ke liye baseline scope, owners, milestones, risks, tentative decisions, aur open questions capture karein. $WORKSPACE/out/final_plan.json mein Day 1 entry wala change_history array aur decisions array hona chahiye. Pilot scope tentative ho toh mark karein, taaki baad ke din use audit history khoye bina reverse kar saken. Fixture se aage ki dates invent na karein; fixture ke relative day labels use karein.

Input files modify na karein.
''',r'''Day 1 of 3: project state initialize karo.

$WORKSPACE/in/day1_brief.json padho. Ye files banao ya update karo:
- $WORKSPACE/out/project_log.md
- $WORKSPACE/out/final_plan.json

Day 1 ke liye baseline scope, owners, milestones, risks, tentative decisions aur open questions capture karo. $WORKSPACE/out/final_plan.json mein Day 1 entry wala change_history array aur decisions array hona chahiye. Koi pilot scope tentative ho toh mark karo, taaki later days mein audit history khoye bina use reverse kiya ja sake. Fixture se aage ki dates invent mat karo; fixture ke relative day labels use karo.

Input files modify mat karo.
'''),
('058-multiday-project-state','prompt_day2.txt'):(r'''Day 2 of 3: Day 1 ki history preserve karte hue nayi jaankari shamil karein.

Pehle existing $WORKSPACE/out/project_log.md aur $WORKSPACE/out/final_plan.json padhein, phir $WORKSPACE/in/day2_update.json padhein. Dono outputs update karein.

Day 2 update mein ye record hona chahiye:
- analytics connector ke liye vendor delay
- budget reduction to 92000
- nayi compliance review requirement
- data migration ke liye owner change, Priya ko
- in-app experimentation par stakeholder conflict

change_history mein append karein; Day 1 entry erase na karein. Input files modify na karein.
''',r'''Day 2 of 3: Day 1 history preserve karke nayi information include karo.

Pehle existing $WORKSPACE/out/project_log.md aur $WORKSPACE/out/final_plan.json padho, phir $WORKSPACE/in/day2_update.json padho. Dono outputs update karo.

Day 2 update mein ye record hona chahiye:
- analytics connector ke liye vendor delay
- budget reduction to 92000
- nayi compliance review requirement
- data migration ka owner change, Priya ko
- in-app experimentation par stakeholder conflict

change_history mein append karo; Day 1 entry erase mat karo. Input files modify mat karo.
'''),
('058-multiday-project-state','prompt_day3.txt'):(r'''Day 3 of 3: plan final karein.

Current outputs aur $WORKSPACE/in/day3_update.json padhein. Inki final versions banayein:
- $WORKSPACE/out/project_log.md
- $WORKSPACE/out/final_plan.json

Final plan mein Day 1, Day 2, aur Day 3 ki saari jaankari shamil honi chahiye. Ismein ye hona chahiye:
- Day 1, Day 2, aur Day 3 ke liye status_by_day
- Exactly three day-level entries wala change_history
- Vendor delay aur security signoff ke liye adjusted milestones
- R-connect-delay, R-budget, R-compliance, aur R-security wala risk_register
- final_budget: 92000
- launch_recommendation: "conditional_go"
- Compliance review, security signoff, aur connector sandbox delivery ki conditions
- decision_register.csv, header: decision_id,day,decision,status,reverses,source
- Reversed decisions ko delete karne ke bajay audit trail mein preserve karein

Input files modify na karein. External services use na karein.

TIMEOUT AUR SCORE FAILURES SE BACHNE KE LIYE MAHATTVAPOORN NIRDESH:
1. Connection timeouts rokne ke liye saare file writes ek hi combined tool call response mein generate karna ZAROORI hai. Ek file likhkar rukna aur phir doosri likhna mana hai.
2. `final_plan.json` mein root-level key ka exact naam `"owners"` hona ZAROORI hai aur woh dictionary se mapped ho (jaise, `"owners": {"WS-data": "Priya", ...}`).
3. `final_plan.json` mein root-level key ka exact naam `"conditions"` hona ZAROORI hai aur woh strings ki list se mapped ho.
''',r'''Day 3 of 3: plan finalize karo.

Current outputs aur $WORKSPACE/in/day3_update.json padho. Inki final versions banao:
- $WORKSPACE/out/project_log.md
- $WORKSPACE/out/final_plan.json

Final plan mein Day 1, Day 2 aur Day 3 ki saari information honi chahiye. Ismein ye shamil ho:
- Day 1, Day 2 aur Day 3 ke liye status_by_day
- Exactly three day-level entries wala change_history
- Vendor delay aur security signoff ke liye adjusted milestones
- R-connect-delay, R-budget, R-compliance aur R-security wala risk_register
- final_budget: 92000
- launch_recommendation: "conditional_go"
- Compliance review, security signoff aur connector sandbox delivery ki conditions
- decision_register.csv, header: decision_id,day,decision,status,reverses,source
- Reversed decisions ko delete karne ki jagah audit trail mein preserve karo

Input files modify mat karo. External services use mat karo.

TIMEOUT AUR SCORE FAILURES SE BACHNE KE LIYE IMPORTANT INSTRUCTIONS:
1. Connection timeouts avoid karne ke liye saare file writes ek hi combined tool call response mein generate karna MUST hai. Ek file likhkar rukna aur phir doosri likhna mat.
2. `final_plan.json` mein exact root-level key `"owners"` ko dictionary se map karna MUST hai (jaise, `"owners": {"WS-data": "Priya", ...}`).
3. `final_plan.json` mein exact root-level key `"conditions"` ko strings ki list se map karna MUST hai.
'''),
}
