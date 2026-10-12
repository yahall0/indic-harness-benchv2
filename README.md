# Indic Harness Bench

Partial Phase I: matched English, Hindi, and Hinglish instruction variants for
lightweight offline agent tasks, using OpenClaw with Ollama Cloud GPT-OSS-20B.

## Current checkpoint

- READY_TO_START: all validation, preservation, security and freeze gates pass.
- Run only the 14 added tasks: 42 new attempts across English, Hindi and Hinglish. The original 120 terminal results stay unchanged and are skipped at launch.
- The combined reporting dataset contains 54 tasks and 162 conditions; those counts include the existing results and do not request a full rerun.
- All 106 source definitions were audited and the 1,116 reference files remain unchanged.
- Every added triplet passed AI semantic review, protected-literal checks and positive/negative oracle validation. The expanded grader passed compatibility checks for all original 40 tasks.
- The frozen dataset contains 61 instruction turns and 183 prompt files. GPT-6 Luna translated the additions; the final AI check corrected two small wording differences before freezing. This is not independent human validation.
- The same GPT-OSS-20B, OpenClaw 2026.9.7, temperature 0, medium reasoning, budgets, language-order rotation, credentials and paired analysis remain in effect.
- All 50 controller tests and four fresh Docker integration checks passed without cloud inference. A copied-journal admission check proves exactly 42 new planned attempts and zero original attempts to rerun.
- All four locally configured anonymous credential slots are eligible. Keys rotate only on confirmed quota exhaustion; no automatic purchase is allowed.
- A pre-run SQLite backup preserves all 120 existing attempts. No new benchmark attempts have started.

Preparation stops here. On the user's start instruction, one exclusive controller launches the 42 pending conditions and a separate read-only monitoring terminal can show progress and scores. See `reports/additional14_ready.md` for the verified state. Never rerun curation or translation bootstrap scripts over the frozen dataset.

The additions were selected after the original campaign, before their own model outcomes. Disclose that expansion. The four infrastructure failures remain missing observations. Fifty complete paired triplets are possible if the additions have no new infrastructure failures; model failures and budget exhaustion remain outcomes in the analysis. AI self-review is not independent human validation.

## Preparation commands

From this directory, with the bundled Python interpreter:

```
python -m bench status
python -m bench verify-reference
python -m bench isolation-check
python -m bench ready
python -m unittest discover -s tests -v
```

`isolation-check` runs trusted synthetic probes in disposable Docker containers;
it makes no model calls. It briefly uses a benign localhost HTTP canary to prove
that the isolated network blocks host access, then removes only owned test
containers, networks, and volumes. A digest-pinned Python image must be available.

## Material locations

- `vendor/harnessbench/`: preserved private reference snapshot; do not edit.
- `provenance/`: source hashes and integrity evidence.
- `dataset/task_manifest.json`: all inclusion, exclusion, and deferral decisions.
- `dataset/pilot_plan.json`: original execution order followed by the locked 14-task expansion.
- `dataset/extension_selection.json`: additions and selection provenance.
- `provenance/initial-40/`: immutable original freeze, metadata and journal backup.
- `reports/additional14_methods.md`: identical protocol, expansion disclosure and sample accounting.
- `reports/luna_additional14_instructions.md`: completed translation-stage instructions and stop boundary.
- `reports/additional14_ready.md`: current readiness, new-only launch behavior, backups and monitoring.
- `reports/additional14_infrastructure_review.json`: original failure evidence and verified recovery behavior.
- `config/protocol.json`: planned shared inference and resource budgets.
- `bench/security.py`: restrictive Docker configurations and safe export checks.
- `reports/security_check.json`: base Docker boundary evidence and its limits.
- `reports/*_check.json`: actual runtime, rotation, helper and save/reopen checks.
- `docs/RUNNING_AND_RECOVERY.md`: gated run commands, checkpoints and emergency stop.
- `reports/methods_checkpoint.md`: adaptations, metrics and study limitations.

The source snapshot has no LICENSE file in the supplied root. Keep it private;
verify redistribution rights before publicly packaging original tasks or code.
No publication is part of this checkpoint.
