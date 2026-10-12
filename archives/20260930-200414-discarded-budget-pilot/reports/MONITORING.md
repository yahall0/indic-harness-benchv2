# Monitoring the running benchmark

The benchmark controller was started independently of this chat. A PowerShell window titled **Indic Harness Bench - live progress and scores** shows a read-only scoreboard, refreshed every five seconds.

The scoreboard shows finished/120, active task and language, elapsed time, inference requests, known token usage, credential eligibility, each task's English/Hindi/Hinglish scores, and recent events. Scores appear after grading. Original scores range from 0 to 1; PASS additionally requires every oracle check and no integrity violation. Pending and infrastructure/quota failures remain visible.

**Closing the monitor or pressing Ctrl+C there does not stop the benchmark.** Keep Docker Desktop running and the laptop awake. The controller's durable saves continue without Codex monitoring.

## Reopen the monitor

In any PowerShell terminal:

    & 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -X utf8 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\scripts\watch_progress.py'

For a single snapshot, add --once.

## Saved results

The project directory is C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench.

- results/exports/metrics.csv: scores and attempt metrics; refreshed after every attempt.
- results/exports/metrics.jsonl and analysis.json: reproducible records and paired comparisons.
- results/runs/: per-round prompts/output, inference traces, workspace snapshots, artifacts and final run.json.
- results/journal.sqlite3: durable run and inference accounting.
- results/checkpoints/latest/: consistent SQLite backup and JSON/JSONL checkpoints.

The CSV/analysis can lag the live journal while an attempt or grading is running. The monitor reads the journal without writing to it.

If the monitor says STOPPED with pending runs, inspect the saved status and logs before resuming. Quota or infrastructure errors cause a pause; agent failures are recorded and the controller continues according to the fixed protocol. No key values appear in the monitor.

## Emergency stop

From another PowerShell terminal:

    & 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\scripts\emergency_stop.py'

This stops only recorded benchmark-owned Docker resources. Previously saved results remain. Current unsaved workspace changes may be lost.

## Recovery and backup

To continue remaining planned conditions after the controller has stopped:

    Set-Location -LiteralPath 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench'
    & 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -u -X utf8 -m bench start

The controller refuses duplicate concurrent spending, skips already-started conditions and records interrupted runs. It does not automatically retry a failed condition for a better score.

To make an online backup and refresh exports, from that same project directory:

    & 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 -m bench backup

Copy the backup to separate storage for protection from laptop/disk failure. All exhausted slots remain exhausted across restarts; see RUNNING_AND_RECOVERY.md for reactivation after an actual provider allowance reset.

Current launch logs:

- C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\results\controller-20260930-190339.log
- C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\results\controller-20260930-190339.err.log

## Startup check

Task 001 English and Hinglish, and task 002 Hindi scored 1.00 and were saved. Task 001 Hindi stopped at a relay/accounting gate. Its original diagnostic grader score is retained in records, but the INFRA condition is excluded from language-performance comparisons and the monitor hides its diagnostic score. The controller was resumed for unstarted conditions only. No failed condition was rerun, and no early credential rotation occurred. The precise gate exception remains undiagnosed; any recurrence causes the same safe pause.

## Runtime revision 2

The relay repair passed all readiness gates and the controller resumed only unstarted conditions. See RELAY_REPAIR.md. Current log paths are recorded in results/controller_process.json; the initial log paths above are historical. If another infrastructure error occurs, the controller pauses and records stage/type diagnostics. The original incident cause is not proven from the old generic record.
