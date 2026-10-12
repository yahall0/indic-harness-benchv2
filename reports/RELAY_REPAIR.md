# Relay repair and resumed execution

A reproducible response-parser bug is fixed: an optional tool_calls field containing null previously raised an exception. The repaired relay removes that optional null field while preserving generated text and function arguments. Raw parsed responses are saved before normalization; future failures record the stage and exception type without logging credentials or exception URLs.

**The specific cause of the original task 001 Hindi failure remains unproven.** Runtime v1 saved only a generic gate classification, so the historical exception cannot be reconstructed. The repair addresses a demonstrated defect and verifies Hindi handling; it does not retroactively establish that defect as the historical cause.

All 24 unit tests passed. Docker tests passed for Hindi request/response preservation, nullable tool-call responses through actual OpenClaw, multi-round state, isolation, quota progression and saved-result recovery. These Docker tests used simulated inference. Three separate small real provider probes in English, Hindi and Hinglish succeeded, consuming 217 input and 103 output tokens in total; they are diagnostic calls, excluded from benchmark results.

The original 120 run IDs and every existing status were verified unchanged. Four completed outcomes scored 1.00. Task 001 Hindi remains an infrastructure failure; task 002 English was interrupted when the user requested a stop and is annotated separately. Neither record was silently rerun or included as valid language-performance evidence.

Runtime revision 2 was frozen and all readiness gates passed. The controller resumed only the 114 unstarted conditions. It still pauses on ambiguous errors, accounting failures or exhausted credentials. The live monitor displays infrastructure states without treating their diagnostic grader scores as language-performance scores.

The study ID stays constant so a runtime repair cannot accidentally create a second set of 120 attempts. Every new outcome records its runtime freeze hash. CSV/JSONL exports now distinguish runtime versions and the operator-requested stop. Runtime v1 source, freeze and check reports are archived under runtime_revisions/v1 in this review package. Dataset prompts, tasks, model settings, grading and inference budgets remain identical; disclose the relay repair and runtime-version split in the paper.

Use MONITORING.md for the scoreboard, saved results, emergency stop and recovery commands. Earlier READY_TO_START.md and handoff files describe historical stages.
