"""AI translations, self-reviewed against each original English instruction.

No private oracle answers are used in the prompts. Literal contracts are fixed.
"""
TEXT = {
'056-inventory-forecast': {
'hi': '''स्थानीय बिक्री और स्टॉक फ़ाइलों से दो सप्ताह की इन्वेंटरी पुनः ऑर्डर योजना बनाएं।

इनपुट:
- $WORKSPACE/in/sales_history.csv
- $WORKSPACE/in/stock.json

बनाएं:
- $WORKSPACE/out/reorder_plan.csv
- $WORKSPACE/out/inventory_exceptions.json
- $WORKSPACE/out/forecast_notes.md

reorder_plan.csv में कॉलम इसी क्रम में हों:
sku,avg_weekly_sales,forecast_14d,current_stock,safety_stock,reorder_qty,risk_level

नियम:
1. फ़िक्स्चर न बदलें।
2. stock.json के हर SKU को शामिल करें, चाहे उसकी sales_history पंक्तियां न हों।
3. हर sku का avg_weekly_sales उसकी सभी इतिहास पंक्तियों के units_sold का औसत है। इतिहास न होने पर avg_weekly_sales और forecast_14d दोनों 0.00 हों; forecast_notes.md में इसका उल्लेख करें।
4. stock.json में न मिलने वाले SKU की sales_history पंक्तियां छोड़ दें और ऐसे SKU को छोड़ा गया बताएं।
5. forecast_14d = avg_weekly_sales * 2.
6. target_stock = forecast_14d + safety_stock.
7. reorder_qty = max(0, target_stock - current_stock); इसे stock.json में दिए sku के pack_size के अगले गुणज तक ऊपर पूर्णांकित करें। कभी नीचे या निकटतम गुणज तक पूर्णांकित न करें।
8. current_stock < target_stock होने पर risk_level high है; target_stock के बराबर या उससे ठीक एक pack_size तक अधिक होने पर medium है; अन्यथा low है।
9. avg_weekly_sales और forecast_14d में ठीक दो दशमलव स्थान रखें। current_stock, safety_stock और reorder_qty पूर्णांक स्ट्रिंग हों।
10. forecast_notes.md में पूर्वानुमान अवधि, high-risk SKU, इतिहास रहित SKU और pack-size पूर्णांकन नियम का उल्लेख करें।

inventory_exceptions.json की आवश्यकताएं:
- वैध JSON की कुंजियां हों: high_risk_skus, missing_history_skus, skipped_history_skus, medium_boundary_skus, more_than_one_pack_low_skus, pack_rounding_cases.
- पहली पांच कुंजियों के मान आरोही क्रम में सॉर्ट किए गए ऐरे हों।
- more_than_one_pack_low_skus में केवल वे SKU शामिल करें जिनका current stock, target_stock से ठीक एक pack_size से भी अधिक ऊपर है। हर low-risk SKU को शामिल न करें, जब तक वह इस सीमा शर्त को पूरा न करे।
- pack_rounding_cases ऐसा ऑब्जेक्ट हो जो गैर-शून्य reorder_qty वाले हर SKU को उसकी reorder_qty स्ट्रिंग से मैप करे।
- यह ऑडिट आर्टिफ़ैक्ट reorder_plan.csv और forecast_notes.md से सुसंगत हो।

नेटवर्क या बाहरी API का उपयोग न करें।''',
'hinglish': '''Local sales aur stock files se two-week inventory reorder plan banao.

Inputs:
- $WORKSPACE/in/sales_history.csv
- $WORKSPACE/in/stock.json

Banao:
- $WORKSPACE/out/reorder_plan.csv
- $WORKSPACE/out/inventory_exceptions.json
- $WORKSPACE/out/forecast_notes.md

reorder_plan.csv ke columns isi exact order mein hon:
sku,avg_weekly_sales,forecast_14d,current_stock,safety_stock,reorder_qty,risk_level

Rules:
1. Fixtures ko modify mat karo.
2. stock.json ka har SKU include karo, bhale uski sales_history rows na hon.
3. Har sku ka avg_weekly_sales uski saari history rows ke units_sold ka average hai. History na ho to avg_weekly_sales aur forecast_14d dono 0.00 hon; forecast_notes.md mein mention karo.
4. Jo SKU stock.json mein nahi hain unki sales_history rows ignore karo aur unhe skipped mention karo, agar aise SKU hon.
5. forecast_14d = avg_weekly_sales * 2.
6. target_stock = forecast_14d + safety_stock.
7. reorder_qty = max(0, target_stock - current_stock), stock.json mein us sku ke pack_size ke next multiple tak round up karo. Kabhi round down ya nearest par round mat karo.
8. current_stock < target_stock par risk_level high hai; target_stock ke equal ya usse exactly ek pack_size tak above par medium hai; warna low hai.
9. avg_weekly_sales aur forecast_14d exactly two decimals mein hon. current_stock, safety_stock aur reorder_qty integer strings hon.
10. forecast_notes.md mein forecast window, high-risk SKUs, missing-history SKU aur pack-size rounding rule mention karo.

inventory_exceptions.json requirements:
- Valid JSON keys: high_risk_skus, missing_history_skus, skipped_history_skus, medium_boundary_skus, more_than_one_pack_low_skus, pack_rounding_cases.
- Pehli paanch keys ke arrays ascending sorted hon.
- more_than_one_pack_low_skus mein sirf woh SKU hon jinka current stock target_stock se exactly ek pack_size se bhi zyada above hai. Har low-risk SKU include mat karo jab tak woh yeh boundary case satisfy na kare.
- pack_rounding_cases object har nonzero reorder_qty wale SKU ko uski reorder_qty string se map kare.
- Yeh audit artifact reorder_plan.csv aur forecast_notes.md se consistent ho.

Network access ya external APIs use mat karo.'''},
'073-research-repro-package': {
'hi': '''आप एक शोध पुनरुत्पादनीयता पैकेज का ऑडिट कर रहे हैं।

पढ़ें:
- $WORKSPACE/in/README.md
- $WORKSPACE/in/scripts/*
- $WORKSPACE/in/results.csv
- $WORKSPACE/in/paper_claims.md

पैकेज में जानबूझकर खराब ऑटोमेशन, गायब मूल इनपुट, प्रकाशित मेट्रिक में असंगतियां और जमा पैकेज से गायब Appendix आर्टिफ़ैक्ट मिले हुए हैं।

बनाएं:
- $WORKSPACE/out/reproducibility_report.md
- $WORKSPACE/out/missing_steps.csv

reproducibility_report.md की आवश्यकताएं:
- हर पेपर दावे के लिए एक Markdown अनुभाग रखें, शीर्षक ठीक `### Claim CLAIM-X` हो (उदाहरण: `### Claim CLAIM-1`, …, `### Claim CLAIM-4`)।
- हर अनुभाग में दावे को अपेक्षित आर्टिफ़ैक्ट (`results.csv`, स्क्रिप्ट, subgroup CSV पथ) से जोड़ें और ईमानदारी से बताएं कि क्या साक्ष्य पुनरुत्पादनीयता का समर्थन करते हैं।
- समझाएं कि आज दिए पैकेज से मुख्य निष्कर्ष शुरू से अंत तक पुनरुत्पादित क्यों नहीं हो सकते (गायब raw bundle, खराब driver script, CSV/पेपर अंतर, गायब subgroup tables)।
- retention lift के संख्यात्मक अंतर (पेपर बनाम `results.csv`) को स्पष्ट रूप से CLAIM-2 से जोड़ें; दोबारा रन के लॉग न गढ़ें।

missing_steps.csv की आवश्यकताएं:
- पहली पंक्ति ठीक यह हो: item,type,impact,recommended_fix
- कम से कम 4 पंक्तियां दें; हर पंक्ति में impact और recommended_fix गैर-रिक्त हों।
- पंक्तियां मिलकर ये सभी अंतराल कवर करें:
  1. README में बताए trial-level raw inputs गायब हैं।
  2. analysis driver (`analyze_main.py`) काम नहीं करता / उसका syntax खराब है।
  3. पेपर CLAIM-2 और दिए `results.csv` में मेट्रिक/टेबल असंगति है (`retention_lift`)।
  4. Appendix D subgroup आर्टिफ़ैक्ट (`results/subgroup_ablation.csv`) गायब है।
  इन अंतरालों को संक्षिप्त item/type शब्दों में लिखें—ओरेकल सामान्यीकृत keywords जांचता है।

निष्पादन परिणाम न गढ़ें और दोबारा रन सफल होने का दावा न करें।
नेटवर्क का उपयोग न करें। इनपुट फ़ाइलें न बदलें।''',
'hinglish': '''Tum ek research reproducibility package audit kar rahe ho.

Padho:
- $WORKSPACE/in/README.md
- $WORKSPACE/in/scripts/*
- $WORKSPACE/in/results.csv
- $WORKSPACE/in/paper_claims.md

Package mein jaanboojhkar broken automation, missing raw inputs, published metric mismatches aur deposit se absent Appendix artifacts ka mix hai.

Banao:
- $WORKSPACE/out/reproducibility_report.md
- $WORKSPACE/out/missing_steps.csv

reproducibility_report.md requirements:
- Har paper claim ke liye ek Markdown section ho, heading exactly `### Claim CLAIM-X` (examples: `### Claim CLAIM-1`, …, `### Claim CLAIM-4`).
- Har section mein claim ko expected artifacts (`results.csv`, scripts, subgroup CSV paths) se map karo aur honestly batao kya evidence reproducibility support karta hai.
- Explain karo ki aaj shipped package se main headline findings end-to-end reproduce kyun nahi ho sakti (missing raw bundle, corrupt driver script, CSV/paper deltas, absent subgroup tables).
- Retention lift ka numerical disagreement (paper vs `results.csv`) explicitly CLAIM-2 se jodo; rerun logs invent mat karo.

missing_steps.csv requirements:
- First row exactly: item,type,impact,recommended_fix
- Kam se kam 4 rows do; har row ka impact aur recommended_fix non-empty ho.
- Rows milkar cover karen:
  1. README ke referenced trial-level raw inputs missing hain.
  2. Non-functional / syntax-corrupted analysis driver (`analyze_main.py`).
  3. Paper CLAIM-2 aur shipped `results.csv` ka metric/table mismatch (`retention_lift`).
  4. Missing Appendix D subgroup artifact (`results/subgroup_ablation.csv`).
  In gaps ko concise item/type wording mein likho—oracle normalized keywords check karta hai.

Execution results fabricate mat karo ya reruns succeeded pretend mat karo.
Network use mat karo. Input files modify mat karo.'''},
'089-ab-test-caveat-analysis': {
'hi': '''केवल स्थानीय फ़ाइलों से A/B परीक्षण का विश्लेषण करें।

इनपुट:
- $WORKSPACE/in/experiment_cells.csv
- $WORKSPACE/in/exclusions.csv
- $WORKSPACE/in/analysis_plan.md

ठीक ये बनाएं:
- $WORKSPACE/out/variant_metrics.csv
- $WORKSPACE/out/ab_summary.json
- $WORKSPACE/out/exclusion_ledger.csv
- $WORKSPACE/out/recommendation.md

नियम:
1. इनपुट फ़ाइलें न बदलें।
2. बताए exclusions लागू करने के बाद experiment_cells.csv के eligible_users और conversions का उपयोग करें।
3. conversion_rate = conversions / eligible_users, refund_rate = refunds / conversions और revenue_per_eligible_user = revenue_usd / eligible_users निकालें।
4. B बनाम A के लिए two-proportion z-test उपयोग करें; two-sided, alpha = 0.05.
5. दरों और lift मानों को चार दशमलव स्थान तक पूर्णांकित करें। revenue_per_eligible_user, z_stat और p_value भी चार दशमलव स्थान तक हों।
6. variant_metrics.csv का हेडर ठीक यह हो:
   variant,eligible_users,conversions,conversion_rate,refund_rate,revenue_per_eligible_user
7. ab_summary.json में हों: control_variant, treatment_variant, alpha, lift_absolute, lift_relative, z_stat, p_value, significant, recommendation.
8. exclusion_ledger.csv का हेडर ठीक यह हो:
   user_id,reason,variant,notes
   exclusions.csv की हर पंक्ति शामिल करें और इनपुट क्रम बनाए रखें।
9. recommendation.md में बताएं कि launch करना चाहिए या नहीं, statistical significance का उल्लेख करें, और underpowered mobile cohort तथा duplicate assignment cleanup की सावधानियां शामिल करें।

नेटवर्क या बाहरी API का उपयोग न करें।''',
'hinglish': '''Sirf local files se A/B test analyze karo.

Inputs:
- $WORKSPACE/in/experiment_cells.csv
- $WORKSPACE/in/exclusions.csv
- $WORKSPACE/in/analysis_plan.md

Exactly yeh banao:
- $WORKSPACE/out/variant_metrics.csv
- $WORKSPACE/out/ab_summary.json
- $WORKSPACE/out/exclusion_ledger.csv
- $WORKSPACE/out/recommendation.md

Rules:
1. Input files modify mat karo.
2. Listed exclusions apply karne ke baad experiment_cells.csv ke eligible_users aur conversions use karo.
3. conversion_rate = conversions / eligible_users, refund_rate = refunds / conversions aur revenue_per_eligible_user = revenue_usd / eligible_users calculate karo.
4. B versus A ke liye two-proportion z-test use karo, two-sided, alpha = 0.05.
5. Rates aur lift values four decimals tak round karo. revenue_per_eligible_user, z_stat aur p_value bhi four decimals tak round karo.
6. variant_metrics.csv ka exact header:
   variant,eligible_users,conversions,conversion_rate,refund_rate,revenue_per_eligible_user
7. ab_summary.json mein hon: control_variant, treatment_variant, alpha, lift_absolute, lift_relative, z_stat, p_value, significant, recommendation.
8. exclusion_ledger.csv ka exact header:
   user_id,reason,variant,notes
   exclusions.csv ki har row input order preserve karke include karo.
9. recommendation.md mein batao launch karna hai ya nahi, statistical significance mention karo aur underpowered mobile cohort aur duplicate assignment cleanup ke caveats include karo.

Network access ya external APIs use mat karo.'''},
'106-release-approval-gate-plan': {
'hi': '''रिलीज़ अनुमोदन गेट पैकेज बनाएं।

पढ़ें:
- $WORKSPACE/in/release_manifest.json
- $WORKSPACE/in/approval_policy.md
- $WORKSPACE/in/preflight_checks.json
- $WORKSPACE/in/risk_register.csv
- $WORKSPACE/in/change_calendar.csv
- $WORKSPACE/in/incident_history.json
- $WORKSPACE/in/rollback_runbook.md

बनाएं:
- $WORKSPACE/out/approval_packet.json
- $WORKSPACE/out/blockers.csv
- $WORKSPACE/out/pending_actions.md
- $WORKSPACE/out/audit_trail.md

आवश्यकताएं:
- निर्धारित करें कि रिलीज़ go, conditional_go या blocked है।
- नीति और साक्ष्य फ़ाइलों से सभी hard blockers पहचानें।
- approval_packet.json में release_id, decision, blocker_ids, required_approvals, pending_actions, evidence_refs और not_executed_statement शामिल हों।
- blockers.csv में blocker_id, severity, owner_role, evidence_ref, required_approval_or_action और rationale शामिल हों।
- pending_actions.md में केवल प्रस्तावित या लंबित कार्रवाइयां सूचीबद्ध करें जिनके लिए अनुमोदन चाहिए।
- audit_trail.md में हर blocker और निर्णय को स्थानीय साक्ष्य से जोड़ें।
- इनपुट फ़ाइलें न बदलें। नेटवर्क का उपयोग न करें।
- यह केवल योजना और अनुमोदन पैकेज है। ऐसा दावा न करें कि production operations, rollback, deploy, feature flag changes या paging actions पहले ही निष्पादित हो चुके हैं।''',
'hinglish': '''Release approval gate package banao.

Padho:
- $WORKSPACE/in/release_manifest.json
- $WORKSPACE/in/approval_policy.md
- $WORKSPACE/in/preflight_checks.json
- $WORKSPACE/in/risk_register.csv
- $WORKSPACE/in/change_calendar.csv
- $WORKSPACE/in/incident_history.json
- $WORKSPACE/in/rollback_runbook.md

Banao:
- $WORKSPACE/out/approval_packet.json
- $WORKSPACE/out/blockers.csv
- $WORKSPACE/out/pending_actions.md
- $WORKSPACE/out/audit_trail.md

Requirements:
- Decide karo release go, conditional_go ya blocked hai.
- Policy aur evidence files se saare hard blockers identify karo.
- approval_packet.json mein release_id, decision, blocker_ids, required_approvals, pending_actions, evidence_refs aur not_executed_statement hon.
- blockers.csv mein blocker_id, severity, owner_role, evidence_ref, required_approval_or_action aur rationale hon.
- pending_actions.md mein sirf proposed ya pending actions list karo jinhe approval chahiye.
- audit_trail.md har blocker aur decision ko local evidence se map kare.
- Input files modify mat karo. Network use mat karo.
- Yeh sirf planning aur approval package hai. Production operations, rollback, deploy, feature flag changes ya paging actions already executed hone ka claim mat karo.'''}
}
