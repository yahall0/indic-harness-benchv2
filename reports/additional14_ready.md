# Additional 14 tasks: READY_TO_START

Only the new 14 tasks will be evaluated: one English, Hindi and Hinglish attempt each, for 42 new attempts. All 120 earlier results, including budget outcomes and infrastructure failures, remain unchanged and will be combined with the additions for reporting. No live attempts were started during preparation.

Every readiness gate passes. The dataset is frozen at runtime revision 6 with the original study ID. A copied-journal launch rehearsal produced exactly 42 new pending conditions, zero old conditions to rerun, and preserved every original result record. The first new triplet runs Hindi, Hinglish, English, continuing the original global language-order rotation. The combined counts of 54 tasks and 162 conditions include the old results.

All 14 new deterministic oracles have correct-workspace, missing-output, task-specific incorrect-output and forbidden-edit evidence. All original 40 oracle validation cases also passed with the expanded private grader. All 50 controller tests and four fresh Docker integration checks passed. Hindi request/response text, multi-round state, safe exports, checkpoint recovery, mock services and blocked host access were exercised using fake inference with zero cloud requests.

The original four infrastructure failures were one local settlement acknowledgment failure, one Ollama HTTP 500 after two retries, and two ambiguous upstream transport failures around 120 seconds. The pinned relay already retries idempotent local accounting operations without replaying inference. The current controller saves settled provider failures, completes cleanup, waits 30 seconds and continues to the next unstarted condition. It pauses after three consecutive provider failures, and immediately for accounting, authentication, integrity, unknown infrastructure or cleanup failures. A fresh simulated timeout check confirmed the failed outcome was saved and the next condition completed. Provider availability remains outside our control.

No model, agent/relay/helper image, temperature, reasoning setting, budget, upstream transport timeout, retry allowance, outcome-attempt count or scoring methodology was changed. Controller file reads explicitly use UTF-8 on Windows. The added grader includes only the new offline fixtures and private validation material, with original scoring preserved. Existing Docker containment and credential separation remain in force.

All four credential slots are configured and locally eligible; their earlier key checks are valid for the unchanged encrypted key store. Live available allowance is determined by the provider. Switching occurs only after explicit quota exhaustion. Generic rate limits use the same key, ambiguous requests are never replayed, and exhausted-slot state persists. No paid credits are bought automatically.

The pre-run backup is at C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\results\checkpoints\before-additional14-20261001T053905Z. During execution each reservation is committed before forwarding, inference traces and completed rounds are saved outside agent storage, final outcomes and safely exported artifacts are durably written, and checkpoints/CSV/JSONL exports are refreshed. A resumed campaign skips every started terminal condition. Local backups cannot protect against loss of the laptop disk itself.

To start after the user authorizes execution, open PowerShell in the project and run:

```powershell
$IhbPython = 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench'
& $IhbPython -u -X utf8 -m bench start
```

In a separate PowerShell terminal, monitor progress and scores with:

```powershell
& 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\scripts\watch_progress.ps1'
```

The monitor reads results only. The controller holds an exclusive OS lock to prevent simultaneous campaigns. The emergency-stop script is documented in `docs/RUNNING_AND_RECOVERY.md` and stops only recorded benchmark-owned containers.

New task IDs, in locked execution order:

- 028-email-thread-merge
- 032-customer-followup-draft
- 037-policy-clause-retrieval
- 044-ci-config-repair
- 048-release-note-changelog
- 054-budget-variance-analysis
- 055-funnel-dropoff-analysis
- 065-capacity-planning
- 066-rollback-readiness
- 068-product-launch-ops
- 079-smallfile-batch-reject-ledger
- 080-schema-roundtrip-conversion
- 096-offline-knowledge-qa-insufficient-evidence
- 103-policy-update-replan-diff

The additions were selected after the first campaign and before their own outcomes. All tasks receive the same analysis. Fifty complete matched triplets are possible if no new infrastructure failures occur; this is not guaranteed. AI translation and review are not independent human validation.
