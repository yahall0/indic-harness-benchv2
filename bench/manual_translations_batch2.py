"""Hand-written Hindi and Hinglish variants for the next selected tasks."""
TRANSLATIONS = {
('033-offline-knowledge-qa','prompt.txt'):(r'''Task: Evidence Attribution ke saath Offline Document QA

Sirf `$WORKSPACE/in/docs/*.md` aur `$WORKSPACE/in/questions.json` ke offline materials use kar sakte hain. Online na jaayein aur materials mein na di gayi jaankari bharne ke liye common knowledge use na karein.

`questions.json` se saare questions padhein aur answers `$WORKSPACE/out/answers.json` mein likhein.

Output format:
- Top level JSON array hona chahiye; har element ek question se correspond kare.
- Har element mein ye fields hon: `question_id`, `answer`, `source_file`, `quote_or_signal`.
- Materials mein jawab dene ke liye paryapt evidence na ho, toh `answer` bilkul `insufficient_evidence` ho, `source_file` `null` ya empty string ho, aur `quote_or_signal` mein batayein ki kis type ka evidence missing hai.
- Jawab diye ja sakne wale questions ke liye `source_file`, `docs/` ke andar ka relative path ho, jaise `docs/operations.md`.
- `quote_or_signal` mein chhota quote ya locate karne ka signal dein jo jawab ko support kare; sirf “see document” na likhein.

Prohibitions:
- Fixtures ki kisi file ko modify na karein.
- Extra Markdown wrapping output na karein.
- Jinka jawab nahi diya ja sakta, unke answers fabricate na karein.
''',r'''Task: Evidence Attribution ke saath Offline Document QA

Sirf `$WORKSPACE/in/docs/*.md` aur `$WORKSPACE/in/questions.json` wale offline materials use kar sakte ho. Online mat jao, aur materials mein missing info bharne ke liye common knowledge use mat karo.

`questions.json` ke saare questions padho aur answers `$WORKSPACE/out/answers.json` mein likho.

Output format:
- Top level JSON array hona chahiye; har element ek question se match kare.
- Har element mein ye fields hon: `question_id`, `answer`, `source_file`, `quote_or_signal`.
- Materials mein answer dene ke liye sufficient evidence na ho toh `answer` exactly `insufficient_evidence` ho, `source_file` `null` ya empty string ho, aur `quote_or_signal` mein batao ki kis type ka evidence missing hai.
- Answerable questions ke liye `source_file`, `docs/` ke andar relative path ho, jaise `docs/operations.md`.
- `quote_or_signal` mein short quote ya locate karne wala signal do jo answer support kare; sirf “see document” mat likho.

Prohibitions:
- Fixtures ki koi file modify mat karo.
- Output ke around extra Markdown mat likho.
- Unanswerable questions ke answers fabricate mat karo.
'''),
('034-evidence-matrix-claims','prompt.txt'):(r'''Task: Claims ke liye Evidence Matrix banayein

Inputs:
- `$WORKSPACE/in/claims.csv`
- `$WORKSPACE/in/sources/*.txt`

claims.csv mein har claim ko ek-ek karke check karein aur `$WORKSPACE/out/evidence_matrix.csv` output karein.

CSV mein ye header hona chahiye:
`claim_id,claim,classification,source_file,evidence_phrase`

Constraints:
- `classification` bilkul inmein se ek ho: `support`, `contradict`, ya `unclear`.
- `source_file` mein relative path `sources/filename.txt` use karein. Agar classification `unclear` ho, toh conclusion par pahunchne ke liye insufficient sabse relevant source de sakte hain.
- `evidence_phrase` chhota evidence signal ho jo bataye ki claim support hota hai, contradict hota hai, ya decide nahi kiya ja sakta.
- claims.csv ke har claim_id ko cover karein; extra claim_ids na jodein.
- Fixtures modify na karein aur online na jaayein.
''',r'''Task: Claims ke liye Evidence Matrix banao

Inputs:
- `$WORKSPACE/in/claims.csv`
- `$WORKSPACE/in/sources/*.txt`

claims.csv ke har claim ko one by one check karo aur `$WORKSPACE/out/evidence_matrix.csv` output karo.

CSV mein ye header hona chahiye:
`claim_id,claim,classification,source_file,evidence_phrase`

Constraints:
- `classification` exactly inmein se ek ho: `support`, `contradict`, ya `unclear`.
- `source_file` mein relative path `sources/filename.txt` use karo. `unclear` classification ho toh conclusion ke liye insufficient sabse relevant source de sakte ho.
- `evidence_phrase` ek short evidence signal ho jo samjhaye ki claim supported hai, contradicted hai, ya determine nahi kiya ja sakta.
- claims.csv ke har claim_id ko cover karo; extra claim_ids mat jodo.
- Fixtures modify mat karo; online mat jao.
'''),
('035-conflicting-source-resolution','prompt.txt'):(r'''Task: Conflicting Sources ko resolve karein

`$WORKSPACE/in/briefs/` ki files mein Project Kestrel ke baare mein kai briefs hain. Kuch facts conflict karte hain. Launch readiness ke facts resolve karne ke liye sirf offline materials use karein.

Samanya roop se sources ki priority ka ye order lagu karein. Agar higher-priority source sirf local ya scoped fact cover karta hai, toh use sirf usi coverage scope mein lagu karein:

1. signed_regulator_notice
2. audited_finance_extract
3. operations_log
4. signed vendor/contract addenda
5. press_release
6. social_digest

Ye outputs banayein:

1. `$WORKSPACE/out/resolved_facts.json`
   - Required fields: `project_status`, `approved_budget_musd`, `launch_date`, `customer_count`, `primary_vendor`, `service_scope`, `scope_exception`, aur `evidence`.
   - `evidence` ek array ho. Har item mein `fact_key`, `source_file`, `quote_or_signal`, aur `priority_reason` hon.
   - `source_file`, `$WORKSPACE/in/` se strict relative path ho, jaise `briefs/signed_regulator_notice.md`; sirf filename na dein.
   - Jab lower-priority source, higher-priority source se conflict kare, toh higher-priority source use karein.
   - `service_scope` ke liye contract-planned scope aur regulator-authorized launch-day scope mein farq batayein. Agar higher-priority source sirf launch-day authorization cover karta ho, toh final fact mein us scoped coverage ko reflect karein.

2. `$WORKSPACE/out/uncertainties.md`
   - Aise facts ko clearly list karein jinki pushti nahi ho sakti.
   - Kam-se-kam three entries dein aur samjhayen ki available materials kyon insufficient hain.

3. `$WORKSPACE/out/conflict_matrix.csv`
   - Header bilkul `fact_key,winning_source,losing_sources,resolution_rationale,coverage_scope` ho.
   - Kam-se-kam five conflict ya scoped-coverage areas cover karein: launch date, budget, vendor, customer count, aur service scope.
   - `coverage_scope` samjhaye ki winning source global fact, budget fact, launch-day authorization, contract-planned scope, ya kisi aur specific scope ko cover karta hai.

4. `$WORKSPACE/out/source_reliability.json`
   - JSON array ho, har used ya rejected source ke liye ek item.
   - Har item mein `source_file`, `priority_rank`, `coverage_scope`, `used_for`, `rejected_claims`, aur `reliability_note` hon.
   - Scoped authority ko clearly samjhayen, khaaskar jahan regulator authorization aur contract-planned service alag hon.

5. `$WORKSPACE/out/decision_log.md`
   - Conflicts kaise resolve hue, iska concise chronological explanation.
   - Launch-day scope aur contract-planned scope ke antar par kam-se-kam ek paragraph aur low-priority rumors reject karne ke kaaran par ek paragraph include karein.

Forbidden: internet use na karein; fixtures modify na karein; low-priority rumors ko final facts ke roop mein na apnayein.
''',r'''Task: Conflicting Sources resolve karo

`$WORKSPACE/in/briefs/` files mein Project Kestrel ke baare mein multiple briefs hain. Kuch facts conflict karte hain. Launch-readiness facts resolve karne ke liye sirf offline materials use karo.

Generally, sources ka ye priority order apply karo. Higher-priority source sirf local ya scoped fact cover karta ho toh use sirf us coverage scope tak apply karo:

1. signed_regulator_notice
2. audited_finance_extract
3. operations_log
4. signed vendor/contract addenda
5. press_release
6. social_digest

Ye outputs banao:

1. `$WORKSPACE/out/resolved_facts.json`
   - Required fields: `project_status`, `approved_budget_musd`, `launch_date`, `customer_count`, `primary_vendor`, `service_scope`, `scope_exception`, aur `evidence`.
   - `evidence` array ho. Har item mein `fact_key`, `source_file`, `quote_or_signal`, aur `priority_reason` ho.
   - `source_file`, `$WORKSPACE/in/` se strict relative path ho, jaise `briefs/signed_regulator_notice.md`; sirf filename mat do.
   - Lower-priority source higher-priority source se conflict kare toh higher-priority source use karo.
   - `service_scope` mein contract-planned scope aur regulator-authorized launch-day scope alag rakho. Higher-priority source sirf launch-day authorization cover kare toh final fact mein us scoped coverage ko reflect karo.

2. `$WORKSPACE/out/uncertainties.md`
   - Confirm nahi ho sakne wale facts clearly list karo.
   - Kam-se-kam three entries include karo aur samjhao ki available materials insufficient kyun hain.

3. `$WORKSPACE/out/conflict_matrix.csv`
   - Header exactly `fact_key,winning_source,losing_sources,resolution_rationale,coverage_scope` ho.
   - Kam-se-kam five conflict ya scoped-coverage areas cover karo: launch date, budget, vendor, customer count, aur service scope.
   - `coverage_scope` bataye ki winning source global fact, budget fact, launch-day authorization, contract-planned scope, ya kisi aur specific scope ko cover karta hai.

4. `$WORKSPACE/out/source_reliability.json`
   - JSON array ho, har used ya rejected source ka ek item.
   - Har item mein `source_file`, `priority_rank`, `coverage_scope`, `used_for`, `rejected_claims`, aur `reliability_note` ho.
   - Scoped authority clearly samjhao, khaaskar jahan regulator authorization aur contract-planned service alag ho.

5. `$WORKSPACE/out/decision_log.md`
   - Conflicts resolve karne ka concise chronological explanation do.
   - Launch-day scope aur contract-planned scope ke difference par kam-se-kam ek paragraph aur low-priority rumors reject kyun hue, is par ek paragraph include karo.

Forbidden: internet use mat karo; fixtures modify mat karo; low-priority rumors ko final facts mat maano.
'''),
('036-citation-consistency-audit','prompt.txt'):(r'''Task: Citation Consistency Audit

Inputs:
- `$WORKSPACE/in/paper_draft.md`
- `$WORKSPACE/in/bib.json`

In-text citations aur bibliography ki consistency audit karein, aur ye outputs banayein:

1. `$WORKSPACE/out/citation_errors.csv`
   - Header bilkul `error_type,citation_key,details,expected_fix,evidence_span` ho.
   - Kam-se-kam ye cases cover karein: draft mein maujood lekin `bib.json` se missing citations, bibliography entries jo draft mein cited nahi hain, author mismatches, aur year mismatches.
   - Ye bhi cover karein: same-author same-year suffix needs jaise 2024a/2024b, duplicate ya conflicting bibliography keys, aur title/DOI inconsistencies.
   - `error_type` mein ye enum use karein: `missing_bib`, `orphan_bib`, `author_mismatch`, `year_mismatch`, `suffix_needed`, `duplicate_key`, `doi_title_mismatch`.
   - Har error point apni row mein ho; multiple `citation_key` values ko ek row mein merge na karein.
   - `evidence_span` mein draft ya bibliography ka chhota span ho jo error judgment ko support kare; sirf filename na dein.

2. `$WORKSPACE/out/corrected_bib.json`
   - Valid JSON hona chahiye.
   - Draft se determine ho sakne wali author/year errors sahi karein.
   - Orphan bibliography entries hataayein aur `bib.json` mein missing draft citations add karein; jo fields determine na ho sakein unmein `"UNKNOWN"` use kar sakte hain.
   - Indirect Rao mention ke liye alag bibliography entry na banayein, jab tak draft ki reference list use explicitly list na karti ho.

3. `$WORKSPACE/out/audit_notes.md`
   - Har error type ka basis samjhayen.
   - Clearly batayein kaun se fields `UNKNOWN` use karte hain aur state karein ki koi internet lookup nahi hua.
   - 2024a/2024b suffixes ka ordering basis samjhayen aur Rao ko standalone bibliography entry kyon nahi banana chahiye, yeh bhi batayein.

4. `$WORKSPACE/out/citation_graph.json`
   - `in_text_citations`, `bibliography_entries`, aur `key_renames` keys wala JSON object.
   - `in_text_citations` har draft citation signal ko corrected bibliography key ya missing/orphan/error status se map kare.
   - `bibliography_entries` bataye ki har original bibliography entry kept, renamed, removed, ya split hui.
   - `key_renames` mein Lin, Ortega, aur Chen key changes explicitly include hon.

Forbidden: internet use na karein; fixtures modify na karein; `citation_errors.csv` ko Markdown table ke roop mein na likhein.
''',r'''Task: Citation Consistency Audit

Inputs:
- `$WORKSPACE/in/paper_draft.md`
- `$WORKSPACE/in/bib.json`

In-text citations aur bibliography ki consistency audit karo, aur ye outputs banao:

1. `$WORKSPACE/out/citation_errors.csv`
   - Header exactly `error_type,citation_key,details,expected_fix,evidence_span` ho.
   - Kam-se-kam ye cover karo: draft mein citations hain par `bib.json` mein missing hain, bibliography entries draft mein cited nahi hain, author mismatch, aur year mismatch.
   - Ye bhi cover karo: same-author same-year suffix needs jaise 2024a/2024b, duplicate ya conflicting bibliography keys, aur title/DOI inconsistencies.
   - `error_type` ke liye ye enum use karo: `missing_bib`, `orphan_bib`, `author_mismatch`, `year_mismatch`, `suffix_needed`, `duplicate_key`, `doi_title_mismatch`.
   - Har error point apni row mein rakho; multiple `citation_key` values ek row mein merge mat karo.
   - `evidence_span` mein draft ya bibliography ka short span ho jo error judgment support kare; sirf filename mat do.

2. `$WORKSPACE/out/corrected_bib.json`
   - Valid JSON hona chahiye.
   - Draft se determine ho sakne wali author/year errors correct karo.
   - Orphan bibliography entries remove karo aur `bib.json` mein missing draft citations add karo; determine na ho sakne wale fields ke liye `"UNKNOWN"` use kar sakte ho.
   - Indirect Rao mention ke liye separate bibliography entry mat banao, jab tak draft ki reference list explicitly usse list na kare.

3. `$WORKSPACE/out/audit_notes.md`
   - Har error type ka basis explain karo.
   - Clearly batao kaun se fields `UNKNOWN` use karte hain aur state karo ki internet lookup nahi hua.
   - 2024a/2024b suffixes ka ordering basis samjhao aur batao ki Rao ko standalone bibliography entry kyun nahi banna chahiye.

4. `$WORKSPACE/out/citation_graph.json`
   - `in_text_citations`, `bibliography_entries`, aur `key_renames` keys wala JSON object.
   - `in_text_citations` mein har draft citation signal ko corrected bibliography key ya missing/orphan/error status se map karo.
   - `bibliography_entries` mein batao ki har original bibliography entry kept, renamed, removed, ya split hui.
   - `key_renames` mein Lin, Ortega, aur Chen key changes explicitly include karo.

Forbidden: internet use mat karo; fixtures modify mat karo; `citation_errors.csv` ko Markdown table ki tarah mat likho.
'''),
}
