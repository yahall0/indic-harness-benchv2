# Nemotron timeout repair and hold — 2026-10-01

**Initial watch completed, 16:13 UTC; evaluation continues.** The seven repaired benchmark attempts covering the queued Hinglish recovery and two complete new language triplets all finished with no new INFRA, unknown usage, integrity violations, or cleanup failures. Meeting-summary scores were English 1.0 / Hindi 1.0 / Hinglish 0.8889; email triage scored 1.0 in all three languages. The Hinglish summary's sole missed check was the original oracle keyword `action`; no grader or translation was changed. The seven attempts used 38 transmissions and 265,568 input / 14,385 output tokens across their independent original per-attempt budgets. These counts exclude the separate language probe. Evidence is campaign `checks/initial-watch/restart-watch-verification.json`. The original failed first-task records remain intact, and baseline/old-result preservation passed again. The read-only browser monitor and five-minute heartbeat remain active while the controller advances. This establishes working transport on these observed attempts, not a general performance or language-effect conclusion.

**Update, 16:00 UTC: the final language gate passed and the authorized benchmark resumed.** The earlier paragraphs below record the failed candidate and hold. Current evidence is `revisions/transport-v2/probes/hindi-hinglish-final/report.json`, `checks/readiness.json`, and the actual campaign journals. The final provider timeout matches the original whole-attempt deadline, at most 600 seconds; remaining CLI/run time still caps each request. All original token, response, transmission and task limits remain unchanged.

The final gate used exactly its separately authorized maximum of 6 transmissions: both Hindi and Hinglish completed read/write/receipt validation, with 36,635 input / 911 output tokens, zero unknown-usage calls, and all owned resources removed. No generic-failure key rotation occurred. Thirteen unit tests and the contained fake/accounting suite passed against these exact sources, including a 130-second Hindi response through actual OpenClaw. All 16 readiness checks passed. The append-only v2 runtime freeze is `30ae3dfeb3de6a789fdfeea4130ae2abe232b161b52b6d1e00b67bf193584bd6`; the v1 freeze and prior failed gate are preserved.

The renewed user instruction authorized resume after repair. Controller PID 26656 started at 15:59 UTC and cleared only this chat's repair hold under exclusive global and campaign leases. It retains the same study and exact 46-task/138-condition plan, skips terminal outcomes, uses only the already scheduled first-task Hinglish recovery, and will not create a third Hindi attempt. Initial benchmark observation is ongoing. Five-minute follow-up monitoring is read-only and cannot start inference or restart the controller. The browser monitor is timestamped and distinguishes saved primary failures from new work. Immediately before resume, preservation checks confirmed the 166 pre-repair terminal records and 3,661 protected artifacts unchanged, including the completed GPT-OSS PDF. No conclusion about intrinsic language incompatibility follows from the earlier timeout failures.

The benchmark is **held**, with no new benchmark attempts admitted during this repair. The final repair candidate passes local/contained checks but has not passed a live check after the last OpenClaw timeout change. Do not launch from the historical READY document or bypass the current gates.

## Evidence and diagnosis

The first task's English primary completed with score 1.0. Hindi's primary and its sole infrastructure recovery failed after valid read-tool responses; Hinglish's primary failed before any response. All outcomes, conservative unknown-use charges and artifacts remain saved. The first-task Hindi condition has no third automatic attempt. The previously scheduled Hinglish recovery remains unstarted. The main journal still has 3 terminal primaries and 135 planned conditions.

A separately recorded diagnostic produced a valid Hindi continuation in 129 seconds, exceeding the old relay's 120-second deadline. Its streaming counterpart completed in 4.629 seconds. One pair establishes neither general latency nor language ability.

The first repair uses bounded upstream streaming, assembles complete tool/content/reasoning fragments, checks authoritative usage and identity, and settles before delivering generated content. Initial/idle socket timeout is 180 seconds. Failed requests now retain a bounded request trace. Original task, token, transmission and whole-attempt limits remain unchanged.

The live receipt canary then exposed OpenClaw's independent 120-second first-event/idle watchdog. Hindi returned a valid read-tool call in 115.4 seconds; the continuation hit that watchdog and the canary ended at its 240-second round limit. Only **2 physical cloud transmissions** were made. Hinglish was not tested in that gate. Known usage is **6,029 input / 74 output** tokens; one killed continuation has unknown usage and retains its full reservation. Aggregate conservative charges are **33,365 input / 4,170 output**. No keys rotated. The original failure report/result remains intact; `accounting-reconciliation.json` records the later unknown-use settlement.

The final candidate explicitly sets `models.providers.ihb.timeoutSeconds` to 210, capped by the existing attempt limit. The installed OpenClaw 2026.9.7 source and [official timeout documentation](https://docs.openclaw.ai/agent-loop) support this setting. CLI/run deadlines still cap it. No OpenClaw package, submitted tool, hook, oracle, prompt, fixture, or containment rule changed.

## Verification and stop decision

- 11 repair unit tests passed.
- Hardened Docker/OpenClaw fake-inference checks passed for English, Hindi and two-round Hinglish, Unicode/tool fragments, truncation, context, accounting and cleanup.
- A **130-second simulated Hindi tool response** completed through the actual OpenClaw process after the explicit provider-timeout fix. This incurred zero Ollama calls.
- Generic rate limits stay on the same key; confirmed quota exhaustion rotates sequentially; lost local accounting acknowledgments settle idempotently. These contained checks passed.
- The final candidate remains blocked by its failed/stale live gate. No additional cloud probes or benchmark attempts were started after that failure, honoring the request to conserve usage.

This is evidence of timeout incompatibility and unreliable latency in the attempted configuration. It does **not** establish that Nemotron intrinsically cannot understand Hindi or Hinglish. Do not label these infrastructure failures language-performance zeros or force any language-degradation conclusion.

## Preservation and restart boundary

The 166 terminal records and 3,661 existing run artifacts checked against the pre-repair ledger matched. The GPT-OSS journal, completed PDF, original 46-task selection, all baseline frozen files, Nemotron v1 freeze/configuration/evidence and old Nemotron outcomes remain unchanged. The repair is isolated under `nextbench_repair` and `campaigns/nemotron-3-super-20261001/revisions/transport-v2`; it is not frozen for benchmark use.

The read-only monitor uses a compact view, clears both screen and scrollback each refresh, and displays **CAMPAIGN ON HOLD**. Closing it cannot launch or stop inference.

Before any future restart, inspect `results/repair_status.json`, the actual journals/locks, and `revisions/transport-v2/checks/readiness.json`. Preserve the failed probe and its costs. A further current-candidate live check needs its own append-only evidence and explicit bounded allowance; the existing fixed probe path refuses replay. Do not overwrite the failed gate, refreeze v1, erase infrastructure failures, replay completed primaries, create a third Hindi attempt, or bypass containment. Current user authorization to resume does not override failed readiness gates.
