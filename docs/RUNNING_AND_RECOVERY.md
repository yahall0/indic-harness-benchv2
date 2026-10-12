# Running, stopping and retaining progress

Use the bundled interpreter from the new project directory:

```powershell
$IhbPython = 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench'
& $IhbPython -X utf8 -m bench ready
```

`ready` is read-only with respect to credentials and makes no inference requests. It checks source hashes, all 54 oracle records, translation review, runtime checks against the current implementation fingerprint, checked credential slots, images and the frozen dataset. The additional translations and final review are complete. The append-only freeze must match the current files. A failed gate blocks live execution.

For the authorized 14-task extension, use `python -m bench extend-freeze` after all preparation gates pass. This appends the tasks, preserves the original study ID and records prompt, dataset, implementation, validation and image hashes. Do not use an ordinary new-study freeze over the completed original campaign. `python -m bench start` starts the evaluation only after all gates pass. Do not run it during preparation. It serially rotates language order between task triplets, reuses an eligible slot, and creates fresh state between languages.

The four slots keep their current key until explicit quota exhaustion. Generic rate limits retry the same key at most twice. A durably settled provider timeout, HTTP server error or exhausted rate-limit retry ends that attempt as `infrastructure_failed`; after cleanup the controller waits 30 seconds and continues with the next unstarted condition. An ambiguous request is never replayed, its full reservation remains charged, and it does not trigger key rotation. Three consecutive recoverable provider failures in one controller session pause the campaign to avoid spending through an outage; it never restarts automatically. An explicit manual resume starts a new session and processes only unstarted conditions. Authentication, accounting, integrity, unknown infrastructure and cleanup failures still pause immediately. Exhausted slots persist across restarts. Never use automatic key cycling to hide agent failures or repeat an outcome.

For an emergency, run this in another PowerShell terminal:

```powershell
& 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\scripts\emergency_stop.py'
```

It kills only benchmark containers recorded in `results/journal.sqlite3`, checking ownership and recorded Docker IDs. It does not prune Docker globally or delete host folders. The active controller stops further attempts when execution fails. Current in-memory workspace changes may be lost in an emergency; previously committed results, inference accounting and round checkpoints remain on Windows.

Use `python -m bench backup` for an online SQLite backup plus CSV/JSONL metrics exports. The primary journal uses WAL and synchronous FULL commits. `results/runs/<run_id>` holds saved prompts, native round output, inference traces, workspace snapshots, safely exported artifacts and final outcomes. Reservations are committed before upstream requests, and saved outside the agent filesystem. Missing or uncertain usage remains conservatively charged.

After a crash, starting again stops recorded containers, marks running attempts interrupted and skips every already-started or completed condition. It does not retry agent failures to improve scores. Remaining planned conditions can continue when the gates pass. Interrupted and quota-paused conditions stay visible as incomplete evidence.

After an actual provider allowance reset, an operator can run `python -m bench reactivate-slot --slot slot-1 --allowance-reset-confirmed`. This re-enables that slot without overwriting any result or resetting run budgets. It does not assume separate keys have independent allowances or buy credits.

Keep SQLite WAL files with the active database. Use the online backup for copying results; copy backups to a second storage location if protection from laptop or disk failure is needed. Local checkpointing protects against process failures, not loss of the underlying disk.

The extension adds 42 conditions. `start` plans the combined 162-condition sequence and skips all 120 preserved terminal results. No new conditions are inserted into the main journal during preparation. To view progress and scores independently, open PowerShell and run `& ".\scripts\watch_progress.ps1"` from the project directory. The monitor reads the journal and does not run benchmarks. The controller uses an exclusive OS lock, so a second `start` cannot launch a separate campaign.
