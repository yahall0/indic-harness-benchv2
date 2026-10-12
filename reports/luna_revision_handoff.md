# Luna translation correction handoff

The infrastructure and oracle preparation is saved. No benchmark evaluation has started. Four real credential probes succeeded; all later integration checks used fake inference and spent no Ollama credits. The target is 40 matched tasks, 46 instruction rounds, 138 language prompt files and 120 single-attempt evaluations.

## Work for GPT-6 Luna

1. Work only in `C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench`. Read `dataset/task_manifest.json` and select only entries with `pilot_candidate: true`. The adjacent reference and `vendor/harnessbench` remain read-only. Do not execute reference hooks, graders or task commands on Windows.
2. Task 025 was deferred because its original oracle has an impossible underscore check. Task 027 replaces it in the same family, before any benchmark outcomes. Its English prompt is already copied; create its Hindi and Hinglish prompts. Do not reinstate 025.
3. Review every instruction round of the selected 40 tasks directly against its original English source. The existing Hindi drafts were mechanically normalized and retain Roman Hindi words such as `hone`, `anivarya`, `lene`, `uske` and `bawajood`. Rewrite prose into natural Devanagari Hindi with familiar technical terms. Review the Roman-script Hinglish for natural phrasing and semantic equivalence too. Do not merely apply another transliteration dictionary.
4. Edit `tasks/<task_id>/prompts/hi/<prompt_file>` and `hinglish/<prompt_file>` as UTF-8 text. Preserve all literal filenames, paths, placeholders, commands, JSON keys, enum values, required headings, exact output strings, quoted strings, backticks, code blocks, dates, numeric limits, ordering and negation. Preserve all multi-round instructions and the original round order. Do not add solution hints or inspect private validation solutions to enrich prompts.
5. English source bodies stay unchanged. Keep the exact common English output-contract footer from `bench/translations.py` in all three conditions. Prose deliverables stay English in every condition so output-language grading is constant. Disclose this controlled choice.
6. Resolve the source wording ambiguity for task 067 consistently: it says one output file but lists two. Append the same English clarification to all three versions: `Benchmark clarification: Produce both listed output files: out/canary_decision.json and out/metric_evidence.csv.` Keep the source body intact. Update the checker to recognize this task-specific common suffix before comparing protected source literals. Do not alter other output contracts.
7. Update `dataset/translation_reviews.json` only after reviewing each task. Record AI translation and AI self-review, never independent human validation. Check requirement coverage, negations, numerical/date constraints, ordering, technical literals, naturalness in both languages and a backtranslation comparison. Clear pending issues only when resolved. Update task translation statuses and semantic review status, while leaving `release_eligible: false` until the later release gates pass.
8. Do not run the old `scripts/materialize_translations.py`: it would overwrite corrections with the mechanical drafts. Do not change runner, credential, isolation, budgets, task selection, source fixtures, or oracle code. Do not call Ollama, freeze the release, or start evaluations.

Run only these no-credit static checks from the new project using the bundled Python interpreter:

```powershell
$IhbPython = 'C:\Users\prish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location -LiteralPath 'C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench'
& $IhbPython -X utf8 -m bench.translations
& $IhbPython -X utf8 -m unittest discover -s tests -p test_translations.py
& $IhbPython -X utf8 -m bench verify-reference
```

There must be exactly 40 selected triplets and all 138 selected prompt files; extra deferred task folders do not enter the release. The static checker cannot establish semantic equivalence; complete the clause review yourself and disclose its AI provenance.

## Stop here

After corrections and checks, write `reports/luna_revision_completion.md` with counts, checks, unresolved issues and changed files. Copy that note to this chat's `outputs/indic-harness-bench-review` folder. Then stop and tell the user to switch back to GPT-6.1 Sol. Do not continue to freeze or evaluate.

On the Sol return: run `python -m bench ready`, resolve remaining gates, freeze only after all pass, inspect saved protocol and manifest, and stop ready to start. The current user authorization is preparation until ready; actual benchmark evaluation has not been requested at this checkpoint.
