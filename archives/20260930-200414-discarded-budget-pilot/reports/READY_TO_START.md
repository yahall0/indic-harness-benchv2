# Ready to start: Indic Harness Bench

Preparation is complete. All readiness gates passed; the dataset and implementation are frozen. **No benchmark runs have started.** Four configured credential slots passed the earlier small live probes; those probes are separate from research results. This final preparation stage made no cloud inference calls.

Project: C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench.

All 1,116 recorded reference files remain unchanged. All 106 original tasks have decisions: 40 validated matched triplets, 2 excluded image tasks and 64 deferred tasks. The set has five tasks from each of eight families, favouring local workflows with few dependencies. Task 025 was replaced by 027 because its original oracle contract was unsatisfiable, before observing outcomes.

## What will run

- **40 tasks × English/Hindi/Hinglish × one attempt = 120 planned runs**, serially, subject to available provider allowances. There are 46 distinct instruction rounds and 138 prompt files.
- OpenClaw 2026.9.7 with Ollama Cloud gpt-oss:20b, temperature 0 and medium reasoning. Required prose outputs remain English across conditions; this measures instruction-language differences.
- Follow the frozen manifest task order. Rotate language order: English/Hindi/Hinglish, then Hindi/Hinglish/English, then Hinglish/English/Hindi, repeating. Fresh state between languages; state preserved between rounds of one attempt.
- Original timeout capped at 600 seconds for all rounds together, at most 30 physical inference requests, 100,000 cumulative input tokens and 16,000 cumulative output tokens. Maximum response allowance is 4,096 tokens per request. Conservative preflight reservations can stop requests before the nominal token cap.
- Stop agent processes before original deterministic oracle grading in a separate offline container. Report added integrity checks separately. No paid LLM grading.
- Collect scores, completion, elapsed/inference time, available tokens, requests, tool calls, retries, slot transitions, failures, traces and bounded artifacts. Unavailable tool/schema-error and compaction counts remain explicitly null.
- Export English-minus-Hindi and English-minus-Hinglish completion differences in percentage points, paired score differences, category breakdowns and task-resampled bootstrap intervals. Show incomplete triplets and infrastructure failures separately.

If every attempt reaches the 10-minute cap, attempt time alone can approach 20 hours, plus setup and grading. Completion within free credits is not guaranteed.

## Keys and quotas

Your four keys are already configured in the encrypted DPAPI store; no further entry is needed. Only the restricted inference relay receives credentials. The evaluated agent receives a temporary attempt token.

The controller keeps its current eligible slot, including across a triplet where possible. It advances only after an explicit provider quota/usage exhaustion response. Generic rate limits and transient failures receive at most two transport retries on the same slot. Authentication failures, ambiguous errors and accounting failures pause instead of speculative cycling. Agent failures are recorded without retries to improve scores.

Exhausted slots persist across restarts. Exhaustion of all slots pauses inference and retains progress, with no purchases. Different keys can share allowances; actual provider responses govern availability. Reactivate only after an actual provider allowance reset with the explicit reset command in RUNNING_AND_RECOVERY.md.

## Containment and saved progress

The entire OpenClaw process runs inside Docker: non-root, read-only roots, no host-drive binds or Docker control interfaces, dropped capabilities, no-new-privileges and seccomp. Each attempt has private tmpfs state, a 512 MiB workspace, 2 CPUs, 3 GiB memory and a 256-process cap. Egress is limited to isolated task services and the inference relay. Graders have no network or credentials.

Containment, malicious export, resource exhaustion, multi-round and save/reopen checks passed. Docker substantially reduces the disk-loss risk but cannot guarantee protection against kernel/container vulnerabilities.

The results/journal.sqlite3 database uses WAL and synchronous FULL commits. Each physical inference forwarding is durably reserved first. Per-round checkpoints and per-attempt outcomes are saved outside agent storage. Completed results survive controller/container failure. On restart, an unfinished started attempt is recorded as interrupted; already-started conditions are not silently rerun. Remaining planned conditions can continue.

Project result locations:

- results/runs/<run_id>/: prompts, round outputs, inference traces, workspace snapshots, artifacts and outcomes.
- results/checkpoints/latest/: JSON/JSONL exports and a consistent SQLite backup.
- results/exports/: metrics.csv, metrics.jsonl and analysis.json.

A crash can lose the current round's unsaved tmpfs changes; committed outcomes and checkpoints remain. Protection against disk/laptop loss requires a backup on separate storage.

## Launch and emergency stop

Keep Docker Desktop running and the laptop awake. **The commands below have not been executed.** When ready, launch from PowerShell:

    $IhbPython = 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    Set-Location -LiteralPath 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench'
    & $IhbPython -X utf8 -m bench ready
    & $IhbPython -X utf8 -m bench start

Start checks all gates again before forwarding inference. Changed frozen files or missing runtime evidence block execution.

Emergency stop from another PowerShell terminal:

    & 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\scripts\emergency_stop.py'

This stops recorded benchmark-owned resources only. It performs no global pruning or recursive host-drive cleanup.

After a process failure, use the same start command to continue remaining planned conditions. Interrupted/failed conditions stay visible. From the project directory, take a consistent online backup and refresh metric exports with:

    & $IhbPython -X utf8 -m bench backup

Copy that backup to separate storage for disk-loss protection.

## Limitations and evidence

Translation and semantic review were performed by AI, including Luna revisions and final contract corrections, without independent human validation. Original graders can be permissive; constructed positive/negative cases cannot prove exhaustive correctness. Fixtures and required prose outputs stay English. Conservative reservations can differ by script. This one-model, one-harness, 40-task, one-attempt study is exploratory and cannot isolate tokenizer effects causally, guarantee significance or establish broad Indian-language conclusions.

The review package contains task_inventory.csv and task_manifest.json for all 106 decisions; oracle_validation.json and oracles/ for grading evidence; translation_check.json, translation_reviews.json and final_contract_check.json for translation evidence; security/runtime/relay/helper/controller reports for containment and recovery evidence; readiness.json for passed gates; and freeze.json for final hashes. Methods are in methods_ready.md.

Older handoff/checkpoint files describe historical stages. The descriptive pilot_status field in protocol.json is historical; current launch gates use readiness.json and freeze.json. Do not edit frozen settings before launch.

Frozen dataset SHA-256: 6498cce290def2038c1da1fe958cae8babdb0ef24e7784bd2f66512d4c641c22.
