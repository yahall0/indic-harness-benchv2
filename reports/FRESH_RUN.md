# Fresh benchmark run: 200,000 input cap

The previous run was stopped and discarded from the primary study at the user's request. Its entire results directory, protocol, freeze and reports were archived rather than deleted. No old scores were carried into the new study.

All 40 matched English/Hindi/Hinglish tasks are being rerun: 120 newly planned conditions. The cumulative input cap is 200,000 instead of 100,000. The 30-request, 16,000-output-token, 4,096-response-token and original capped 600-second timeout limits remain. Model, harness, tasks, prompts, oracle scores and Docker restrictions are identical across the new conditions.

The preflight input guard remains a conservative UTF-8 byte bound. It releases unused reservations when actual usage is known; unknown transmission usage remains charged conservatively. The larger cap provides additional room but does not guarantee completion. Budget-denial events now identify input, output or request limits and record the attempted reservation alongside charged and known usage. Unknown aggregate usage is explicitly null, with known tokens and outstanding reservations reported separately.

All 25 unit tests and Docker runtime, relay, helper and controller checks passed. Reference integrity and all freeze/readiness gates passed. Credential slot states were preserved, and keys still advance only on explicit provider exhaustion. No diagnostic model requests were made for this policy restart.

The fresh monitoring terminal refreshes every five seconds, shows the 200,000-input cap, and has console Quick Edit disabled to prevent selection from freezing output. Closing the monitor does not stop the benchmark.

Use MONITORING.md for reopen, emergency-stop and recovery commands. The primary results are now the fresh project results directory; earlier outputs and runtime repair notes describe historical stages. No old/new results should be pooled as one uniform-budget study.

Archived old run: C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench\archives\20260930-200414-discarded-budget-pilot

New study ID: be79c2f6c171dbe17a7c517df8fba4996844029a2be4cfd92b47db77ef0ee036
