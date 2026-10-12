# Report-matched scope and infrastructure recovery

This policy applies only to separate future model campaigns. It does not authorize
launch, change the completed GPT-OSS experiment, or authorize more GPT-OSS retries.
It supersedes the earlier unresolved 54-task/subset decision for future campaigns.

## Fixed scope

Use exactly the 46 original task IDs in `report_matched_scope.json`, each in English,
Hindi and Hinglish: 138 primary conditions and 156 prompt files / 52 instruction turns.
The selection comes from `pdf/report_data/included_task_scores.csv`, checked against
the authoritative primary journal and report condition metrics. Preserve the selected
conditions in original journal order, including each task's original language order.
Reuse the prompts, fixture contracts, original deterministic oracles and validations.
The eight tasks excluded from the previous report stay outside this scope; do not add
or remove tasks based on future model outcomes. The selection is fixed before future
outcomes but was made after the baseline; disclose that provenance.

The pinned source and shared-input hashes must pass validation before admission.
Every model needs a distinct study ID, model configuration, freeze, journal, outputs,
accounting, logs, checkpoints and read-only monitor in its own campaign namespace.

## One separately saved recovery

Allow at most one fresh recovery attempt per task/language condition after a proved
recoverable terminal INFRA failure. Save the original primary outcome first. Recovery
uses fresh agent state, a new run ID, a separate journal and output directory, and the
same frozen per-attempt settings and budgets. Account for both attempts, including
unknown usage at its full conservative reservation. A timeout's ambiguous cloud call
must never be replayed with the same call ID; the authorized recovery is a new attempt.
No automatic third attempt is permitted.

Eligible failures are settled provider HTTP errors/rate limits/transport timeouts with
safe resource cleanup, or a proved response-delivery failure after successful durable
settlement. Keep bounded local accounting retries and physical transport retry limits
inside each attempt. Do not change keys on rate limits, model failures or timeouts;
rotate sequentially only after explicit confirmed quota exhaustion. Persist exhausted
slots across primary/recovery journals and restarts.

Agent failure, ordinary task timeout, budget exhaustion, low oracle scores and integrity
outcomes are never grounds for a score-seeking retry. Unknown, authentication,
containment, accounting-integrity and unsafe-cleanup failures require investigation.

Wait at least 30 seconds before the eligible recovery. If that sole recovery also has
recoverable INFRA, retain both failures and continue to the next unstarted condition
after cooldown. One isolated recoverable INFRA does not stop or refreeze the campaign.
Three consecutive provider-failed attempts trigger a saved outage pause to prevent
an outage cascade; an unstarted recovery remains durably scheduled. Safety or accounting
failures still pause immediately. Neither pause automatically restarts the campaign.

Commit scheduling before a recovery starts. Crash-safe resume may start only planned
attempts: a started recovery becomes interrupted after ownership-verified cleanup and
is never replayed. Keep exclusive baseline/global and campaign controller locks,
transactional saving, round checkpoints, online backups and atomic exports.

## Accepted analysis decision

The user authorized all recommended choices on 2026-10-01. Recovery-inclusive outcomes
enter the main future analysis; primary-only results are a required parallel sensitivity
and comparison view. The implementation exports both views.
For the recovery-inclusive view, choose the sole recovery if it yields any scored agent
outcome, even zero score or budget exhaustion; never choose the better score or average
attempts. All costs remain in combined accounting regardless of the chosen outcome view.
If a final analyzed condition is INFRA, exclude its whole task triplet from the paired
complete-case comparison and report attrition against the fixed 46-task population.
Do not replace it with a new task or conceal the failure. Show primary-only results
alongside any recovery-inclusive comparison and disclose the changed attempt policy.
The completed baseline PDF and its primary-only analysis remain unchanged.

## Exposure and remaining launch gates

Each model has 138 primaries and at most 138 separately accounted recoveries (276 total
attempts). This is a maximum, not a target. The accepted Nemotron campaign uses
`nemotron-3-super`, thinking on through its documented OpenAI compatibility alias,
65,536 declared context and the baseline per-attempt caps: 200,000 conservative input,
16,000 output, 30 physical transmissions including retries, 4,096 per response, and
min(original task timeout, 600 seconds). Maximum aggregate exposure is 55,200,000 input,
4,416,000 output and 8,280 transmissions across all 276 possible attempts. Only existing
free credits may be used; no purchases or automatic account changes are authorized.
The separately authorized compatibility allowance is 12 transmissions, 200,000
conservative input and 16,384 output, recorded outside benchmark evidence.

`nextbench/scope.py` pins and validates scope. `nextbench/recovery.py` schedules bounded
recoveries and rejects the baseline attempt function. `nextbench/attempt.py` supplies
the separate campaign's hardened Docker callback. `nextbench/runner.py` requires
verified compatibility, production-path, accounting and unit checks before freeze;
launch additionally requires an explicit authorization flag. `nextbench/launch.ps1`
opens the visible read-only monitor and writes durable controller logs only when
launch is subsequently authorized. Preparation does not authorize benchmark attempts.

Before launch, use fake inference and contained integration checks to reduce known
delivery/accounting/transport faults; verify tool/schema/Unicode handling, token
accounting, identity/aliases, response truncation and timeout behavior. Keep the entire
OpenClaw process, its commands/hooks and graders inside the existing hardened Docker
boundary. Never expose host folders, Docker control interfaces or real keys to agents.
