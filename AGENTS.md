# Indic Harness Bench: staged implementation instructions

The original 40-task campaign is complete. The user authorized execution of the 14 additional matched tasks on 2026-10-01, under exactly the same protocol. All readiness gates passed and the append-only extension is frozen at runtime revision 6. Preserve and skip all 120 original terminal results. Before any restart, check the process record and exclusive controller lock; never launch a second campaign or automatically replay an already-started condition. The user subsequently explicitly authorized one infrastructure recovery for task 037 in Hindi. That separate attempt completed with score 0 and the same controller resumed the remaining planned conditions. Both primary and recovery records are retained; see `results/infrastructure_retries.json`. Do not retry agent outcomes or create further recoveries without an explicit user request.

## Reference protection and execution boundary

- The adjacent `../harness-bench` directory and its paper are reference only. Never modify it, run its CLI, or import task modules on Windows/ordinary WSL.
- The copied reference under `vendor/harnessbench` is a preserved source snapshot. Do not alter it. Infrastructure adaptations belong in new runtime code.
- Use no files or results from the earlier Indic attempt.
- Only the trusted `bench` controller and static checks run on Windows. Agent tools, submitted code, hooks, and graders run in restricted Docker containers after full integration and isolation validation.
- No host bind mounts, host networks, Docker socket/named pipe, devices, or real credentials in agent containers. Do not weaken controls to make a task pass.
- Never use global Docker pruning or recursively delete/move host paths.
- No sub-agents or other-chat delegation were requested. Work in this chat.

## Study scope and current state

All 120 original attempts and their artifacts must remain unchanged, including four infrastructure failures. Fourteen offline additions yield 54 original tasks and 162 conditions; 42 additional attempts are awaiting execution after the append-only freeze. Original task/prompt/review hashes, protocol settings and result records are backed up in `provenance/initial-40` and checked by `python -m bench.extension`. Use the same GPT-OSS-20B/OpenClaw settings, budgets, grading, language order rotation, credential policy and analysis for all tasks. The additions were selected after the original campaign, before their own model outcomes; disclose this dataset expansion. Do not select or exclude tasks based on model scores. Fifty complete matched triplets are possible if no new infrastructure failures occur; they are not guaranteed.

The secure runner, relay, helpers, isolated grader, accounting and safe exports are integrated. All 54 original oracles have positive and negative validation evidence; the expanded private grader also passed compatibility validation for the original 40 without changing their old reports. Never weaken containment. The translation and preparation stop boundaries were completed before the user authorized this launch. Keep the same study ID so completed attempts are skipped. Pause on quota exhaustion; never buy credits automatically. Translations receive AI self-review, not independent human review. Do not claim statistical significance or broad Indian-language performance from this exploratory study.
