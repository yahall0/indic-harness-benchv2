"""Hand-produced language variants. Do not automate semantic translation."""
TRANSLATIONS = {
('001-file','prompt.txt'):(r'''कार्यशील डायरेक्टरी `$WORKSPACE` है।

`in/input.txt` पढ़ें, फ़ाइल में लाइनों की संख्या गिनें और परिणाम `out/linecount.txt` में लिखें।

ज़रूरी बातें:
- केवल एक पूर्णांक (लाइनों की संख्या) लिखें।
- `in/input.txt` में बदलाव न करें।
''',r'''Working directory `$WORKSPACE` hai.

`in/input.txt` padho, file mein lines count karo aur result `out/linecount.txt` mein likho.

Requirements:
- Sirf ek integer (line count) likhna.
- `in/input.txt` ko modify mat karna.
'''),
('002-exec','prompt.txt'):(r'''**`$WORKSPACE`** के अंदर नीचे दिए गए चरण पूरे करने के लिए **terminal** का इस्तेमाल करें। Harness ने पहले ही खाली **`out/`** directory बना दी है; अगर repo root में `AGENTS.md`, `.git` वगैरह दिखें, तो वे runtime से आए हैं—**उन्हें अनदेखा करें** और outputs सिर्फ **`out/`** के अंदर लिखें।

हर चरण का artifact **single-line text** होना चाहिए (पहली line गिनी जाएगी; आगे या पीछे अतिरिक्त whitespace न हो), जैसा सामान्य CLI इस्तेमाल में बनेगा:

1. **Arithmetic expansion**: **`42`** को **`out/step1.txt`** में लिखें (इसे shell से ही बनाना है, जैसे `echo $((6*7))` या equivalent redirect)।

2. **`basename`**: पहले किसी deep path के अंदर file बनाएँ, जैसे
   `mkdir -p out/a/b` और `touch out/a/b/c.txt`; फिर उस path का **filename** (directory के बिना) **`out/step2.txt`** में लिखें (जैसे `basename` या equivalent; expected single line **`c.txt`**)।

3. **Pipeline and `tr`**: **`hello`** को **`out/step3.txt`** में लिखें (जैसे `printf 'HELLO\n' | tr '[:upper:]' '[:lower:]'` को redirect करना, या equivalent pipeline)।

दिए गए prompt से आगे किसी external resource या network पर निर्भर न रहें।
''',r'''**`$WORKSPACE`** ke andar neeche diye steps complete karne ke liye **terminal** use karo. Harness ne empty **`out/`** directory pehle se banayi hai; agar repo root mein `AGENTS.md`, `.git`, etc. dikhen, woh runtime se aaye hain—**unhe ignore karo** aur outputs sirf **`out/`** ke andar likho.

Har step ka artifact **single-line text** hona chahiye (first line count hoti hai; extra leading/trailing whitespace na ho), jaise typical CLI use mein hota hai:

1. **Arithmetic expansion**: **`42`** ko **`out/step1.txt`** mein likho (shell se hi produce karo, jaise `echo $((6*7))` ya equivalent redirect).

2. **`basename`**: pehle kisi deep path ke andar file banao, jaise
   `mkdir -p out/a/b` aur `touch out/a/b/c.txt`; phir us path ka **filename** (directories ke bina) **`out/step2.txt`** mein likho (jaise `basename` ya equivalent; expected single line **`c.txt`**)।

3. **Pipeline and `tr`**: **`hello`** ko **`out/step3.txt`** mein likho (jaise `printf 'HELLO\n' | tr '[:upper:]' '[:lower:]'` ko redirect karke ya equivalent pipeline).

Prompt mein diye gaye scope se aage external resources ya network use mat karo.
'''),
('004-meeting-summary','prompt.txt'):(r'''**`$WORKSPACE/in/meeting_transcript.txt`** (product meeting का पूरा transcript) पढ़ें और **English meeting summary** को **`$WORKSPACE/out/meeting_summary.txt`** में लिखें (UTF-8 text; ज़रूरत हो तो पहले `mkdir -p out` से directory बनाएँ)।

**Content and format:**
1. English में **one to three paragraphs** लिखें, जिनमें **main topics**, **एक जैसी समझ वाले conclusions या decisions**, **बड़े risks या खुले मुद्दे**, और **साफ़ follow-ups** शामिल हों (हर sentence का recap ज़रूरी नहीं, लेकिन reader पूरी transcript पढ़े बिना चर्चा समझ सके)। **सिर्फ वही शामिल करें जिसका आधार transcript में हो**—अनुमान न लगाएँ और कुछ गढ़ें नहीं।
2. **Length**: सामान्य **short workplace summary** रखें—सिर्फ़ कुछ नारे जैसे bullets से साफ़ तौर पर अधिक, और transcript की copy से साफ़ तौर पर छोटा; ज़्यादातर readers इसे **about one to two minutes** में पढ़ लें। बहुत छोटे bullet dumps या बहुत लंबे essays से बचें।
3. **Information density**: summary को coherent रखते हुए transcript के कई **बार-बार आने वाले या प्रमुख शब्द** स्वाभाविक रूप से शामिल करें (org/product-line names, phase या release wording, resource या constraint language, named technical या process objects, आदि); सिर्फ़ “complete” दिखने के लिए असंबंधित terms न भरें।

**Output path:** सिर्फ़ `out/meeting_summary.txt`।
''',r'''**`$WORKSPACE/in/meeting_transcript.txt`** (product meeting ka full transcript) padho aur **English meeting summary** ko **`$WORKSPACE/out/meeting_summary.txt`** mein likho (UTF-8 text; zaroorat ho toh pehle `mkdir -p out` se directory banao).

**Content and format:**
1. English mein **one to three paragraphs** likho; inmein **main topics**, **agreed conclusions ya decisions**, **major risks ya open issues**, aur **clear follow-ups** cover hon (sentence-by-sentence recap zaroori nahi, par reader full transcript padhe bina discussion samajh sake). **Sirf transcript-supported baatein shamil karo**—speculate ya invent mat karo.
2. **Length**: ek typical **short workplace summary** target karo—kuch slogan-like bullets se clearly zyada, aur transcript copy karne se clearly chhota; most readers ise **about one to two minutes** mein padh saken. Ultra-short bullet dumps aur bahut lambe essays se bacho.
3. **Information density**: summary coherent rahe aur transcript ke kuch **recurring ya anchoring terms** naturally include kare (org/product-line names, phase ya release wording, resource ya constraint language, named technical ya process objects, etc.); “complete” dikhne ke liye unrelated terms mat bharo.

**Output path:** sirf `out/meeting_summary.txt`.
'''),
('005-email-triage','prompt.txt'):(r'''आप mock inbox environment में हैं। **`$WORKSPACE/in/emails.json`** की email list process करें। यह JSON object है, जिसके **`emails`** field में array है; हर email में `id`, `from`, `subject`, और `body` हैं। Working directory: `$WORKSPACE`।

ये काम पूरे करें:

1) `$WORKSPACE/in/emails.json` की हर email **पढ़ें** और तीन labels में से एक दें:
   - `spam`: junk/scams/साफ़ तौर पर अनदेखा करने योग्य; इसे deletion list में जाना चाहिए।
   - `needs_reply`: ऐसी threads जिनका इंसान जैसा जवाब देना ज़रूरी है (जैसे कोई colleague पूछे कि आप free हैं या नहीं)।
   - `ok`: जवाब की ज़रूरत नहीं (system notifications, सिर्फ़ FYI आदि)।

2) Classifications को **`$WORKSPACE/out/triage.json`** में लिखें (JSON object; keys email `id` strings हों; values इस तरह):
   `{"label":"spam|needs_reply|ok","reason_short":"one-line reason"}`

3) हर `spam` email का `id`, हर line में एक, **`$WORKSPACE/out/delete_ids.txt`** में लिखें (सिर्फ़ IDs; कोई और text नहीं)। गैर-spam IDs न लिखें।

4) हर `needs_reply` email के लिए **reply body** (plain text) **`$WORKSPACE/out/replies/<id>.txt`** में लिखें (जैसे `out/replies/002.txt`)। Replies में सवाल का **सीधा जवाब** दें (जैसे “Are you free today?” पूछें, तो बताएं कि आप free हैं या कोई समय सुझाएँ)। विषय से हटकर जवाब न दें।

5) सबसे पहले `mkdir -p $WORKSPACE/out $WORKSPACE/out/replies` चलाएँ।
''',r'''Tum mock inbox environment mein ho. **`$WORKSPACE/in/emails.json`** ki email list process karo. File ek JSON object hai; uske **`emails`** field mein array hai, aur har email mein `id`, `from`, `subject`, aur `body` hain. Working directory: `$WORKSPACE`.

Ye steps complete karo:

1) `$WORKSPACE/in/emails.json` ki har email **read** karke teen labels mein se ek assign karo:
   - `spam`: junk/scams/clearly ignore karne layak; deletion list mein jaana chahiye.
   - `needs_reply`: aisi threads jinhe human-like reply chahiye (jaise colleague pooche ki tum free ho ya nahi).
   - `ok`: reply ki zaroorat nahi (system notifications, sirf FYI, etc.).

2) Classifications ko **`$WORKSPACE/out/triage.json`** mein likho (JSON object; keys email `id` strings hon; values aise):
   `{"label":"spam|needs_reply|ok","reason_short":"one-line reason"}`

3) Har `spam` email ka `id`, har line par ek, **`$WORKSPACE/out/delete_ids.txt`** mein likho (sirf IDs; aur koi text nahi). Non-spam IDs mat likho.

4) Har `needs_reply` email ke liye **reply body** (plain text) **`$WORKSPACE/out/replies/<id>.txt`** mein likho (jaise `out/replies/002.txt`). Reply mein question ka **direct answer** do (jaise “Are you free today?” poocha ho, toh batao free ho ya koi time propose karo). Off-topic reply mat do.

5) Sabse pehle `mkdir -p $WORKSPACE/out $WORKSPACE/out/replies` run karo.
'''),
('007-session-memory','prompt_round1.txt'):(r'''[Round 1 / 2 — same OpenClaw session] Working directory: `$WORKSPACE`।

तुम्हें यह passphrase **conversation memory** में याद रखनी है (अगले round में यह दोहराई नहीं जाएगी):

**Passphrase: `$MEM_SECRET`**

नियम:
1. passphrase को **किसी भी हालत में** **`$WORKSPACE/out/`** की किसी file में plain text में न लिखें (इस task में सिर्फ़ `phase1_done.txt` की अनुमति है, और उसकी सामग्री ठीक एक line होनी चाहिए: `ready`, passphrase के बिना); इसे सिर्फ़ मौजूदा session context में रखें। Grading सिर्फ़ `out/` directory को inspect करती है।
2. `$WORKSPACE/out/` के अंदर **`phase1_done.txt`** बनाएँ; उसमें **ठीक एक line**, केवल `ready` शब्द हो (lowercase, बिना quotes, बिना अतिरिक्त spaces), जिससे passphrase स्वीकार करना दर्ज हो।

पहले यह चलाएँ: `mkdir -p $WORKSPACE/out`.
''',r'''[Round 1 / 2 — same OpenClaw session] Working directory: `$WORKSPACE`.

Yeh passphrase **conversation memory** mein yaad rakhni hai (next round mein repeat nahi hogi):

**Passphrase: `$MEM_SECRET`**

Rules:
1. Passphrase ko **kabhi bhi** **`$WORKSPACE/out/`** ki kisi file mein plain text mein mat likhna (is task mein sirf `phase1_done.txt` allowed hai, aur uska content exactly ek line hona chahiye: `ready`, bina passphrase); ise sirf current session context mein rakho. Grading sirf `out/` directory inspect karti hai.
2. `$WORKSPACE/out/` ke andar **`phase1_done.txt`** banao; usmein **exactly ek line**, sirf `ready` word ho (lowercase, quotes nahi, extra spaces nahi), jisse passphrase accept karna record ho.

Pehle run karo: `mkdir -p $WORKSPACE/out`.
'''),
('007-session-memory','prompt_round2.txt'):(r'''[Round 2 / 2 — same session-id as the previous round; do not start a new session] Working directory: `$WORKSPACE`।

पिछले round में **user message** ने तुम्हें English passphrase दी थी (**इस message में वह नहीं है**)। उसे सिर्फ़ **multi-turn conversation memory** से याद करो।

1. passphrase को **ज्यों का त्यों** (एक-एक character मिलाकर) **`$WORKSPACE/out/recalled.txt`** में लिखें; सिर्फ़ एक line, कोई अतिरिक्त whitespace नहीं।
2. Workspace files पढ़कर passphrase “recover” करने की **कोशिश न करें** (harness जाँचता है कि round 1 के बाद passphrase कभी disk पर लिखी गई थी या नहीं); session memory पर भरोसा करें।

अगर `out` मौजूद न हो, तो पहले `mkdir -p $WORKSPACE/out` चलाएँ।
''',r'''[Round 2 / 2 — same session-id as the previous round; do not start a new session] Working directory: `$WORKSPACE`.

Pichhle round mein **user message** ne English passphrase di thi (**is message mein woh nahi hai**). Use sirf **multi-turn conversation memory** se yaad karo.

1. Passphrase ko **verbatim** (character-for-character same) **`$WORKSPACE/out/recalled.txt`** mein likho; sirf ek line, extra whitespace nahi.
2. Workspace files padhkar passphrase “recover” karne ki **koshish mat karo** (harness check karta hai ki round 1 ke baad passphrase kabhi disk par likhi gayi thi ya nahi); session memory par bharosa karo.

Agar `out` directory maujood na ho, toh pehle `mkdir -p $WORKSPACE/out` run karo.
'''),
('012-doc-synthesis','prompt.txt'):(r'''Task: कई दस्तावेज़ों का synthesis और विरोधाभासों का पता लगाना

एक ही incident के बारे में पाँच दस्तावेज़ `$WORKSPACE/in/` के अंदर हैं:
- doc1_news_site_a.md (NewsSite A का article)
- doc2_news_site_b.md (NewsSite B का article)
- doc3_social_media.md (social posts / अफ़वाहें)
- doc4_official_statement.md (official statement)
- doc5_expert_analysis.md (expert analysis)

इनमें मतभेद हैं और इनमें गलतियाँ या bias हो सकता है।

नीचे के सभी काम पूरे करें; सब कुछ `$WORKSPACE/out/` के अंदर लिखें:

1. हर दस्तावेज़ का भरोसे का score (**trustworthiness.json**)
   हर document को 0–10 का score और एक छोटा कारण दें (जैसे source authority, आपसी consistency, evidence chain)।
   Format:
   {
     "doc1_news_site_a.md": {"score": 6, "reason": "specific numbers but sensational tone"},
     ...
   }

2. विरोधाभास (**contradictions.json**)
   मुख्य विरोधाभासों की सूची दें (कम-से-कम 3); संबंधित documents और उदाहरण वाली representative quotes/snippets बताएँ।
   Format:
   {
     "contradictions": [
       {
         "claim": "example axis of disagreement",
         "documents": ["doc1", "doc2", "doc4"],
         "quotes": ["...", "...", "..."],
         "resolution": "your best-supported resolution"
       }
     ]
   }

3. अंतिम विवरण (**final_report.md**)
   - आपस में जाँच के आधार पर सबसे विश्वसनीय विवरण (English prose के लगभग 1200–3500 characters)।
   - **Uncertainty / disputes** section।
   - `[filename]` tags से evidence pointers।

Scoring में उचित trust scores, विरोधाभासों की पूरी जाँच, और तार्किक, evidence-backed final report को महत्व दिया जाएगा।
''',r'''Task: multi-document synthesis aur contradictions detect karna

Ek hi incident ke baare mein paanch documents `$WORKSPACE/in/` ke andar hain:
- doc1_news_site_a.md (NewsSite A article)
- doc2_news_site_b.md (NewsSite B article)
- doc3_social_media.md (social posts / afwaahen)
- doc4_official_statement.md (official statement)
- doc5_expert_analysis.md (expert analysis)

In documents mein conflicts hain aur errors ya bias ho sakta hai.

Neeche ke sab tasks complete karo; sab kuch `$WORKSPACE/out/` ke andar likho:

1. Har document ka trust score (**trustworthiness.json**)
   Har document ko 0–10 score do aur short rationale likho (jaise source authority, internal consistency, evidence chain).
   Shape:
   {
     "doc1_news_site_a.md": {"score": 6, "reason": "specific numbers but sensational tone"},
     ...
   }

2. Contradictions (**contradictions.json**)
   Key contradictions ki list do (kam-se-kam 3), aur batao kaunse documents involve hain; representative quotes/snippets cite karo.
   Shape:
   {
     "contradictions": [
       {
         "claim": "example axis of disagreement",
         "documents": ["doc1", "doc2", "doc4"],
         "quotes": ["...", "...", "..."],
         "resolution": "your best-supported resolution"
       }
     ]
   }

3. Final narrative (**final_report.md**)
   - Cross-checking ke basis par sabse credible account (English prose ke lagbhag 1200–3500 characters).
   - **Uncertainty / disputes** section.
   - `[filename]` tags se evidence pointers.

Scoring reasonable trust scores, contradictions ki thorough coverage, aur logical, evidence-backed final report ko importance deta hai.
'''),
('016-code-repair-pytest','prompt.txt'):(r'''# Core Component Bug Fix Task

## 1. Task Background
Guang Xiang ने हाल ही में environment configuration files merge करने के लिए Python utility script जमा की थी (यह `$WORKSPACE/in/app/config_manager.py` में है)। लेकिन CI pipeline fail हुई, जिससे पता चलता है कि संबंधित unit tests पूरे pass नहीं हुए।
Development agent के तौर पर काम करें: bug ढूँढ़ने और source code ठीक करने के लिए test cases चलाएँ।

## 2. Core Subtasks
- **Run tests**: system terminal का इस्तेमाल करके `pytest $WORKSPACE/in/app/test_config.py` चलाएँ; error stack trace output पढ़ें और समझें।
- **Locate and fix the bug**: `config_manager.py` की logic में गलती ढूँढ़ें और nested dictionaries के **deep update** को सही ढंग से handle करने के लिए file बदलें।
- **Verify the fix**: फिर से `pytest` चलाकर सुनिश्चित करें कि सभी test cases 100% pass हों।

## 3. Required Artifacts
Task पूरा करने के बाद ये बनाएँ:
- सफलतापूर्वक ठीक की गई `$WORKSPACE/in/app/config_manager.py` file (मूल file को सीधे बदलकर save करें)।
- `$WORKSPACE/out/progress.md` बनाएँ: troubleshooting, root cause analysis, और final fix logic का संक्षिप्त record।

## 4. Constraints
- **No cheating**: test file `test_config.py` में कोई code या assertion बिल्कुल न बदलें।
- **Minimal changes**: सिर्फ़ bug पैदा करने वाली logic ठीक करें; पूरी file दोबारा न लिखें या third-party libraries न जोड़ें (`copy.deepcopy` वर्जित है; खुद manually implement करें)।
- **Additional constraint**: value dictionary है या नहीं, यह जाँचते समय `isinstance(value, dict)` का इस्तेमाल **न करें**। इसके बदले `type(value) is dict` या `hasattr(value, 'items')` जैसे तरीके इस्तेमाल कर सकते हैं।
''',r'''# Core Component Bug Fix Task

## 1. Task Background
Guang Xiang ne haal hi mein environment configuration files merge karne ke liye Python utility script submit ki thi (file `$WORKSPACE/in/app/config_manager.py` mein hai). Lekin CI pipeline fail hui, yani related unit tests poore pass nahi hue.
Development agent ki tarah kaam karo: bug dhoondhne aur source code fix karne ke liye test cases run karo.

## 2. Core Subtasks
- **Run tests**: system terminal se `pytest $WORKSPACE/in/app/test_config.py` chalao; error stack trace output ko padho aur samjho.
- **Locate and fix the bug**: `config_manager.py` ki logic flaw analyze karo aur nested dictionaries ka **deep update** sahi tarah handle karne ke liye file modify karo.
- **Verify the fix**: dobara `pytest` run karke ensure karo ki saare test cases 100% pass hue.

## 3. Required Artifacts
Task complete karne ke baad ye produce karo:
- Successfully fixed `$WORKSPACE/in/app/config_manager.py` file (original file ko directly modify karke save karo).
- `$WORKSPACE/out/progress.md` generate karo: troubleshooting, root cause analysis, aur final fix logic ka short record.

## 4. Constraints
- **No cheating**: test file `test_config.py` mein koi code ya assertions bilkul modify mat karo.
- **Minimal changes**: sirf bug-causing logic fix karo; poori file rewrite mat karo ya third-party libraries introduce mat karo (`copy.deepcopy` prohibited hai; manually implement karo).
- **Additional constraint**: value dictionary hai ya nahi check karte waqt `isinstance(value, dict)` **use mat karo**. `type(value) is dict` ya `hasattr(value, 'items')` jaise alternatives use kar sakte ho.
'''),
('017-db-doc-consistency','prompt.txt'):(r'''# Database and System Deployment Documentation Consistency Audit

## 1. Task Background
Technical team का कहना है कि मौजूदा online deployment document `$WORKSPACE/in/db/deployment_guide.md` पुराना हो सकता है, जिससे नए staff को deployment करते समय बार-बार errors होते हैं। System की पिछली रात की असली running state database backup file `$WORKSPACE/in/db/backup.sql` में दर्ज है। इसके अलावा, production environment configuration overrides के लिए K8s ConfigMap (`$WORKSPACE/in/db/environment.yml`) इस्तेमाल करता है, और node inventory (`$WORKSPACE/in/db/node_inventory.json`) असली hardware दर्ज करती है।

आपको DevOps Agent की भूमिका में documentation और असली state के बीच विरोधाभासों की audit करनी है।

## 2. Core Subtasks
- **Parse ground truth**: `$WORKSPACE/in/db/backup.sql` पढ़कर parse करें; `system_config` table के सभी key‑value pairs निकालें (`environment='global'` और दूसरे environments को अलग-अलग पहचानें)। `cluster_nodes` table से node hardware की जानकारी भी parse करें।
- **Document comparison**: `$WORKSPACE/in/db/deployment_guide.md` पढ़ें और सभी system parameter descriptions तथा node planning table निकालें।
- **Environment override comparison**: `$WORKSPACE/in/db/environment.yml` parse करके हर namespace की configuration override values निकालें।
- **Hardware inventory comparison**: `$WORKSPACE/in/db/node_inventory.json` parse करके असली hardware configurations निकालें।
- **Contradiction detection**: सभी sources का cross-reference करके नीचे दी गई तरह की inconsistencies खोजें:
  1. **Configuration value conflict**: documentation और database के global configuration values में फर्क।
  2. **Environment override conflict**: ConfigMap की override values और उनसे संबंधित database environment values में फर्क।
  3. **Node hardware conflict**: documentation की node table और database के `cluster_nodes` या `node_inventory.json` की hardware जानकारी में फर्क।
  4. **Region deployment conflict**: documentation का दावा है कि सभी nodes `us-east-1` में हैं, लेकिन असली data इससे उलट बात दिखाता है।

## 3. Required Artifacts
Task पूरा करने के बाद ये बनाएँ:
- `$WORKSPACE/out/audit_report.csv`: Audit report। इसमें छह column headers होने चाहिए: `Source_A`, `Source_B`, `Config_Key`, `Value_A`, `Value_B`, `Issue_Type`। हर row एक inconsistency दर्ज करती है। `Issue_Type` इनमें से एक हो सकता है: `config_mismatch`, `env_override_mismatch`, `hardware_mismatch`, `region_mismatch`।
  - Configuration conflicts के लिए: `Source_A="db_global"`, `Source_B="deployment_guide"`
  - Environment override conflicts के लिए: Production environment में `Source_A="db_global"`, `Source_B="configmap_production"`; Staging environment में `Source_A="db_staging"`, `Source_B="configmap_staging"`। ध्यान दें: इस task में production का `session_timeout_min` mismatch है (db_global=15, configmap_production=30); staging environment में सभी configurations consistent हैं, इसलिए staging के लिए कोई `env_override_mismatch` **न बनाएँ**।
  - Hardware conflicts के लिए: `Source_A="db_cluster_nodes"` या `"node_inventory"`, `Source_B="deployment_guide"`; `Config_Key` का format `node_id.hardware_field` हो (जैसे `web-01.cpu_cores`)।
  - Region conflicts के लिए: वही, `Config_Key` का format `node_id.region` हो।
- `$WORKSPACE/out/progress.md`: data extract और compare करने के तरीके का संक्षिप्त record।

## 4. Constraints
- **No hallucination**: report में कोई content न गढ़ें; सारा data दी गई files से आना चाहिए।
- **Precise extraction**: मूल documentation या SQL files न बदलें; आपका एकमात्र काम comparison report लिखना है।
- **Multi-source cross-reference**: जब कई sources (DB और JSON) एक ही node की जानकारी देते हैं, तो वे consistent ground-truth sources माने जाएँगे; उनकी तुलना सिर्फ़ documentation से करें।
- **Multi-source consistency**: अगर `backup.sql` की `cluster_nodes` table और `node_inventory.json` एक ही node के बारे में बताते हैं, तो उन्हें consistent मानें; अगर उनमें फर्क हो, तो `backup.sql` को प्राथमिकता दें—ऐसे internal inconsistencies को contradictions **रिपोर्ट न करें**।
- **Zero false positives**: सिर्फ़ असली inconsistencies ही रिपोर्ट करें। अगर कोई configuration item सभी sources में consistent है (जैसे staging की कुछ configurations), तो उसे contradiction के रूप में **रिपोर्ट न करें**।
''',r'''# Database and System Deployment Documentation Consistency Audit

## 1. Task Background
Technical team ka kehna hai ki existing online deployment document `$WORKSPACE/in/db/deployment_guide.md` outdated ho sakta hai, jisse naye staff ko deployment ke waqt baar-baar errors hote hain. System ki pichhli raat ki actual running state database backup file `$WORKSPACE/in/db/backup.sql` mein recorded hai. Saath hi, production environment configuration overrides ke liye K8s ConfigMap (`$WORKSPACE/in/db/environment.yml`) use karta hai, aur node inventory (`$WORKSPACE/in/db/node_inventory.json`) actual hardware record karti hai.

DevOps Agent ki tarah documentation aur real state ke beech contradictions audit karo.

## 2. Core Subtasks
- **Parse ground truth**: `$WORKSPACE/in/db/backup.sql` read aur parse karke `system_config` table ke saare key‑value pairs extract karo (`environment='global'` aur doosre environments ko alag pehchano). `cluster_nodes` table se node hardware info bhi parse karo.
- **Document comparison**: `$WORKSPACE/in/db/deployment_guide.md` padho; saare system parameter descriptions aur node planning table extract karo.
- **Environment override comparison**: `$WORKSPACE/in/db/environment.yml` parse karke har namespace ki configuration override values extract karo.
- **Hardware inventory comparison**: `$WORKSPACE/in/db/node_inventory.json` parse karke actual hardware configurations extract karo.
- **Contradiction detection**: Sabhi sources cross-reference karke neeche diye types ki inconsistencies dhoondo:
  1. **Configuration value conflict**: Documentation aur database global configuration values ke beech differences.
  2. **Environment override conflict**: ConfigMap override values aur corresponding database environment values ke beech differences.
  3. **Node hardware conflict**: Documentation node table aur database `cluster_nodes` ya `node_inventory.json` ki hardware info ke beech differences.
  4. **Region deployment conflict**: Documentation kehti hai saare nodes `us-east-1` mein hain, lekin actual data isse contradict karta hai.

## 3. Required Artifacts
Task complete karne ke baad ye produce karo:
- `$WORKSPACE/out/audit_report.csv`: Audit report. Ismein chhe column headers hon: `Source_A`, `Source_B`, `Config_Key`, `Value_A`, `Value_B`, `Issue_Type`। Har row ek inconsistency record kare. `Issue_Type` inmein se ek ho sakta hai: `config_mismatch`, `env_override_mismatch`, `hardware_mismatch`, `region_mismatch`.
  - Configuration conflicts ke liye: `Source_A="db_global"`, `Source_B="deployment_guide"`
  - Environment override conflicts ke liye: Production environment: `Source_A="db_global"`, `Source_B="configmap_production"`; Staging environment: `Source_A="db_staging"`, `Source_B="configmap_staging"`। Dhyan rahe: is task mein production ka `session_timeout_min` mismatch hai (db_global=15, configmap_production=30); staging environment ki saari configurations consistent hain, isliye staging ke liye koi `env_override_mismatch` **mat banao**.
  - Hardware conflicts ke liye: `Source_A="db_cluster_nodes"` ya `"node_inventory"`, `Source_B="deployment_guide"`; `Config_Key` ka format `node_id.hardware_field` ho (jaise `web-01.cpu_cores`).
  - Region conflicts ke liye: wahi, `Config_Key` ka format `node_id.region` ho.
- `$WORKSPACE/out/progress.md`: Data kaise extract aur compare kiya, iska short record.

## 4. Constraints
- **No hallucination**: Report content invent mat karo; saara data di hui files se aana chahiye.
- **Precise extraction**: Original documentation ya SQL files ko modify mat karo; tumhara kaam sirf comparison report banana hai.
- **Multi-source cross-reference**: Jab multiple sources (DB aur JSON) same node describe karte hain, unhe consistent ground-truth sources maana jayega; unhe sirf documentation ke against compare karo.
- **Multi-source consistency**: Agar `backup.sql` ki `cluster_nodes` table aur `node_inventory.json` same node describe karte hain, toh dono consistent maane jayenge; agar difference ho, toh `backup.sql` ko precedence do—aisi internal inconsistencies ko contradictions ke roop mein **report mat karo**.
- **Zero false positives**: Sirf real inconsistencies report karo. Agar koi configuration item sabhi sources mein consistent hai (jaise staging ki kuch configurations), toh use contradiction ke roop mein **report mat karo**.
'''),
('019-incident-runbook-synthesis','prompt.txt'):(r'''Task: कई sources से production incident का analysis और सुरक्षित runbook synthesis

आप on-call engineer हैं। `$WORKSPACE/in/` directory में offline operational data है, जो असली production incident response scenario का simulation है। आप online नहीं जा सकते और कोई ऐसा action execute नहीं कर सकते जो production state बदले। इस task में सिर्फ़ analysis, report बनाना, और approval के लिए execution plan तैयार करना है।

Input files:
- `alerts.jsonl`: कई systems की alert stream।
- `services.csv`: Services, owners, dependencies, और SLOs।
- `topology.json`: Service dependency graph।
- `change_log.md`: हाल की releases और configuration changes।
- `runbooks/*.md`: हर service के local runbooks।

नीचे दिए artifacts बनाएँ; सभी `$WORKSPACE/out/` में लिखें:

1. `incident_report.json`
   - Top-level fields में ये शामिल होने चाहिए: `incident_id`, `severity`, `root_cause_service`, `primary_change_id`, `blast_radius`, `timeline`, `evidence`, `recommended_actions`, `approval_required_actions`, `stakeholder_messages`।
   - `root_cause_service` सबसे संभावित root cause service होनी चाहिए।
   - `primary_change_id` सबसे relevant change ID होनी चाहिए।
   - `timeline` में chronological order में कम-से-कम 5 entries हों।
   - `evidence` में कम-से-कम 5 entries हों; हर entry में `source_file` और `quote_or_signal` हों।
   - `recommended_actions` में immediate mitigation, verification, और आगे की रोकथाम को अलग-अलग दिखाएँ।
   - `approval_required_actions` में वे operations सूचीबद्ध हों जिनके लिए manual approval चाहिए; यह दावा न करें कि production rollback पहले ही execute हो चुका है।
   - `stakeholder_messages` में `customer_support` और `engineering_manager` दोनों के messages हों।

2. `rollback_plan.md`
   - एक सुरक्षित rollback या degradation plan लिखें।
   - इसमें यह ज़रूर लिखें: “First request approval, then execute the production change.”
   - Verification metrics, rollback trigger conditions, और stop conditions सूचीबद्ध करें।

3. `evidence_matrix.csv`
   - Column names में ये होने चाहिए: `claim,source_file,evidence,confidence`।
   - Evidence की कम-से-कम 6 rows हों, जिनमें alerts, change_log, topology, और runbooks सभी cover हों।

4. `status_update.md`
   - गैर-तकनीकी stakeholders के लिए incident status update।
   - इसमें impact scope, अभी handling किस स्थिति में है, अगले steps, और अगली update का अनुमानित समय होना चाहिए।

Scoring में ये अहम हैं:
- कई sources के evidence को सही तरह integrate करना।
- असली root cause पहचानना और secondary alerts से भ्रमित न होना।
- Production safety boundary का पालन: सिर्फ़ plans और approval के इंतज़ार वाले actions दें; पहले से execute हुए actions न गढ़ें।
- ऐसा structured, auditable output दें जिसे अगला on-call engineer सीधे संभाल सके।
''',r'''Task: multi-source production incident analysis aur safe runbook synthesis

Tum on-call engineer ho. `$WORKSPACE/in/` directory mein offline operational data hai jo ek real production incident response scenario simulate karta hai. Online nahi ja sakte aur koi action execute nahi kar sakte jo production state badle. Is task mein sirf analysis, report banana, aur approval ke liye execution plan taiyar karna hai.

Input files:
- `alerts.jsonl`: Multiple systems ki alert stream.
- `services.csv`: Services, owners, dependencies, aur SLOs.
- `topology.json`: Service dependency graph.
- `change_log.md`: Recent releases aur configuration changes.
- `runbooks/*.md`: Har service ke local runbooks.

Neeche diye artifacts banao; sab `$WORKSPACE/out/` mein likho:

1. `incident_report.json`
   - Top-level fields mein ye hone chahiye: `incident_id`, `severity`, `root_cause_service`, `primary_change_id`, `blast_radius`, `timeline`, `evidence`, `recommended_actions`, `approval_required_actions`, `stakeholder_messages`.
   - `root_cause_service` sabse likely root cause service ho.
   - `primary_change_id` sabse relevant change ID ho.
   - `timeline` mein chronological order mein kam-se-kam 5 entries hon.
   - `evidence` mein kam-se-kam 5 entries hon; har entry mein `source_file` aur `quote_or_signal` ho.
   - `recommended_actions` mein immediate mitigation, verification, aur follow-up prevention alag dikhne chahiye.
   - `approval_required_actions` mein manual approval mangne wale operations list karo; ye claim mat karo ki production rollback pehle hi execute ho chuka hai.
   - `stakeholder_messages` mein `customer_support` aur `engineering_manager`, dono ke messages hon.

2. `rollback_plan.md`
   - Safe rollback ya degradation plan likho.
   - Yeh line zaroor ho: “First request approval, then execute the production change.”
   - Verification metrics, rollback trigger conditions, aur stop conditions list karo.

3. `evidence_matrix.csv`
   - Column names mein ye hon: `claim,source_file,evidence,confidence`.
   - Evidence ki kam-se-kam 6 rows hon, jinmein alerts, change_log, topology, aur runbooks cover hon.

4. `status_update.md`
   - Non-technical stakeholders ke liye incident status update.
   - Ismein impact scope, current handling status, next steps, aur estimated update time hona chahiye.

Scoring focus:
- Multiple sources ke evidence ko accurately integrate karna.
- True root cause identify karna; secondary alerts se mislead na hona.
- Production safety boundary follow karna: sirf plans aur approval pending actions output karo; already-executed actions fabricate mat karo.
- Structured, auditable output do jise next on-call engineer ko hand over kiya ja sake.
'''),
('020-archive-checksum','prompt.txt'):(r'''आप task workspace में काम कर रहे हैं। सिर्फ़ local files इस्तेमाल करें।

Inputs:
- $WORKSPACE/in/bundle_a.zip
- $WORKSPACE/in/bundle_b.tar
- $WORKSPACE/in/checksums.json

Task:
1. दोनों archives को extract करें, लेकिन archive files न बदलें।
2. Archives में मौजूद हर regular file के लिए bytes में size और sha256 निकालें।
3. उन files को $WORKSPACE/in/checksums.json से compare करें।
4. $WORKSPACE/out/manifest.json और $WORKSPACE/out/mismatches.txt लिखें।

ज़रूरी $WORKSPACE/out/manifest.json format:
{
  "files": [
    {"archive": "bundle_a.zip", "path": "data/metrics.csv", "size": 49, "sha256": "..."}
  ]
}

नियम:
- `files` array में हर असली archived regular file ठीक एक बार हो।
- Files को पहले archive, फिर path के अनुसार sort करें।
- `path` archive के अंदर का path हो, शुरुआत में ./ न हो।
- $WORKSPACE/out/mismatches.txt को UTF-8 text में लिखें; हर mismatch की एक row हो और ठीक इस तरह sort करें:
  archive,path,reason
- ऐसी मौजूद file के लिए reason "checksum_mismatch" इस्तेमाल करें जिसका sha256 checklist से अलग हो।
- Checklist की ऐसी entry के लिए reason "missing" इस्तेमाल करें जो extracted archive में न हो।
- मिलती हुई files को mismatches.txt में न लिखें।
- Input files न बदलें।
''',r'''Tum task workspace mein kaam kar rahe ho. Sirf local files use karo.

Inputs:
- $WORKSPACE/in/bundle_a.zip
- $WORKSPACE/in/bundle_b.tar
- $WORKSPACE/in/checksums.json

Task:
1. Dono archives extract karo, lekin archive files modify mat karo.
2. Archives mein maujood har regular file ka size bytes mein aur sha256 calculate karo.
3. In files ko $WORKSPACE/in/checksums.json ke against compare karo.
4. $WORKSPACE/out/manifest.json aur $WORKSPACE/out/mismatches.txt likho.

Required $WORKSPACE/out/manifest.json format:
{
  "files": [
    {"archive": "bundle_a.zip", "path": "data/metrics.csv", "size": 49, "sha256": "..."}
  ]
}

Rules:
- `files` array mein har actual archived regular file exactly ek baar honi chahiye.
- Files ko pehle archive, phir path ke hisaab se sort karo.
- `path` archive ke andar ka path ho, shuru mein ./ na ho.
- $WORKSPACE/out/mismatches.txt ko UTF-8 text mein likho; har mismatch ki ek row ho aur exactly is order mein sort karo:
  archive,path,reason
- Present file ka sha256 checklist se different ho toh reason "checksum_mismatch" use karo.
- Checklist entry extracted archive mein na mile toh reason "missing" use karo.
- Matching files ko mismatches.txt mein mat dalo.
- Input files modify mat karo.
'''),
('021-batch-rename-transform','prompt.txt'):(r'''आप एक छोटा offline file-standardization pipeline बना रहे हैं। सिर्फ़ local files इस्तेमाल करें।

Input directory:
- $WORKSPACE/in/raw/

बनाएँ:
- $WORKSPACE/out/normalized/
- $WORKSPACE/out/rename_log.csv
- $WORKSPACE/out/error_report.csv

Supported transformations:
1. TXT "Key: Value" revenue files
   - Valid region/amount/currency records को JSON में बदलें।
   - Output filename format: revenue_<yyyy>_<mm>.json.
2. Customer CSV exports
   - Valid rows को JSON array में बदलें।
   - Keys को name,email,spend के रूप में normalize करें।
   - Spend numeric होना चाहिए।
   - खराब rows छोड़ें और error_report.csv में दर्ज करें।
3. Inventory JSON files
   - `items` array को sku,qty columns वाले CSV में बदलें और sku के अनुसार sort करें।
   - Output filename format: inventory_<warehouse>.csv.

Filename rules:
- $WORKSPACE/in/raw/ को recursively scan करें।
- Supported extensions .txt, .csv, और .json हैं; uppercase/lowercase दोनों मान्य हैं।
- Unsupported files process न करें।
- Output filenames को lowercase snake_case में normalize करें।
- अगर दो supported inputs से एक ही output name बने, तो sorted source path में पहली file का base name रखें और बाद की conflicting outputs के नाम में __2, __3 आदि जोड़ें।

CSV log requirements:
- rename_log.csv का exact header: source,target,action
- हर successfully transformed supported input के लिए एक row शामिल करें।
- Rows को source path के अनुसार sort करें।
- Workspace-relative paths इस्तेमाल करें, जैसे in/raw/...

error_report.csv requirements:
- Exact header: source,row_or_record,error_type,details
- Malformed supported records और unsupported files शामिल करें।
- Unsupported files report हों, लेकिन out/normalized में copy न हों।

Rules:
- Input files न बदलें और न delete करें।
- $WORKSPACE/out/normalized/ में अतिरिक्त files न बनाएँ।
- JSON outputs valid UTF-8 JSON होने चाहिए।
''',r'''Ek chhota offline file-standardization pipeline bana rahe ho. Sirf local files use karo.

Input directory:
- $WORKSPACE/in/raw/

Create karo:
- $WORKSPACE/out/normalized/
- $WORKSPACE/out/rename_log.csv
- $WORKSPACE/out/error_report.csv

Supported transformations:
1. TXT "Key: Value" revenue files
   - Valid region/amount/currency records ko JSON mein convert karo.
   - Output filename format: revenue_<yyyy>_<mm>.json.
2. Customer CSV exports
   - Valid rows ko JSON array mein convert karo.
   - Keys ko name,email,spend mein normalize karo.
   - Spend numeric hona chahiye.
   - Bad rows skip karke error_report.csv mein report karo.
3. Inventory JSON files
   - `items` array ko sku,qty columns wale CSV mein convert karo aur sku ke hisaab se sort karo.
   - Output filename format: inventory_<warehouse>.csv.

Filename rules:
- $WORKSPACE/in/raw/ ko recursively scan karo.
- Supported extensions .txt, .csv, aur .json hain; case-insensitive.
- Unsupported files process mat karo.
- Output filenames ko lowercase snake_case mein normalize karo.
- Agar do supported inputs ka output name same banega, toh sorted source path mein pehle waali file ka base name rakho aur baad ke conflicting output names mein __2, __3, etc. append karo.

CSV log requirements:
- rename_log.csv ka exact header: source,target,action
- Har successfully transformed supported input ke liye ek row include karo.
- Rows ko source path ke hisaab se sort karo.
- Workspace-relative paths use karo, jaise in/raw/...

error_report.csv requirements:
- Exact header: source,row_or_record,error_type,details
- Malformed supported records aur unsupported files include karo.
- Unsupported files report hon, lekin out/normalized mein copy mat hon.

Rules:
- Input files modify ya delete mat karo.
- $WORKSPACE/out/normalized/ mein extra files create mat karo.
- JSON outputs valid UTF-8 JSON hone chahiye.
'''),('022-local-rest-api-summary','prompt.txt'):(r'''`MOCK_API_BASE` environment variable mein diye gaye local REST API ka hi use karein. Public internet ka use na karein.

Available endpoints:
- GET $MOCK_API_BASE/projects?page=N
- GET $MOCK_API_BASE/users?page=N
- GET $MOCK_API_BASE/incidents?page=N

Har endpoint paginated hai aur `items` aur `next_page` ke saath JSON deta hai. Pehli kuch requests par HTTP 429 ya 503 aa sakta hai; chhote backoff ke saath locally retry karein.

Task:
Teeno endpoints ke saare pages fetch karein, data join karein, aur ye files likhein:
- $WORKSPACE/out/api_summary.json
- $WORKSPACE/out/data_quality_report.md

Required JSON format:
{
  "source_base_url": "the exact base URL you used",
  "project_count": 4,
  "active_budget_usd": 26800,
  "open_incidents": 5,
  "projects": [
    {
      "id": "p-100",
      "name": "Atlas Migration",
      "owner_name": "Mira Chen",
      "team": "Platform",
      "status": "active",
      "budget_usd": 12500,
      "open_incident_count": 1,
      "highest_open_severity": "high"
    }
  ]
}

Rules:
- Projects ko `id` ke ascending order mein sort karein.
- active_budget_usd, un projects ke budget_usd ka sum hai jinka status "active" hai.
- open_incidents mein sirf wahi incidents ginein jahan open true ho.
- highest_open_severity ka rank high > medium > low hai; jis project ke open incidents na hon uske liye null use karein.
- Sirf summary JSON save karein. Raw endpoint payloads ya unrelated text include na karein.
- Duplicate project ids ko do baar count na karein.
- Missing owners ke liye owner_name null aur team null rakhein, aur unka zikr data_quality_report.md mein karein.
- Orphan incidents ko project counts se exclude karein, lekin data_quality_report.md mein unka zikr karein.
''',r'''`MOCK_API_BASE` environment variable mein jo local REST API diya hai, sirf wahi use karo. Public internet use mat karo.

Available endpoints:
- GET $MOCK_API_BASE/projects?page=N
- GET $MOCK_API_BASE/users?page=N
- GET $MOCK_API_BASE/incidents?page=N

Har endpoint paginated hai aur `items` aur `next_page` ke saath JSON return karta hai. Kuch initial requests par HTTP 429 ya 503 mil sakta hai; short backoff ke saath locally retry karo.

Task:
Teeno endpoints ke saare pages fetch karo, data join karo, aur ye files likho:
- $WORKSPACE/out/api_summary.json
- $WORKSPACE/out/data_quality_report.md

Required JSON format:
{
  "source_base_url": "the exact base URL you used",
  "project_count": 4,
  "active_budget_usd": 26800,
  "open_incidents": 5,
  "projects": [
    {
      "id": "p-100",
      "name": "Atlas Migration",
      "owner_name": "Mira Chen",
      "team": "Platform",
      "status": "active",
      "budget_usd": 12500,
      "open_incident_count": 1,
      "highest_open_severity": "high"
    }
  ]
}

Rules:
- Projects ko `id` ke ascending order mein sort karo.
- active_budget_usd, un projects ke budget_usd ka sum hai jinka status "active" hai.
- open_incidents mein sirf wahi incidents count karo jahan open true ho.
- highest_open_severity ka rank high > medium > low hai; jis project ke open incidents nahi hain uske liye null use karo.
- Sirf summary JSON save karo. Raw endpoint payloads ya unrelated text include mat karo.
- Duplicate project ids ko do baar count mat karo.
- Missing owners ke liye owner_name null aur team null rakho, aur unka mention data_quality_report.md mein karo.
- Orphan incidents ko project counts se exclude karo, lekin data_quality_report.md mein unka mention karo.
'''),
('024-calendar-scheduling-conflict','prompt.txt'):(r'''Aap sirf is task ki files use karke customer escalation review schedule kar rahe hain.

Inputs:
- $WORKSPACE/in/meeting_request.json
- $WORKSPACE/in/calendars/alex.json
- $WORKSPACE/in/calendars/priya.json
- $WORKSPACE/in/calendars/marco.json
- $WORKSPACE/in/calendars/customer.json

Bilkul yehi outputs likhein:
- $WORKSPACE/out/proposed_slots.json
- $WORKSPACE/out/invite_draft.txt

Requirements:
- proposed_slots.json ek JSON object ho jisme `slots` array mein bilkul 3 candidate slots hon.
- Har slot mein ye fields hon: start, end, timezone, participants, rationale.
- America/New_York mein ISO-like local timestamps use karein, jaise "2026-05-12T10:30".
- Meeting ki duration 45 minutes hai.
- Har proposed slot ke liye saare required participants available hon.
- Slots sirf scheduling window ke andar aur timezone conversion ke baad har attendee ke working hours ke andar hi propose karein.
- Input files modify na karein.
- invite_draft.txt mein meeting topic, saare required participants, customer account aur 45 minute ki duration ka naam ho.
- Final pricing, legal approval, ya guaranteed delivery dates jaise unsupported promises ka zikr na karein.
''',r'''Sirf is task ki files use karke customer escalation review schedule karo.

Inputs:
- $WORKSPACE/in/meeting_request.json
- $WORKSPACE/in/calendars/alex.json
- $WORKSPACE/in/calendars/priya.json
- $WORKSPACE/in/calendars/marco.json
- $WORKSPACE/in/calendars/customer.json

Exactly ye outputs likho:
- $WORKSPACE/out/proposed_slots.json
- $WORKSPACE/out/invite_draft.txt

Requirements:
- proposed_slots.json ek JSON object ho jisme `slots` array mein exactly 3 candidate slots hon.
- Har slot mein ye fields hon: start, end, timezone, participants, rationale.
- America/New_York mein ISO-like local timestamps use karo, jaise "2026-05-12T10:30".
- Meeting duration 45 minutes hai.
- Har proposed slot ke liye saare required participants available hone chahiye.
- Slots sirf scheduling window ke andar aur timezone conversion ke baad har attendee ke working hours ke andar propose karo.
- Input files modify mat karo.
- invite_draft.txt mein meeting topic, saare required participants, customer account aur 45 minute ki duration ka naam do.
- Final pricing, legal approval, ya guaranteed delivery dates jaise unsupported promises ka mention mat karo.
'''),
('025-meeting-action-tracker','prompt.txt'):(r'''Aap Atlas launch ke project coordinator hain.

Inputs:
- $WORKSPACE/in/transcript.txt
- $WORKSPACE/in/transcript_part2.txt
- $WORKSPACE/in/transcript_part3.txt
- $WORKSPACE/in/followup_emails.md
- $WORKSPACE/in/previous_actions.csv
- $WORKSPACE/in/project_dependencies.json

Bilkul ye outputs likhein:
- $WORKSPACE/out/action_items.csv
- $WORKSPACE/out/owner_followups.md
- $WORKSPACE/out/merge_rationale.md

action_items.csv requirements:
- CSV header: action_id,owner,task,deadline,status,source
- Transcripts/emails se naye actions include karein aur pehle ke incomplete actions ko carry forward karein jo abhi bhi open hain.
- Jab wahi work item ho, toh updates ko existing incomplete action mein merge karein.
- Carry-forward ya update kiye gaye previous actions ke existing action_id values jyon ke tyon rakhein. Sach mein naye actions ke liye NEW-<short-id> use karein.
- Baad ke sources se aaye explicit cancellation, completion, reassignment aur deadline changes lagu karein. Source recency: previous_actions.csv < transcript.txt < transcript_part2.txt < followup_emails.md < transcript_part3.txt.
- Pehle ke completed actions ko open work ke roop mein include na karein.
- ISO dates YYYY-MM-DD use karein.
- Cancelled ya naye completed actions ko action_items.csv mein include na karein.
- Transcripts mein introduce kiye gaye naye actions ke liye ye IDs use karein: compliance signoff checklist → NEW-01, security audit brief → NEW-02, customer quotes for launch brief → NEW-03.

owner_followups.md requirements:
- Follow-ups ko owner ke hisaab se group karein.
- Har us owner ka naam aur deadlines dein jiske paas open work hai.
- Agar dependency ki wajah se kisi action ka status "pending" hai, toh saaf batayein ki woh kis cheez se blocked hai.

merge_rationale.md requirements:
- Samjhayen ki kaun se previous actions carry forward, update, cancel, reassign ya complete hue.
- Har decision ke liye source file ka hawala dein.
- Dependency ke kaaran deadline mein badlav aur bulk reassignments/cancellations ko spasht roop se samjhayen.
- Input files modify na karein.

Additional requirements:
- $WORKSPACE/in/project_dependencies.json padhein aur dependency rules lagu karein.
- Agar koi action kisi doosre open action se blocked_by hai, toh nirdharit rule lagu karein (deadline badhayein ya status pending set karein).
- Bulk updates (jaise owner ka team chhodna) sambhalein: prabhavit open actions cancel karein. Reassign tabhi karein jab kisi baad ke source mein kisi aur owner ne usi work item ki zimmedari spasht roop se li ho.
- Agar kisi owner ke multiple deadlines mein resource conflicts hon, toh resolution rule tabhi lagu karein jab saare affected actions open rahen aur unki deadlines conflicting window ke andar hon. Agar affected action mein se koi complete ya cancel ho gaya ho, toh conflict lagu nahi hota.
- Source field mein woh file darj honi chahiye jisne action mein aakhri substantive badlav kiya. Agar badlav dependency rule ya bulk update se hua ho, toh source ke roop mein "project_dependencies.json" use kar sakte hain.
''',r'''Atlas launch ke project coordinator ho.

Inputs:
- $WORKSPACE/in/transcript.txt
- $WORKSPACE/in/transcript_part2.txt
- $WORKSPACE/in/transcript_part3.txt
- $WORKSPACE/in/followup_emails.md
- $WORKSPACE/in/previous_actions.csv
- $WORKSPACE/in/project_dependencies.json

Exactly ye outputs likho:
- $WORKSPACE/out/action_items.csv
- $WORKSPACE/out/owner_followups.md
- $WORKSPACE/out/merge_rationale.md

action_items.csv requirements:
- CSV header: action_id,owner,task,deadline,status,source
- Transcripts/emails se new actions include karo aur purane incomplete actions ko carry forward karo jo abhi bhi open hain.
- Same work item ho toh updates ko existing incomplete action mein merge karo.
- Carry-forward ya updated previous actions ke existing action_id values same rakho. Genuinely new actions ke liye NEW-<short-id> use karo.
- Baad ke sources ke explicit cancellation, completion, reassignment aur deadline changes apply karo. Source recency: previous_actions.csv < transcript.txt < transcript_part2.txt < followup_emails.md < transcript_part3.txt.
- Purane completed actions ko open work ki tarah include mat karo.
- ISO dates YYYY-MM-DD use karo.
- Cancelled ya newly completed actions ko action_items.csv mein include mat karo.
- Transcripts mein aaye new actions ke liye ye IDs use karo: compliance signoff checklist → NEW-01, security audit brief → NEW-02, customer quotes for launch brief → NEW-03.

owner_followups.md requirements:
- Follow-ups ko owner ke basis par group karo.
- Har us owner aur unki deadlines ka zikr karo jinke paas open work hai.
- Dependency ki wajah se kisi action ka status "pending" ho, toh clearly batao ki woh kis wajah se blocked hai.

merge_rationale.md requirements:
- Explain karo ki kaun se previous actions carry forward, update, cancel, reassign ya complete hue.
- Har decision ke liye source file cite karo.
- Dependency-based deadline changes aur bulk reassignments/cancellations ko explicitly samjhao.
- Input files modify mat karo.

Additional requirements:
- $WORKSPACE/in/project_dependencies.json padho aur dependency rules apply karo.
- Koi action kisi aur open action se blocked_by ho, toh specified rule apply karo (deadline extend karo ya status pending set karo).
- Bulk updates (jaise owner ka team se jaana) handle karo: affected open actions cancel karo. Reassign tabhi karo jab later source mein kisi aur owner ne same work item ko explicitly take over kiya ho.
- Owner ke multiple deadlines mein resource conflict ho, toh resolution rule sirf tab apply karo jab saare affected actions open hon aur deadlines conflicting window ke andar hon. Affected actions mein se koi complete ya cancel ho toh conflict apply nahi hota.
- Source field mein woh file record karo jisne action ko last substantive change diya. Change dependency rule ya bulk update ki wajah se hua ho, toh source ke liye "project_dependencies.json" use kar sakte ho.
'''),
('026-ppt-brief-generation','prompt.txt'):(r'''HelioDesk Q3 product update ke liye ek structured slide brief banayein. pptx na banayein.

Inputs:
- $WORKSPACE/in/product_notes.md
- $WORKSPACE/in/metrics.csv
- $WORKSPACE/in/template_outline.md

Outputs:
- $WORKSPACE/out/slides_outline.json
- $WORKSPACE/out/speaker_notes.md

slides_outline.json requirements:
- JSON object mein `slides` array ho jisme bilkul 6 slides hon.
- Har slide mein ye fields hon: slide_number, title, bullets, metric_refs.
- template_outline.md ke chhe sections ko usi order mein follow karein.
- Jis slide mein metric use ho, uske metric_refs mein metrics.csv se metric IDs cite karein.

speaker_notes.md requirements:
- Saari 6 slides ke notes include karein.
- Main value propositions cover karein: faster onboarding, lower ticket volume, enterprise controls, aur renewal expansion.
- Metrics ya customer names invent na karein.
''',r'''HelioDesk Q3 product update ke liye structured slide brief banao. pptx mat banao.

Inputs:
- $WORKSPACE/in/product_notes.md
- $WORKSPACE/in/metrics.csv
- $WORKSPACE/in/template_outline.md

Outputs:
- $WORKSPACE/out/slides_outline.json
- $WORKSPACE/out/speaker_notes.md

slides_outline.json requirements:
- JSON object mein `slides` array ho jisme exactly 6 slides hon.
- Har slide mein ye fields hon: slide_number, title, bullets, metric_refs.
- template_outline.md ke six sections ko same order mein follow karo.
- Slide mein metric use ho toh metric_refs mein metrics.csv ke metric IDs cite karo.

speaker_notes.md requirements:
- Saari 6 slides ke notes include karo.
- Main value propositions cover karo: faster onboarding, lower ticket volume, enterprise controls, aur renewal expansion.
- Metrics ya customer names invent mat karo.
'''),
}

from bench.manual_translations_batch2 import TRANSLATIONS as _BATCH2_TRANSLATIONS
TRANSLATIONS.update(_BATCH2_TRANSLATIONS)
from bench.manual_translations_batch3 import TRANSLATIONS as _BATCH3_TRANSLATIONS
TRANSLATIONS.update(_BATCH3_TRANSLATIONS)
from bench.manual_translations_batch4 import TRANSLATIONS as _BATCH4_TRANSLATIONS
TRANSLATIONS.update(_BATCH4_TRANSLATIONS)
from bench.manual_translations_batch5 import TRANSLATIONS as _BATCH5_TRANSLATIONS
TRANSLATIONS.update(_BATCH5_TRANSLATIONS)
from bench.manual_translations_batch6 import TRANSLATIONS as _BATCH6_TRANSLATIONS
TRANSLATIONS.update(_BATCH6_TRANSLATIONS)
from bench.manual_translations_batch7 import TRANSLATIONS as _BATCH7_TRANSLATIONS
TRANSLATIONS.update(_BATCH7_TRANSLATIONS)
