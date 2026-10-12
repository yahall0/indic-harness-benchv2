"""Hand-written Hindi and Hinglish variants for local data tasks."""
TRANSLATIONS = {
('049-excel-like-cleaning','prompt.txt'):(r'''Aap finance reconciliation review ke liye messy sales export clean kar rahe hain. Sirf local files use karein.

Workspace root mein copy kiye gaye inputs:
- $WORKSPACE/in/messy_sales.csv
- $WORKSPACE/in/customer_dictionary.csv
- $WORKSPACE/in/fx_rates.csv

Bilkul ye outputs banayein:
- $WORKSPACE/out/cleaned_sales.csv
- $WORKSPACE/out/reject_ledger.csv
- $WORKSPACE/out/reject_summary.json
- $WORKSPACE/out/cleaning_report.md

Cleaning rules:
1. Input files modify na karein.
2. `customer_id` ko customer_dictionary.csv ke against validate karein. Unknown ya inactive `customer_id` wali rows reject karein.
3. `order_date` ko row ke locale ke mutabik parse karein:
   - `en_US` dates month/day/year hoti hain.
   - `en_GB` aur `de_DE` dates day/month/year hoti hain.
   - ISO dates pehle se year-month-day format mein hain.
   - Month names wali dates, jaise "10-Jan-2025", valid hain.
4. `status` ko lowercase mein normalize karein. Refund/returned rows ka amount_usd negative hi rehna chahiye.
5. `fx_rates.csv` se `amount` ko USD mein normalize karein. `amount` field row ka total hai, unit price nahi. Currency symbols aur accounting parentheses hataayein. `en_US`/`en_GB` ke liye comma thousands separator aur dot decimal separator hai. `de_DE` ke liye dot thousands separator aur comma decimal separator hai. amount_usd ko exactly two decimals tak round karein.
6. `quantity` positive integer hona chahiye.
7. Validation ke baad `order_id` ke basis par deduplicate karein. Input order mein pehli valid occurrence rakhein aur baad ki valid duplicates ko reason duplicate_order_id se reject karein. Invalid rows ko duplicate_order_id ke bajay unke validation reason se reject karein.
8. Invalid dates, unsupported currency, missing/non-numeric amounts, invalid quantities, unknown/inactive customers, ya duplicates wali rows reject karein.
9. Ek row mein multiple reject reasons hon, toh is priority order mein pehla applicable reason record karein:
   missing_amount, unsupported_currency, invalid_quantity, inactive_customer, unknown_customer, invalid_date, duplicate_order_id.
10. Refund/returned rows ka amount_usd bilkul ek baar negative hona chahiye: positive returned amount ko negative karein, aur pehle se negative returned amount ko negative hi rakhein.

cleaned_sales.csv requirements:
- Exact header:
  order_id,order_date,customer_id,customer_name,sku,quantity,amount_usd,status
- Rows ko order_date phir order_id ke hisaab se sort karein.
- Extra columns include na karein.

reject_ledger.csv requirements:
- Exact header:
  order_id,reason,source_row,notes
- Har rejected input row ke liye ek row include karein. source_row, messy_sales.csv mein header ko chhodkar 1-based data-row number hai.
- Rule 9 mein diye gaye reason codes mein se ek use karein.

reject_summary.json requirements:
- Valid JSON object ho jo rule 9 ke har reason code ke liye keyed ho, zero-count reasons samet.
- Har reason entry mein count, source_rows, aur order_ids hon.
- source_rows, ascending input order mein numeric arrays hon.

cleaning_report.md requirements:
- Valid row count, rejected row count, duplicate count, aur total amount_usd summarize karein.
- Har reject reason category samjhayen.
- Use ki gayi locale ya FX assumptions ka zikr karein.

Network access ya external APIs use na karein.
''',r'''Finance reconciliation review ke liye messy sales export clean kar rahe ho. Sirf local files use karo.

Workspace root mein copied inputs:
- $WORKSPACE/in/messy_sales.csv
- $WORKSPACE/in/customer_dictionary.csv
- $WORKSPACE/in/fx_rates.csv

Exactly ye outputs banao:
- $WORKSPACE/out/cleaned_sales.csv
- $WORKSPACE/out/reject_ledger.csv
- $WORKSPACE/out/reject_summary.json
- $WORKSPACE/out/cleaning_report.md

Cleaning rules:
1. Input files modify mat karo.
2. `customer_id` ko customer_dictionary.csv se validate karo. Unknown ya inactive `customer_id` wali rows reject karo.
3. `order_date` ko row ke locale ke according parse karo:
   - `en_US` dates month/day/year hoti hain.
   - `en_GB` aur `de_DE` dates day/month/year hoti hain.
   - ISO dates already year-month-day format mein hain.
   - Month names wali dates, jaise "10-Jan-2025", valid hain.
4. `status` ko lowercase mein normalize karo. Refund/returned rows mein amount_usd negative rehna chahiye.
5. `fx_rates.csv` ke through `amount` ko USD mein normalize karo. `amount` field row total hai, unit price nahi. Currency symbols aur accounting parentheses strip karo. `en_US`/`en_GB` mein comma thousands separator aur dot decimal separator hai. `de_DE` mein dot thousands separator aur comma decimal separator hai. amount_usd ko exactly two decimals tak round karo.
6. `quantity` positive integer hona chahiye.
7. Validation ke baad `order_id` ke basis par deduplicate karo. Input order mein first valid occurrence rakho aur later valid duplicates ko reason duplicate_order_id ke saath reject karo. Invalid rows ko duplicate_order_id ke bajay unke validation reason se reject karo.
8. Invalid dates, unsupported currency, missing/non-numeric amounts, invalid quantities, unknown/inactive customers, ya duplicate rows reject karo.
9. Row ke liye multiple reject reasons hon, toh is priority order mein pehla applicable reason record karo:
   missing_amount, unsupported_currency, invalid_quantity, inactive_customer, unknown_customer, invalid_date, duplicate_order_id.
10. Refund/returned rows mein amount_usd exactly ek baar negative hona chahiye: positive returned amount ko negative banao aur already-negative returned amount ko negative hi rakho.

cleaned_sales.csv requirements:
- Exact header:
  order_id,order_date,customer_id,customer_name,sku,quantity,amount_usd,status
- Rows ko pehle order_date, phir order_id se sort karo.
- Extra columns mat jodo.

reject_ledger.csv requirements:
- Exact header:
  order_id,reason,source_row,notes
- Har rejected input row ke liye ek row include karo. source_row, header ko chhodkar messy_sales.csv ka 1-based data-row number hai.
- Rule 9 mein listed reason codes mein se ek use karo.

reject_summary.json requirements:
- Valid JSON object ho, rule 9 ke har reason code ki key ho, zero-count reasons bhi.
- Har reason entry mein count, source_rows, aur order_ids ho.
- source_rows ascending input order mein numeric arrays hon.

cleaning_report.md requirements:
- Valid row count, rejected row count, duplicate count aur total amount_usd summarize karo.
- Har reject reason category explain karo.
- Use ki gayi locale ya FX assumptions mention karo.

Network access ya external APIs use mat karo.
'''),
('050-multitable-join-analysis','prompt.txt'):(r'''Local tables se customer-level revenue metrics aur reconciliation note banayein.

Workspace root mein copy kiye gaye inputs:
- $WORKSPACE/in/customers.csv
- $WORKSPACE/in/orders.csv
- $WORKSPACE/in/payments.csv
- $WORKSPACE/in/refunds.csv
- $WORKSPACE/in/fx_rates.csv
- $WORKSPACE/in/chargebacks.csv

Ye files banayein:
- $WORKSPACE/out/customer_metrics.csv
- $WORKSPACE/out/region_summary.json
- $WORKSPACE/out/reconciliation_audit.json
- $WORKSPACE/out/reconciliation_notes.md

customer_metrics.csv ke columns, isi exact order mein:
canonical_customer_id,name,region,order_count,gross_revenue_usd,refund_amount_usd,chargeback_amount_usd,net_revenue_usd,segment
Rows ko canonical_customer_id ascending order mein sort karein.

Business rules:
1. Input files modify na karein.
2. customers.csv ke canonical_customer_id se aliases roll up karein. Har canonical customer ki ek row output karein, un canonical customers samet jinka valid revenue nahi hai.
3. `order_count` un distinct `order_id` values ko count karta hai jinka `order_status` paid hai aur jinke liye kam-se-kam ek captured payment hai. Ek order ki multiple captured payment rows phir bhi ek hi order gini jaayengi.
4. Gross revenue captured payments se aata hai, order_amount se nahi. Duplicate payment rows sirf tab ignore karein jab `(order_id, amount, currency, status)` ke saare values match karte hon; ek hi order ke different amounts wale captured payments additive hain.
5. Payments, refunds, aur chargebacks ko fx_rates.csv se USD mein convert karein.
6. Aise captured payments jo missing order_id ko reference karte hain, orphan payments hain. Unhe revenue mein count na karein, lekin reconciliation_notes.md mein list karein.
7. Refunds sirf tab count hon jab woh aise order ko reference karte hon jo paid ho aur captured payment revenue ke through included ho. Orphan refunds, cancelled orders ke refunds, aur captured revenue ke bina orders ke refunds anomalies hain, revenue deductions nahi.
8. Chargebacks sirf tab count hon jab woh included paid/captured order ko reference karte hon aur status won_by_customer ho. won_by_merchant chargebacks reconciliation notes mein hon, par revenue deduction nahi.
9. Net revenue = gross revenue - refunds - chargebacks.
10. Money fields ko exactly two decimals ke saath format karein.
11. Canonical customers ko is tarah segment karein:
   - jab net_revenue_usd >= 500 ho, platinum
   - jab net_revenue_usd >= 250 aur < 500 ho, gold
   - jab net_revenue_usd > 0 aur < 250 ho, silver
   - jab net_revenue_usd == 0 ho, dormant

region_summary.json requirements:
- Region ke hisaab se keyed valid JSON object.
- Har region entry mein canonical_customer_count, gross_revenue_usd, net_revenue_usd hon.

reconciliation_notes.md requirements:
- Revenue ka basis samjhayen.
- Duplicate payments, orphan payments, orphan refunds, cancelled/no-captured orders ke against refunds, aur chargebacks list karein.
- Canonical customer merge ka zikr karein.

reconciliation_audit.json requirements:
- `duplicate_payment_ids`, `orphan_payment_ids`, `refund_anomaly_ids`, `included_chargeback_ids`, `excluded_chargeback_ids`, `alias_customer_ids` keys wala valid JSON.
- Har value ascending order mein sorted IDs ka array ho.
- duplicate_payment_ids, tuple rule ki wajah se ignore ki gayi duplicate captured payment rows hain.
- refund_anomaly_ids mein orphan refunds, cancelled orders ke refunds, aur captured revenue ke bina orders ke refunds shamil hon.
- excluded_chargeback_ids mein woh chargebacks shamil hon jo deduct nahi hue kyunki order included nahi hai ya chargeback status won_by_customer nahi hai.

Network access use na karein. customer_metrics.csv mein extra columns na jodein.
''',r'''Local tables se customer-level revenue metrics aur reconciliation note banao.

Workspace root mein copied inputs:
- $WORKSPACE/in/customers.csv
- $WORKSPACE/in/orders.csv
- $WORKSPACE/in/payments.csv
- $WORKSPACE/in/refunds.csv
- $WORKSPACE/in/fx_rates.csv
- $WORKSPACE/in/chargebacks.csv

Ye files banao:
- $WORKSPACE/out/customer_metrics.csv
- $WORKSPACE/out/region_summary.json
- $WORKSPACE/out/reconciliation_audit.json
- $WORKSPACE/out/reconciliation_notes.md

customer_metrics.csv columns, isi exact order mein:
canonical_customer_id,name,region,order_count,gross_revenue_usd,refund_amount_usd,chargeback_amount_usd,net_revenue_usd,segment
Rows ko canonical_customer_id ascending order mein sort karo.

Business rules:
1. Input files modify mat karo.
2. customers.csv ke canonical_customer_id se aliases roll up karo. Har canonical customer ke liye ek row output karo, un canonical customers samet jinke paas valid revenue nahi hai.
3. `order_count`, un distinct `order_id` values ko count karta hai jinka `order_status` paid hai aur jinke liye at least ek captured payment hai. Same order ki multiple captured payment rows phir bhi ek hi order count hongi.
4. Gross revenue captured payments se aata hai, order_amount se nahi. Duplicate payment rows sirf tab ignore karo jab `(order_id, amount, currency, status)` ki saari values match hon; same order ke different amounts wale captured payments add honge.
5. Payments, refunds aur chargebacks ko fx_rates.csv se USD mein convert karo.
6. Missing order_id ko refer karne wale captured payments orphan payments hain. Unhe revenue mein count mat karo, lekin reconciliation_notes.md mein list karo.
7. Refunds sirf tab count karo jab woh us order ko refer karte hon jo paid hai aur captured payment revenue ke zariye included hai. Orphan refunds, cancelled orders ke refunds aur captured revenue ke bina orders ke refunds anomalies hain, revenue deductions nahi.
8. Chargebacks sirf tab count karo jab woh included paid/captured order ko refer karte hon aur status won_by_customer ho. won_by_merchant chargebacks reconciliation notes mein likho, lekin revenue se deduct mat karo.
9. Net revenue = gross revenue - refunds - chargebacks.
10. Money fields ko exactly two decimals mein format karo.
11. Canonical customers ko is tarah segment karo:
   - net_revenue_usd >= 500 ho toh platinum
   - net_revenue_usd >= 250 aur < 500 ho toh gold
   - net_revenue_usd > 0 aur < 250 ho toh silver
   - net_revenue_usd == 0 ho toh dormant

region_summary.json requirements:
- Region-keyed valid JSON object.
- Har region entry mein canonical_customer_count, gross_revenue_usd, net_revenue_usd hon.

reconciliation_notes.md requirements:
- Revenue ka basis explain karo.
- Duplicate payments, orphan payments, orphan refunds, cancelled/no-captured orders ke against refunds aur chargebacks list karo.
- Canonical customer merge mention karo.

reconciliation_audit.json requirements:
- `duplicate_payment_ids`, `orphan_payment_ids`, `refund_anomaly_ids`, `included_chargeback_ids`, `excluded_chargeback_ids`, `alias_customer_ids` keys wala valid JSON.
- Har value ascending order mein sorted IDs ka array ho.
- duplicate_payment_ids woh duplicate captured payment rows hain jinhe tuple rule ki wajah se ignore kiya gaya.
- refund_anomaly_ids mein orphan refunds, cancelled orders ke refunds, aur captured revenue ke bina orders ke refunds include hon.
- excluded_chargeback_ids mein woh chargebacks include hon jo deduct nahi kiye gaye kyunki order included nahi hai ya chargeback status won_by_customer nahi hai.

Network access mat use karo. customer_metrics.csv mein extra columns mat jodo.
'''),
}
