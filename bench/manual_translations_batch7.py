"""Hand-written Hindi and Hinglish variants for two multi-round tasks."""
TRANSLATIONS = {
('059-event-update-replan','prompt_round1.txt'):(r'''Round 1 of 2: shuruati staffing plan banayein.

$WORKSPACE/in/base_event.json aur $WORKSPACE/in/team_availability.json padhein. $WORKSPACE/out/original_plan.json banayein.

Plan mein "Atlas Launch Webinar" ke liye chaar work blocks schedule hon: setup, rehearsal, live_support, aur teardown. Sirf fixture mein available logon ka use karein. Room, start, end, assigned_people, aur assumptions include karein.

Abhi $WORKSPACE/out/revised_plan.json ya $WORKSPACE/out/diff.md na banayein. Input files modify na karein.
''',r'''Round 1 of 2: initial staffing plan banao.

$WORKSPACE/in/base_event.json aur $WORKSPACE/in/team_availability.json padho. $WORKSPACE/out/original_plan.json banao.

Plan mein "Atlas Launch Webinar" ke liye chaar work blocks schedule karo: setup, rehearsal, live_support aur teardown. Fixture mein jo log available hain sirf unhi ko use karo. Room, start, end, assigned_people aur assumptions include karo.

Abhi $WORKSPACE/out/revised_plan.json ya $WORKSPACE/out/diff.md mat banao. Input files modify mat karo.
'''),
('059-event-update-replan','prompt_round2.txt'):(r'''Round 2 of 2: nayi constraint ke baad plan revise karein.

Existing $WORKSPACE/out/original_plan.json aur $WORKSPACE/in/update_notice.json padhein. Ye banayein:
- $WORKSPACE/out/revised_plan.json
- $WORKSPACE/out/diff.md

Update notice mein ye constraints jodi gayi hain:
- live_support ko Room B mein shift karna hoga
- Chen 13:00 ke baad unavailable hain
- rehearsal 11:00 se pehle khatam honi chahiye
- live_support se pehle 15-minute accessibility check add karein

Original plan ke useful, unaffected setup/teardown decisions preserve karein. $WORKSPACE/out/diff.md mein added, removed, aur changed items list hone chahiye. Input files modify na karein.
''',r'''Round 2 of 2: nayi constraint ke baad plan revise karo.

Existing $WORKSPACE/out/original_plan.json aur $WORKSPACE/in/update_notice.json padho. Banao:
- $WORKSPACE/out/revised_plan.json
- $WORKSPACE/out/diff.md

Update notice ye constraints add karta hai:
- live_support ko Room B mein move karna hoga
- Chen 13:00 ke baad unavailable hain
- rehearsal 11:00 se pehle end honi chahiye
- live_support se pehle 15-minute accessibility check add karo

Original plan ke useful unaffected setup/teardown decisions preserve karo. $WORKSPACE/out/diff.md mein added, removed aur changed items list karo. Input files modify mat karo.
'''),
('060-task-cancellation-cleanup','prompt_round1.txt'):(r'''Round 1 of 2: export preparation shuru karein.

$WORKSPACE/in/export_request.json aur $WORKSPACE/in/customer_segments.csv padhein. Banayein:
- $WORKSPACE/out/state.json
- $WORKSPACE/out/tmp/export_manifest_draft.json
- $WORKSPACE/out/audit.log

State mein status "running", request_id "cancel-77", aur planned artifacts ki list honi chahiye. tmp draft mein segment count aur planned output names hon, lekin final export files na banayein.

Input files modify na karein.
''',r'''Round 1 of 2: export preparation start karo.

$WORKSPACE/in/export_request.json aur $WORKSPACE/in/customer_segments.csv padho. Banao:
- $WORKSPACE/out/state.json
- $WORKSPACE/out/tmp/export_manifest_draft.json
- $WORKSPACE/out/audit.log

State mein status "running", request_id "cancel-77" aur planned artifacts ki list honi chahiye. tmp draft mein segment count aur planned output names hon, par final export files mat banao.

Input files modify mat karo.
'''),
('060-task-cancellation-cleanup','prompt_round2.txt'):(r'''Round 2 of 2: cancel karke cleanup karein.

$WORKSPACE/out/state.json, $WORKSPACE/out/tmp/export_manifest_draft.json, aur $WORKSPACE/in/cancel_notice.json padhein. Cancellation authoritative hai.

Update/create karein:
- $WORKSPACE/out/state.json
- $WORKSPACE/out/cancellation_report.md
- $WORKSPACE/out/audit.log

Required behavior:
- state.status "cancelled" hona chahiye
- state.cancel_reason notice se match karna chahiye
- $WORKSPACE/out/tmp ke andar ke temporary files aur directories remove karein
- $WORKSPACE/out/audit.log aur cancellation_report.md mein audit trail preserve karein
- Input files delete ya modify na karein
- Final export files na banayein
''',r'''Round 2 of 2: cancel karke cleanup karo.

$WORKSPACE/out/state.json, $WORKSPACE/out/tmp/export_manifest_draft.json aur $WORKSPACE/in/cancel_notice.json padho. Cancellation authoritative hai.

Update/create karo:
- $WORKSPACE/out/state.json
- $WORKSPACE/out/cancellation_report.md
- $WORKSPACE/out/audit.log

Required behavior:
- state.status "cancelled" hona chahiye
- state.cancel_reason notice se match kare
- $WORKSPACE/out/tmp ke andar temporary files aur directories remove karo
- $WORKSPACE/out/audit.log aur cancellation_report.md mein audit trail preserve karo
- Input files delete ya modify mat karo
- Final export files mat banao
'''),
}
