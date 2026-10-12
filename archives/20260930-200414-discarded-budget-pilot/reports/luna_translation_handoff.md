# Translation-stage handoff

The GPT-6 Luna translation stage is complete. The selected set contains 40 candidate tasks (five from each of the eight original families), with 46 distinct prompt rounds/files translated into English, Hindi, and Hinglish: 138 prompt files total. The planned pilot remains 40 matched tasks × 3 languages = 120 conditions; **no pilot attempts have run**.

English prompt bodies are copied from the reference sources. Hindi instructions use Devanagari; Hinglish uses Roman script. The shared English output-contract footer is identical in all three conditions so output-language grading stays constant. Disclose this footer in the methods section.

The Hindi wording was authored in a Romanized draft and normalized into Devanagari with a deterministic common-word mapping outside protected literals. The translations received AI self-review against source requirements and a static comparison of protected literals, numbers, rounds, and output files. This is not independent human or independent bilingual review. The review records are in `dataset/translation_reviews.json`; please obtain a qualified Hindi review before treating the set as a final public release.

`python -X utf8 -m bench.translations` passed: 40 tasks, 46 prompt sources, all 138 expected language files present, and no detected literal, number, footer, encoding, script, or review-provenance errors. This check does not establish semantic equivalence or task correctness. `python -X utf8 -m bench verify-reference` also passed: all 1,116 reference files match their recorded hashes.

The task manifest still marks the candidates as not release-eligible. **Oracle validation: not run (0 validated triplets). OpenClaw runner integration: not complete. Ollama calls: 0. Pilot runs: 0. Results and study metrics: none.** A prior Docker boundary probe passed the base isolation checks, but it does not validate a complete OpenClaw, helper, relay, and grader runtime; see `reports/security_check.json`.

One source wording issue is preserved for GPT-6.1 Sol to resolve before freeze: task `067-canary-release-check` says “exactly this output file” and then lists two output files. The wording is identical in the three language conditions. Do not silently repair only one condition.

Next, GPT-6.1 Sol should validate correct-workspace and meaningful negative oracle cases for all candidates, resolve or defer source inconsistencies consistently, complete and test the full container/runtime boundary, freeze the final validated selection, then run only the quota-affordable pilot and produce its metrics and methods/limitations report. The source papers and code remain reference-only. No results from the older Indic attempt were used.

Stop point: translation and static checks are complete. Wait for the user to switch back to GPT-6.1 Sol and confirm before continuing.
