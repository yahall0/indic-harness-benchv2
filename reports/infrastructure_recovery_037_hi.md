# Authorized infrastructure recovery: 037, Hindi

The original condition stopped after two provider HTTP 500 retries followed by a successful upstream response. Delivery to OpenClaw failed with BrokenPipeError. The terminal primary record, full inference accounting, traces and artifacts remain unchanged.

The user explicitly requested one recovery attempt. It used fresh Docker state with identical prompts, model, budgets, tools and grading. This recovery completed normally, scored 0.0 and had no integrity violation. It is an agent outcome and is not retried to improve its score. The single locked controller resumed the unstarted conditions afterward.

The primary one-attempt analysis stays intact. `results/exports/infrastructure-recovery/analysis_with_recovery.json` is a separately labeled sensitivity analysis that uses this sole authorized recovery if it yields any agent outcome, regardless of score. Both attempts and their resource usage remain available, including `recovery_cost_accounting.json`. Disclose this operator-requested retry after observing an infrastructure failure; do not present it as pre-registered single-attempt evidence.

Use `scripts/emergency_stop.py` during recovery as well as normal execution. It checks the primary and recovery journals and stops only recorded, ownership-verified containers. A mocked test verified both journal targets without stopping real containers. No agent-generated commands run on Windows and the containment configuration is unchanged.
