# Methods notes — translation-stage draft

## Proposed comparison

The planned experiment holds the task, local fixture, deterministic oracle, OpenClaw harness, model, tool exposure, and inference budgets constant while changing only the user-instruction language across English, Hindi, and Hinglish. It covers 40 matched tasks selected before model outcomes, five from each original task family. The current prompt set contains 46 distinct instruction files because some tasks have multiple rounds; all 138 language prompt files preserve round boundaries.

A shared English output-contract footer is appended identically to all language conditions so filenames, commands, identifiers, JSON keys, enum values, headings, and exact output strings stay comparable. Report this as a design choice and limitation: the treatment is the instruction body, not every token in the complete prompt.

## Planned protocol (not yet executed)

The pilot is planned as one attempt per task-language condition: 120 total conditions. Keep all rounds of a task in one attempt, reset state between language variants, and rotate language order. Planned inference settings are GPT-OSS-20B through Ollama Cloud and OpenClaw, with temperature 0 and medium reasoning effort; exact model, harness, image digests, token caps, and runtime must be frozen after integration. Stop when eligible free quota is exhausted. Do not assume separate accounts multiply permitted free use.

Primary outcome is the original deterministic oracle score. Planned secondary records include completion, integrity violations, time and inference latency, token counts, prompt-token inflation, tool calls/errors, retries, compaction, timeout cause, and artifacts. Mark unavailable measurements explicitly. Paid LLM process grading is outside the design.

Planned reporting uses paired task-level English-minus-Hindi and English-minus-Hinglish score differences in percentage points, category summaries, and uncertainty intervals resampled by original task. Separate agent failures from infrastructure failures and show incomplete triplets. Diagnose from traces without claiming a definitive split between model and harness responsibility.

## Translation provenance and limitations

Prompts are AI-translated and AI-self-reviewed. Hindi wording was drafted in Romanized Hindi and normalized to Devanagari with a deterministic common-word mapping outside protected literals. Hinglish uses Roman script. The review is not independent human or bilingual validation; obtain qualified Hindi review before public release. Static checks establish file coverage and literal/script consistency, not semantic equivalence or cultural naturalness.

No oracle validation, runner integration, model calls, pilot attempts, or outcome metrics exist at this checkpoint. The candidate list is not a validated release. Selection favors local, lower-dependency tasks and does not represent the full space of Indian-language agent work. A 40-task, single-model, single-harness exploratory pilot cannot establish broad Indian-language capability claims, isolate tokenizer effects causally, or guarantee statistical significance.
