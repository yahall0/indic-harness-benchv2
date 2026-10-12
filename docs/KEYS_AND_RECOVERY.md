# Local keys and result recovery

Run this in an interactive PowerShell terminal (the prompt hides each key):

```powershell
& 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\scripts\configure_keys.py'
```

Enter each of your eligible Ollama Cloud keys at the numbered prompts. Setup accepts up to four distinct keys. It makes no cloud requests. The encrypted store is `config/credentials.dpapi.json` in the new project, protected by Windows current-user DPAPI and a restricted file ACL. Do not paste keys into chat, source files, report files, or container commands. The agent receives a temporary attempt token; real keys are sent to the restricted relay on stdin.

The controller keeps using the current slot. It switches only on an explicit provider quota/usage-exhaustion response. A generic HTTP 429 is a rate limit: bounded retries stay on the same slot. A durably recorded server error, exhausted rate-limit retry or uncertain transport failure ends the current attempt without replaying it or rotating keys. After safe cleanup the controller waits 30 seconds and continues to the next unstarted condition. Three consecutive provider failures in a controller session pause the campaign. Authentication, unknown responses, accounting and safety failures pause immediately. When all configured slots are exhausted, further inference stops. Slot changes and retries are recorded without key values. Exhausted slots remain exhausted across restarts; a reset requires a separate explicit operator action after the provider allowance resets. Different keys can share one provider allowance.

The controller journal is SQLite with WAL and `synchronous=FULL`. Attempt starts, inference reservations, physical forwarding, accounting and final outcomes are durable transactions. Failed and completed attempts are never overwritten or automatically retried. An interrupted attempt is recorded separately; unacknowledged inference remains charged conservatively. Portable JSON/JSONL/CSV exports and a SQLite backup are generated from the journal. Files already saved remain available after an agent container is stopped or removed.

Keep the main `.sqlite3`, `-wal` and `-shm` files together while the controller is active. For copying progress elsewhere, use the controller's online backup command, which includes committed WAL records. Laptop/disk failure still requires a second storage location; local crash recovery cannot replace an off-device backup.

Live benchmark runs remain gated until the full runtime, oracle and translation validations pass and the study is frozen.
