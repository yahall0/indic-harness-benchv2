# READY_TO_START — Nemotron 3 Super

Prepared and frozen on 2026-10-01. **Benchmark launch has not been authorized or started.**
The campaign journal contains exactly 138 planned conditions, zero started conditions,
zero inference transmissions and zero recovery registrations. All 22 readiness gates pass.

Campaign study/runtime ID:
`9dae480295addab8da59fdc15e41b91896e7eb03d983e754f7229fd402c142d7`

## Accepted run

The user's instruction to adopt all recommended choices resolves the model, budget and
analysis decisions. Use Ollama Cloud `nemotron-3-super` with OpenClaw 2026.9.7, temperature
0 and thinking on. The provider advertises boolean thinking; the documented OpenAI
compatibility `high` alias maps to true. It is not an independently supported named
high reasoning effort. Raw reasoning is preserved and delivered separately from final
content. The relay validates every reported response model and forwards no unsupported
provider extensions. There is no model fallback.

Run exactly the completed report's 46 original tasks × English/Hindi/Hinglish = 138
primary conditions, in their original journal/language order. Reuse all 156 prompt files,
52 instruction turns, fixtures, validated deterministic graders and oracle contracts.
The eight tasks excluded from the report remain outside the fixed scope. Selection used
baseline infrastructure attrition and was locked before future model outcomes.

| Parameter | Frozen value |
| --- | --- |
| Declared OpenClaw context | 65,536 |
| Provider-served context metadata | 262,144 |
| Response allowance | 4,096 tokens |
| Per-attempt cumulative input | 200,000 conservative UTF-8 byte-based allowance |
| Per-attempt cumulative output | 16,000 tokens |
| Physical transmissions per attempt | 30, including retries |
| Wall time | min(original task timeout, 600 seconds), across all rounds |
| Transient transport retries | At most two; never replay ambiguous generation |
| Infrastructure recovery | At most one fresh, separately saved attempt per condition |
| Total maximum | 276 attempts; 55,200,000 input / 4,416,000 output / 8,280 transmissions |

## Recovery and analysis

A proved recoverable INFRA failure is saved first, then receives one fresh attempt after
30 seconds. If that recovery also fails recoverably, both records remain and the next
unstarted condition proceeds after cooldown. Three consecutive provider-failed attempts
pause to prevent an outage cascade. Authentication, containment, accounting-integrity,
unknown failures and unsafe cleanup pause immediately. These pauses do not restart
automatically. Agent failures, low/zero scores, ordinary task timeouts, integrity outcomes
and budget exhaustion do not receive score-seeking retries.

Rotate the four credential slots sequentially only on explicit confirmed quota exhaustion.
Generic rate limits, slow inference, timeouts and model failures keep the same key. Exhausted
states persist across primary/recovery journals and restarts. No keys appear in agent
containers, prompts, command lines or outputs.

The main future analysis selects the sole recovery when it yields an agent outcome,
including score zero or budget exhaustion. Required primary-only exports and comparisons
are retained alongside it. Never select the better score. Every attempt and conservative
unknown-usage reservation remains in combined accounting. Paired comparisons against the
completed baseline use complete scored triplets in both models, exclude whole tasks and
show attrition. Bootstrap samples use original tasks, not independent language conditions.
Unavailable token/error measurements are explicitly marked. No direction of language
effects or statistical significance is assumed.

## Verification evidence

- 25 static tests pass, covering recovery/continuation, crash-safe admission, no replay,
  duplicate controller rejection, quota persistence, signed pairing, whole-task attrition,
  zero/budget outcomes, launch authorization, read-only monitoring and emergency-stop scope.
- The current-image simulated full harness passes English, Hindi, Hinglish, retained state
  across rounds, Unicode, reasoning, tools, context and truncation checks.
- Ten relay accounting checks pass, including lost local acknowledgments, generic 429
  retries on the same slot, confirmed sequential quota rotation and no spending after pause.
- An original 001-file English fixture passes the production attempt path using fake
  inference: original round hook and oracle, full score, agent stopped before separate
  grading, valid checkpoint, settled accounting and safe cleanup. It is diagnostic evidence,
  excluded from benchmark rows.
- The separately authorized real cloud suite passes all 24 checks with **10 transmissions,
  55,946 input and 1,450 output tokens**, within its 12 / 200,000 / 16,384 allowance.
  English/Hindi/Hinglish tool execution and a two-round workflow pass through actual OpenClaw.
  No inference is repeated for further preparation. Context checks verify sample behavior
  and declared configuration, not the full advertised capacity.
- All 291 baseline frozen files and 1,116 reference files are unchanged. All seven baseline
  journal tables match the preparation backup. All 162 primary records, the original 120
  records/accounting/artifacts and the completed PDF match their preserved fingerprints.
  An additional hash ledger seals 3,622 baseline output files.
- All check containers, volumes and networks have been removed. No benchmark controller
  is running. All 138 conditions remain planned; a read-only monitor snapshot confirms this.

The entire OpenClaw process, commands, hooks and graders remain in hardened non-root Docker
containers with read-only roots, restricted namespaces/resources, no host folders/control
interfaces, no agent credentials, isolated agent networking and no-network grading. Agents
are stopped before grading. Saving remains transactional with reservations before forwarding,
idempotent settlements, SQLite FULL/WAL, round checkpoints, online backups and atomic exports.
Cleanup and emergency stop address only recorded ownership-verified resource IDs.

## Availability, credits and remaining uncertainty

Official metadata currently lists Nano, Super and Ultra with tools/thinking. Super reports
120B NVFP4 and advertised digest `da11955bb451`; cloud weights cannot be cryptographically
pinned by the client. Launch rechecks metadata and every response checks model identity.
[Official model page](https://ollama.com/library/nemotron-3-super),
[cloud documentation](https://docs.ollama.com/cloud),
[thinking controls](https://docs.ollama.com/capabilities/thinking),
[OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility).

[Published rates](https://ollama.com/pricing) per million input/output tokens are Nano
$0.06/$0.24, Super $0.015/$0.60 and Ultra $0.10/$3.00; GPT-OSS-20B is $0.07/$0.30.
Super has cheaper input and more expensive output, so it is not automatically cheaper.
At the maximum frozen allowances, Super represents approximately $3.4776 in usage credits;
this is an estimate, not a bill or balance guarantee. The probes represent about $0.00171.
Only existing allowance is authorized; no credit purchases or billing/account changes.
Starter eligibility/balance is account-specific, and four keys do not establish independent
quotas. Successful probes establish access for slot-1, not all four balances or campaign
completion. The API does not identify the remaining free-credit balance or credit bucket;
provider rules can draw from an existing purchased balance after included credits.

Live availability can still change. The passed checks address known compatibility and
infrastructure faults; they cannot guarantee zero future INFRA. Preserve failures honestly.

## Later launch

After the user explicitly authorizes start, invoke `nextbench/launch.ps1 -LaunchAuthorized`
from the project directory. It first verifies the frozen readiness gates, starts a controller
with exclusive global/campaign locks and durable separate stdout/stderr logs, and opens a
visible read-only score/progress window. Closing that window leaves the controller running.
The campaign-correct emergency command is `python -m nextbench.stop
campaigns/nemotron-3-super-20261001`. A stop flag blocks further admission and must not be
silently cleared. Started conditions are never automatically replayed.

Current authoritative evidence: `checks/readiness.json`, `config/freeze.json`,
`probes/compatibility/report.json`, `preservation/verification.json`, and
`results/journal.sqlite3`. Historical baseline readiness/README prose is not launch evidence.
