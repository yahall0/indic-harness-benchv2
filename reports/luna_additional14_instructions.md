# Luna handoff: translate only the 14 additional tasks, then stop

Project: `C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench`.
Python: `C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

The user asked to pause before translation to switch to GPT-6 Luna. Begin this stage only after that switch is confirmed. Work in this chat; do not delegate. The original 40 tasks, 138 prompt files, translation reviews and all 120 recorded attempts are immutable. The additions must use precisely the same evaluation and analysis methodology. Do not launch benchmarks, call Ollama, probe keys, change inference settings or budgets, rebuild containers, freeze the dataset, or modify original references.

## Scope

Read `dataset/extension_selection.json` and `dataset/extension_prompt_inventory.json`. Translate these 14 tasks only:

028-email-thread-merge; 032-customer-followup-draft; 037-policy-clause-retrieval; 044-ci-config-repair; 048-release-note-changelog; 054-budget-variance-analysis; 055-funnel-dropoff-analysis; 065-capacity-planning; 066-rollback-readiness; 068-product-launch-ops; 079-smallfile-batch-reject-ledger; 080-schema-roundtrip-conversion; 096-offline-knowledge-qa-insufficient-evidence; 103-policy-update-replan-diff.

There are **15 English instruction turns**: one per task except 103, which has two. Create **30 files**, one Hindi and one Hinglish version of every instruction turn. The combined dataset will contain 54 tasks, 61 instruction turns and 183 language prompt files. Do not add a 55th task or reduce the set based on difficulty.

For each task, use `source_prompt_files` in `dataset/task_manifest.json` as the ordered prompt filenames. Read the already prepared English version at `tasks/<task_id>/prompts/en/<filename>`. Create the counterparts at `tasks/<task_id>/prompts/hi/<filename>` and `tasks/<task_id>/prompts/hinglish/<filename>`. Read and write **UTF-8 explicitly**, preserving the original baselines. Use LF line endings, ASCII digits and UTF-8 without a BOM. Never import reference task modules or execute them on Windows/WSL.

## Translation rules

Translate the instruction body naturally. Hindi uses Devanagari with familiar technical terms; Hinglish uses conversational Roman-script Hindi with familiar English technical terms and no Devanagari. Preserve the intent, agency, sequence, scope, specificity and tone of each original instruction. Translate every user turn, including both turns of task 103.

Keep literal filenames, paths, placeholders such as `$WORKSPACE`, commands, flags, identifiers, case-sensitive JSON keys, CSV headers, enum values, required headings, exact output strings, fenced code and sample schemas unchanged. Preserve quoted and backticked literals byte-for-byte. The static checker compares counters of placeholders, backticks, fenced blocks, double-quoted strings and numbers. A checker pass cannot establish semantic equivalence: also manually inspect unquoted commands, paths, field names and required headings. Do not introduce new quoted strings or reformat dates and numbers in a way that changes protected counters.

Preserve every requirement, prohibition, negation, approval boundary, quantity, limit, date, dependency and ordering condition. Do not weaken “must,” “exactly,” “do not,” “at least,” or “only.” Do not explain solutions, add examples or hints, remove difficult requirements, translate technical literals into new identifiers, or change the agent's required output language.

Append the **exact unchanged English suffix** from `bench.translations.COMMON_CLARIFICATIONS.get(task_id, '') + bench.translations.OUTPUT_CONTRACT` to both translations, matching the English prompt. These common additions are identical across conditions, and all prose deliverables remain English in all three conditions. Do not translate or otherwise edit this suffix. Task 048 clarifies that all five listed artifacts are required; task 068 clarifies that all four listed audience segments must be addressed, with the unavailable segment mentioned only to explain exclusion. Preserve the original body and append these common clarifications; do not silently repair its contradictions differently by language.

For task 103 retain both rounds in source order, the prohibition on revised artifacts in round 1, stable decision IDs and round 2 change tracking. Preserve the supplied files and constraints; add no planning solution.

Do not inspect `validation/`, private build contexts, oracle reports, ground truth or saved solutions while translating. Use the English instructions and task manifest. Validation solutions remain outside the evaluated agent's environment.

## Semantic review and records

Review each translated turn against the English body requirement by requirement. Backtranslate or compare the Hindi and Hinglish meaning in English, then inspect negation, numbers/dates, ordering, all protected literals and naturalness. This is AI translation and self-review, not independent human validation.

Append only the 14 new keys in `dataset/translation_reviews.json`. Match the existing format: `reviewer: "AI self-review"`, `independent_human_review: false`, and all nine checks true only after actual review: `requirements`, `negations`, `numbers_and_dates`, `round_order`, `no_new_hints`, `technical_literals`, `hindi_naturalness`, `hinglish_naturalness`, `backtranslation_comparison`. Add the checked prompt filenames and brief review notes, with model provenance as GPT-6 Luna. Do not alter any original review entry.

Update only these new task entries in `dataset/task_manifest.json`: the Hindi/Hinglish translation statuses and `validation.semantic_review: "passed"`. Keep `status: "candidate"` and `validation.release_eligible: false`; final release and freezing belong to Sol. Do not alter English prompts, task IDs, fixtures, source hashes, original task entries or inference configuration.

## Checks and the stopping boundary

From the project directory, with the Python path above:

1. `python -m bench.translations` — must pass for all 54 tasks, 61 instruction turns, 183 files.
2. `python -m bench.extension` — must confirm 40 original tasks and 120 original attempts unchanged, with the original settings intact.
3. `python -m bench verify-reference` — must confirm all reference hashes unchanged.
4. `python -m unittest discover -s tests -q` — run the trusted-controller tests only; never import private validators on Windows.

Fix translation issues only within the 30 new prompt files and new review/manifest entries. Never weaken the checker or change protected English originals to force a pass. If semantic equivalence cannot be resolved, document the issue and stop for Sol instead of releasing the task.

Write `reports/luna_additional14_completion.md` with exact counts, checks, AI-review provenance and unresolved issues. Copy the completion note and static translation report into `C:\Users\prish\Documents\Codex\2026-09-30\new-chat\outputs\indic-harness-bench-review\additional-14`. Do not overwrite the original review package or results.

**STOP immediately after translation and these static checks.** Tell the user to switch back to **GPT-6.1 Sol** for final readiness, preservation checks and append-only freeze. Do not start the 42 attempts. Sol will verify readiness and stop at READY_TO_START so the user can authorize execution and reopen the existing progress monitor.
