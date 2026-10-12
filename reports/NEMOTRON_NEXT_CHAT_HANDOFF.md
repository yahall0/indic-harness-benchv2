# Next-chat handoff: Nemotron experiment

**Latest verified state, 2026-10-02 04:15 IST: MAIN_AND_USER_REQUESTED_RECOVERIES_COMPLETE.** All 138 primaries are terminal (113 completed, 20 budget exhausted, 5 INFRA). Three automatic recoveries are scored; first-task Hindi and canary-release-check English remained INFRA after their sole original recovery. The user explicitly requested another INFRA-only recovery and saving it in the same run. One additional fresh attempt for each is saved under the same campaign/study in `results/additional-recoveries/20261002`: Hindi completed with score 0; canary English completed with score 0.06. Both have zero new unknown usage and all owned resources removed. The final `user_requested_resolved_*` exports count exactly 46 scored task triplets / 138 conditions and disclose the extra-recovery policy. Original primary/original recovery-inclusive views remain untouched; do not pass the new attempts off as primaries. All original journal tables/artifacts/PDF and frozen source/configuration were verified unchanged. Additional usage is 10 transmissions / 71,746 input / 13,670 output, included in `accounting_including_additional_recoveries.json`; old unknown reservations remain retained. Both controllers have exited. The existing browser scoreboard shows resolved rows plus original failures/retry history. Five-minute chat monitoring is paused at the user's request. No further attempt is authorized or queued. See campaign `results/additional-recoveries/20261002/COMPLETION.md` and `verification.json`. Earlier running/watch/READY paragraphs below are historical.

**Latest verified state, 2026-10-01 16:13 UTC: INITIAL_WATCH_COMPLETE; benchmark continues.** The first three task groups resolved. Seven attempts under transport v2 completed without new infrastructure errors, missing usage, integrity problems, or leftover owned resources: the queued first-task Hinglish recovery scored 1.0; meeting summary scored English 1.0 / Hindi 1.0 / Hinglish 0.8889 (only `phrase_action` missed); email triage scored 1.0 in all three languages. They used 38 physical benchmark transmissions, 265,568 input / 14,385 output tokens in total; the separate six-call live gate remains excluded from benchmark scores and accounting. See campaign `checks/initial-watch/restart-watch-verification.json`. Original first-task Hindi primary/recovery INFRA and Hinglish primary INFRA remain saved; no third Hindi attempt was created. Full old-record/artifact/PDF preservation passed again after these attempts. The controller is continuing into later tasks, with the live read-only browser monitor open and five-minute heartbeat active. `results/away_monitor_state.json` records the already-reported milestone to avoid repeat alerts. Verify live journals/process identity for later state; monitoring must never start or replay inference.

**Latest verified state, 2026-10-01 16:00 UTC: RUNNING_TRANSPORT_V2.** The user renewed authorization to fix, resume, and monitor while away. The final, separately capped live gate passed Hindi and Hinglish (read, write, receipt validation): 6 transmissions, 36,635 input / 911 output tokens, no unknown usage, and all owned containers removed. Thirteen repair unit tests and contained integration/accounting checks passed, including a 130-second simulated Hindi response. Transport v2 is frozen at `30ae3dfeb3de6a789fdfeea4130ae2abe232b161b52b6d1e00b67bf193584bd6`. It streams upstream responses and sets the OpenClaw provider timeout to the original whole-attempt limit (maximum 600 seconds), retaining the original task/token budgets and containment. The main campaign study ID is unchanged. Controller PID 26656 was verified alive; logs are `campaigns/nemotron-3-super-20261001/results/logs/20261001-155935-streaming-fa7bbc06`. It cleared only the recorded repair admission hold under both controller leases and will run the already scheduled Hinglish recovery, then unstarted conditions. Never create a third first-task Hindi attempt or overwrite any old result. Verify actual process/journal state before acting: PID and this paragraph will become historical. A read-only browser monitor is open at the URL in campaign `results/browser_monitor.json`, with live timestamps and separate recovery rows; a five-minute heartbeat watches for material changes without starting inference. First-three-triplet observation is in progress, not yet complete. Baseline/old terminal records and 3,661 protected artifacts were verified unchanged immediately before resume.

Verified 2026-10-01. This document transfers context; writing it made no inference calls and changed no benchmark results or frozen settings.

**Latest state, 2026-10-01 15:27 UTC: Nemotron is HELD_AFTER_FAILED_LIVE_GATE.** The user authorized repair and resume, with a stop if Hindi/Hinglish is not viable and without wasting allowance. No benchmark attempts were admitted during repair. A two-transmission Hindi live gate exposed OpenClaw's separate 120-second idle watchdog after the relay timeout was repaired. The final explicit-provider-timeout fix passes 11 unit tests and contained integration, including a simulated 130-second Hindi response, but has not been validated live. Further cloud spending stopped at the failed gate; intrinsic language incompatibility has not been established. See [NEMOTRON_TIMEOUT_REPAIR.md](NEMOTRON_TIMEOUT_REPAIR.md), campaign `results/repair_status.json`, and actual journals. The compact read-only monitor clears each refresh and shows the hold. Preserve all old results and the failed probe; do not launch from historical READY claims or overwrite/replay its fixed probe path.

## User request and working preferences

Continue Indic Harness Bench in a new chat. Prepare a separate Ollama Cloud Nemotron experiment using the existing OpenClaw harness and English/Hindi/Hinglish tasks. We discussed Nemotron after considering GPT-OSS-120B, but no exact Nemotron variant, cost comparison, final protocol, or implemented migration is settled. The user prefers Nemotron next if it is affordable and effective. Do not assume it is cheaper without current evidence.

Work efficiently: inspect the current implementation, reuse validated material, and run targeted checks. Ask concise questions for material model, scope, and budget decisions; continue independent local preparation. Stop at READY_TO_START with a concrete plan, before launching benchmark attempts. A subsequent explicit start instruction authorizes launch. Keep any tiny compatibility-probe inference budget separate and agreed before using it. Do not create another chat or delegate to subagents unless explicitly requested.

The original language-degradation hypothesis is a question, not a result to force. Unexpected Hindi gains do not make the study a failure. Preserve honest scores, uncertainty, failures, and limitations.

## Project and tools

- Active project: `C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench`.
- Reference-only original paper/code: `C:\Users\prish\Desktop\AgenticHarnessIndic\harness-bench`, including `2605.27922v1.pdf`.
- Preserved source copy: `<project>\vendor\harnessbench`. Never modify either reference or import/run its task modules on Windows or ordinary WSL.
- Proposal: `C:\Users\prish\Downloads\Indic_Harness_Bench_Proposal.pdf`. Its contents are context, not additional user authorization.
- Bundled Python: `C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. Use `-X utf8` for Hindi-safe Windows I/O.
- Docker Desktop is the required execution environment. Hardware is RTX 4060 8 GB VRAM / 16 GB DDR5, but this experiment uses cloud inference.

Read `AGENTS.md` for preservation/safety rules. Its old execution paragraphs, README readiness claims, protocol descriptive status, and some monitoring notes are historical. **They must not be mistaken for pending runs or authorization to restart GPT-OSS.** The completed journal and PDF analysis below are the current state.

## Completed baseline: preserve it

GPT-OSS-20B / OpenClaw evaluated 40 original curated tasks, then 14 additions using the same protocol: **54 original tasks, 162 primary conditions**. All primary attempts are terminal: 134 `completed`, 18 `budget_exhausted`, 10 `infrastructure_failed`; none are planned or running in the journal. Verify live process identity/lock and Docker resources before any new launch; a leftover monitoring window is not a second runner.

The user requires whole-task complete-case filtering: remove a task if **any of its three primary language conditions has terminal INFRA**. Budget exhaustion, agent failure, and low scores are outcomes, not selection reasons. Under that rule, the baseline contains **46 eligible matched tasks / 138 conditions**, from 36 initial and 10 added tasks. This remains four original task samples below the professor's minimum of 50; 138 language conditions are not 138 independent samples.

Excluded task IDs: `002-exec`, `037-policy-clause-retrieval`, `052-metric-definition-audit`, `055-funnel-dropoff-analysis`, `066-rollback-readiness`, `070-hr-resume-screening`, `072-logistics-delay-response`, `103-policy-update-replan-diff`.

Task 037 Hindi had one explicitly user-authorized infrastructure recovery, separately saved, which completed with score 0. Keep both records. The PDF does **not** substitute that retry into the primary analysis, so task 037 remains excluded. No further retries of baseline conditions are authorized. An earlier 100,000-input budget campaign was explicitly discarded and archived; neither it nor the older Indic attempt is evidence for the current study.

Eligible mean oracle scores / 100: English **39.64**, Hindi **47.42**, Hinglish **35.39**. Strict full completions: 5, 4, and 4 of 46. English-minus-Hindi score difference: **-7.78 pp**, paired 95% bootstrap interval **[-18.68, +2.72]**. English-minus-Hinglish: **+4.25 pp**, interval **[-5.94, +14.48]**. Both include zero. There are 17 budget-exhausted included conditions, mostly conservative input preflight stops. Many failures omitted required artifacts. Do not present causal tokenizer, broad Indian-language, or statistically established language effects.

## File map

Dataset:
- `dataset/task_manifest.json`: audited source task metadata, inclusion/deferral decisions, protected literals, language paths and validation status.
- `dataset/task_inventory.csv`; `dataset/pilot_plan.json`: inventory and fixed ordered 54-task plan with rotating language order.
- `dataset/extension_selection.json`: initial 40 and added 14 IDs, selection provenance.
- `tasks/<task-id>/prompts/en`, `hi`, `hinglish`: completed prompts, including all rounds. There are 61 instruction turns / 183 prompt files for the full 54. No retranslation is needed.
- `dataset/translation_reviews.json`, `reports/oracle_validation.json`, `reports/oracles/`, `reports/extension_original_oracle_compatibility.json`: AI translation/review and positive/negative oracle evidence. Review is not independent human validation. Ground truth and validation solutions stay inaccessible to evaluated agents.

Frozen provenance and settings:
- `dataset/freeze.json`, `config/protocol.json`, `config/images.json`.
- `provenance/initial-40/`: immutable original metadata, hashes, settings and results backup. All 120 original records are preserved.
- Old study ID: `be79c2f6c171dbe17a7c517df8fba4996844029a2be4cfd92b47db77ef0ee036`.
- Final baseline runtime freeze: `9808c0237cde9a9416a203c169ebc07d7994a237c875c1938ca9e83573fd7708`.
- 1,116 reference files verified unchanged. Baseline runtime infrastructure changed during the campaign; the PDF discloses four implementation fingerprints. The Nemotron campaign should freeze a uniform implementation before its evaluation.

Results/report:
- `results/journal.sqlite3`: authoritative durable run/credential/accounting journal.
- `results/runs/<run-id>/`: prompts, outputs, inference traces, workspace snapshots, artifacts and final outcomes.
- `results/exports/`: existing CSV/JSONL metrics and analysis; these exports may use older filter behavior, so do not assume they are the PDF's strict complete-case population.
- `results/checkpoints/`, `results/controller_process.json`, `results/monitor_process.json`: backups and process records.
- `results/infrastructure_retries.json`, `results/infrastructure-retries/`: separate recovery provenance/data.
- `pdf/Indic_Harness_Bench_Experiment_Report.pdf`: finished, visually checked 15-page report with nine figures and a task-score atlas.
- `pdf/report_data/analysis_summary.json`, `included_condition_metrics.csv`, `included_task_scores.csv`, `excluded_task_ledger.csv`, `report_validation.json`: exact filtered report data and QA.
- `pdf/figures/`: PNG/SVG exports. `scripts/build_experiment_report.py` rebuilds the **baseline** report; do not overwrite it with Nemotron results.

Runner/code:
- `bench/controller.py`, `bench/durable.py`, `bench/lease.py`: serial execution, transactional persistence, exclusive controller lock.
- `bench/security.py`, `bench/containers.py`, `bench/task_services.py`: containment, safe artifacts, offline helper services/hooks.
- `runtime/agent.py`, `runtime/relay.py`, `runtime/grader.py`, `runtime/mock_api.py`: container programs.
- `bench/openclaw_config.py`, `bench/collector.py`, `bench/rotation.py`: model config, external accounting, credential/error handling.
- `bench/readiness.py`, `bench/fingerprint.py`, `bench/*_check.py`, `tests/`: gates and integration checks.
- `docs/RUNNING_AND_RECOVERY.md`, `reports/FRESH_RUN.md`, `reports/RELAY_REPAIR.md`, `reports/accounting_retry_repair.json`, `reports/additional14_infrastructure_review.json`: methods, repairs and failure evidence.
- `scripts/watch_progress.py`, `scripts/watch_progress.ps1`: read-only monitor. `scripts/emergency_stop.py`: existing baseline-owned-resource stop. Adapt monitoring and emergency stop to the **new** campaign's journal; current paths are fixed to the baseline.

## Existing protocol: comparison anchor, not an assumed Nemotron capability

- Model `gpt-oss:20b`, harness OpenClaw **2026.9.7**; one primary attempt per task/language, no model fallback.
- Endpoint `https://ollama.com/v1/chat/completions`; temperature 0, reasoning effort medium.
- Declared OpenClaw context **65,536**; per-response allowance **4,096**. Actual provider context capacity was not independently established. Context capacity is separate from cumulative input budget.
- Per attempt: **200,000 cumulative conservative input allowance**, **16,000 cumulative output tokens**, **30 physical inference transmissions**, including retries. Input preflight uses UTF-8 bytes plus framing; it can stop before actual reported tokens reach 200,000. Reserve output allowance before forwarding and reconcile measured usage after settlement.
- Wall time `min(original task timeout, 600 seconds)` across all rounds; upstream transport timeout 120 seconds; maximum two transient retries.
- Keep state between rounds of one attempt; fresh state between languages; serial execution and rotating language order. English fixtures, schemas, commands and output contracts are held fixed; user instruction language changes.
- Deterministic original oracle scores are primary; integrity checks separate. Strict full completion requires `completed`, score >= 0.9999, every exposed check passing, and no integrity violation. Preserve fractional original scores even when all exposed checks pass. No paid LLM judge was used.

## Critical safety and persistence

The user previously lost substantial SSD data to a rogue agent. **The entire OpenClaw process must stay in Docker**, not merely its built-in tool sandbox. No direct Windows/ordinary-WSL agent commands or graders.

Agent: non-root, read-only root, dropped capabilities, no-new-privileges, default seccomp, private namespaces, no host folders/drives/bind mounts, Docker socket/named pipe, devices or host networking. Default limits: 2 CPUs, 3 GiB RAM, 256 processes, 512 MiB tmpfs workspace; private temporary/state storage. Restricted network reaches only local task services and inference relay. The relay holds cloud credentials; agent never sees them. No elevated execution, external nodes, messaging, updates, or unnecessary plugins. Stop agent processes before grading in a separate restricted no-network/no-credential container. Oracles and solutions remain protected. Reject unsafe/oversized exports. Cleanup only recorded, ownership-verified benchmark resource IDs; no global Docker prune or recursive host-drive cleanup. If containment fails, stop; no unsafe fallback.

Persist reservations before inference, settle idempotently, and store bounded traces/results outside agent storage. Keep SQLite WAL/synchronous FULL, round checkpoints and online backups, plus atomic CSV/JSONL updates after each attempt. A new campaign must resume only unstarted conditions and preserve every started outcome. Never retry an agent failure for a better score. Explicitly requested infrastructure recoveries remain append-only, individually accounted for.

One controller at a time; inspect process records and exclusive lock before launch. Monitoring is a separate read-only process; closing it does not stop inference. Prefer a visible progress/score terminal when the user later authorizes launch, with durable background logs and a campaign-correct emergency stop. Confirm healthy progress initially; continuous chat monitoring is not required.

## Credentials and error policy

Four local slots are configured in Windows DPAPI-encrypted `config/credentials.dpapi.json`. `bench/credentials.py` securely loads them; `scripts/configure_keys.py` is the interactive configuration entry point. Environment alternatives are `INDIC_OLLAMA_KEY_1` through `_4`. Never print keys, decrypt them into chat/logs, or put them into prompts/agent containers. Do not ask the user to paste secrets here. Existing checks are historical; verify actual eligibility for the chosen model before use.

The user wants graceful sequential cycling only on **confirmed allowance exhaustion**, never generic HTTP 429, transient HTTP 500, timeout, slow inference, or low score. Keep exhausted-slot state across restarts. Free quota independence is not established merely by having four keys; respect current provider account/usage rules. No credit purchases. Baseline forwarding records actually used slot-1 throughout; there is no evidence that the others were consumed by this campaign, but do not infer their present quota balance.

Current provider failure policy: at most two transient retries; a settled exhausted provider failure ends the condition as INFRA, saves/cleans up, waits 30 seconds, and proceeds to an unstarted condition. Three consecutive recoverable provider failures pause the session to avoid an outage cascade. Authentication, accounting, integrity, unknown failures or unsafe cleanup pause immediately. Ambiguous transports retain the full reservation and must not be replayed or trigger key rotation. Broken-pipe delivery and local acknowledgment issues have distinct stage diagnostics. Preserve these repairs and prove them with targeted tests.

## Nemotron preparation tasks and unresolved decisions

1. Inspect the actual journal, process lock and runner. Make a consistent baseline backup and verify reference/result hashes. Do not use the old GPT-OSS `start` command to create the new run.
2. Create an isolated **new campaign/study ID**, protocol, freeze, journal, accounting, outputs, logs, monitor and recovery namespace. Many modules hard-code the baseline project root, so campaign separation must be implemented or use a safely isolated new runner checkout. Preserve old prompts, fixtures, oracles, frozen code/settings and results. Do not overwrite/refreeze the GPT-OSS study or mix model rows in its exports.
3. Verify current official Ollama/NVIDIA model tags, free availability, supported context, tool calling, thinking controls, usage fields and limits. User previously listed `nemotron-3-nano:30b`, `nemotron-3-super`, and `nemotron-3-ultra`; availability/relative cost is not a verified present fact. Choose a model based on affordability and useful agent ability, not marketing size alone. If per-model free usage rates are undisclosed, state that rather than inventing prices.
4. Audit the complete OpenClaw-to-relay contract before model use: tool schemas/calls/results, content vs reasoning, Unicode, finish reasons, reported model aliases, non-streaming-to-SSE normalization, truncation and token accounting. **Current relay hard-codes `reasoning_effort='medium'`; OpenClaw declares reasoning enabled and 65,536 context. `bench/check_keys.py` hard-codes GPT-OSS and reasoning effort none.** These cannot be assumed valid Nemotron settings. Adapt supported fields and identity validation deliberately, with no silent model fallback or false success.
5. Use fake-inference/local checks first. Then, after agreement on a small recorded probe budget, test benign English/Hindi/Hinglish tool use, tool results, reasoning/truncation, context behavior and one multi-round workflow through the actual secure harness. Keep smoke tests outside benchmark evidence. Never import task oracles or execute submissions on the host.
6. Before looking at Nemotron task outcomes, settle full 54-task scope vs a pre-specified subset, exact model, supported thinking mode, response/context settings, fixed budgets, retry policy, sample target and free-usage stop rules. Prefer identical prompts/oracles and comparable budgets where technically supported; document any change. Do not silently carry a GPT-OSS-specific reasoning setting to another model. A future cross-model paired comparison uses only original tasks with valid complete triplets in **both** campaigns; exclude whole tasks consistently and display attrition. Keep standalone model analyses separate.
7. Freeze images/configuration/data/implementation and record preregistered analysis. Collect original scores/checks, completion, elapsed/inference latency, usage and uncertainty, prompt inflation, tool calls/errors, retries, budgets/timeouts, integrity events and artifacts; mark unavailable measurements explicitly. Use original-task paired bootstrap intervals, not language conditions as independent samples. Preserve unsuccessful agent outcomes.
8. Check security, durable resume, exact admission counts, duplicate-run rejection, rotation/error recovery, monitor and emergency stop against the new journal. Stop at READY_TO_START, explain the exact run and expected compute exposure, and wait for the user's start instruction.

If new translations become necessary, stop before translation so the user can switch the chat model to GPT-6 Luna. Provide precise translation/review instructions and a stopping point for switching back to GPT-6.1 Sol. Existing 54 triplets are already translated and validated, so that work should normally be reused.

## Subsequent user instructions and preparation, 2026-10-01

The user has now specified that future model benchmarks must use exactly the tasks
included in the completed report: **46 original tasks / 138 primary conditions**, not
all 54 attempted tasks. `campaigns/shared/report_matched_scope.json` pins the exact
selected task/condition IDs, original language order, and source/shared-input hashes.
This resolves the earlier full-54-versus-subset decision for future campaigns.

The user also requested at least one infrastructure retry and continuation after an
isolated infrastructure error. `campaigns/shared/FUTURE_BENCHMARK_POLICY.md` records
the bounded policy: one separately accounted fresh recovery after proved recoverable
INFRA, cooldown, continuation even after that recovery fails, and persistent safeguards
for unsafe accounting/cleanup/authentication and sustained provider outages. Baseline
results and its primary-only PDF remain unchanged. Do not retry baseline conditions.

The user then authorized all recommended choices while using Codex remotely on their
phone. The model is `nemotron-3-super`; thinking is explicitly on, using the documented
OpenAI compatibility alias `high` for boolean true, not a claimed named high effort.
Keep the baseline 65,536 declared context, response cap 4,096 and all per-attempt caps.
Use recovery-inclusive outcomes for the main future analysis and primary-only as a
required parallel sensitivity/comparison. Never select the better score. Preserve all
attempts and combined costs, including budget-exhausted outcomes and zero scores.

The authorized separate probe cap is 12 physical transmissions / 200,000 conservative
input / 16,384 output tokens. Existing free credits only; never purchase credits.
`nextbench/` now contains separate attempt, relay contract, runner, analysis, monitor
and emergency-stop code. Read the campaign's `checks/readiness.json` and probe journal
for actual preparation state; historical prose is not proof of readiness. Frozen
baseline code/data/results are reused without alteration. No benchmark launch is
authorized by the preparation instruction. Stop at READY_TO_START and await start.

## Final preparation state, 2026-10-01

The separate campaign `campaigns/nemotron-3-super-20261001` is **READY_TO_START**.
Read `READY_TO_START.md` in that directory for the complete launch brief. All 22 current
readiness gates pass; 25 static tests, contained fake harness, relay accounting and the
original-fixture production integration checks pass. The separately authorized live
compatibility suite passed with 10 physical transmissions, 55,946 input and 1,450 output
tokens. Do not replay that fixed probe suite or count probes as benchmark results.

New study/runtime ID:
`9dae480295addab8da59fdc15e41b91896e7eb03d983e754f7229fd402c142d7`.
The new main journal has 138 planned conditions, zero started conditions, zero forwards
and zero recoveries. No controller is running and no benchmark-owned Docker test
resources remain. Baseline preservation verification covers all seven journal tables,
291 frozen files, 1,116 reference files, all 162 primary records, the original 120 saved
records/accounting/artifacts, the PDF fingerprint and a 3,622-output-file hash ledger.

Do not edit frozen campaign source/configuration/evidence or refreeze it routinely.
Use `python -m nextbench.runner ready campaigns/nemotron-3-super-20261001` to verify current
gates. Only after explicit launch authorization, use `nextbench/launch.ps1
-LaunchAuthorized`: it starts the separate serial controller under exclusive locks with
durable logs and a visible read-only monitor. `nextbench.stop` targets this campaign's
recorded ownership-verified resources. Never launch the baseline controller.

Current official pricing and credit-bucket limitations are documented in the brief.
No purchases or billing/account changes are authorized, no full free-credit balance is
known, and four slots do not establish independent quotas. Managed cloud weights can
change; metadata is rechecked before launch and every reported model identity is checked.
The campaign remains stopped pending the user's start instruction.
