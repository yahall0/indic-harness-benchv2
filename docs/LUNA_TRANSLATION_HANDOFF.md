# Translation stage completed

This stage has been completed. The remaining instructions below document its workflow. Current handoff and stop point: `../reports/luna_translation_handoff.md`. Wait for the user to switch back to GPT-6.1 Sol and confirm before continuing.


## Entry and stopping rules

Start only after the user confirms they switched this chat to GPT-6 Luna.
The 40-task selection is already recorded in `dataset/task_manifest.json` and
`dataset/pilot_plan.json`. Translate only entries whose status is `candidate`.
Do not translate excluded or deferred tasks. Do not expand or replace the set.

Use the current chat model to write the translations directly. Do not call an
external translation API, Ollama, OpenClaw, or another agent to do this work.
Do not install/start model runtimes, create credentials, or make cloud calls.
If a task's wording or oracle contract appears inconsistent, record the exact
problem for Sol. Do not silently repair, weaken, or remove the requirement.

**Stop after the translation checks and handoff report.** Tell the user:
"The translation stage is complete [or list the remaining issues]. Please switch
back to GPT-6.1 Sol and confirm so it can continue oracle validation and secure
runner integration." Do not continue into those stages yourself.

## Source and output layout

Read each selected task's original prompts under
`vendor/harnessbench/tasks/<task_id>/`. The manifest's `prompt_rounds` preserves
execution order; `source_prompt_files` lists each unique file to translate.
Some tasks have several rounds; translate all their distinct instruction files.
The simulated multi-day task has consecutive rounds, not actual days of waiting.

Create only these prompt files for each original filename:

```
tasks/<task_id>/prompts/en/<original_prompt_filename>
tasks/<task_id>/prompts/hi/<original_prompt_filename>
tasks/<task_id>/prompts/hinglish/<original_prompt_filename>
```

Use UTF-8. The English body must exactly match the original text as decoded with
Python `read_text(encoding='utf-8')`; preserve its original final newline.
Append `bench.translations.OUTPUT_CONTRACT` unchanged to every language version.
This shared English output-contract footer keeps English prose output grading
consistent across conditions. It is deliberately constant and must be disclosed
in the study methods; the task instruction body is the language manipulation.

Do not translate fixtures, code, metadata, tool schemas, oracle files, ground
truth, example output values, proper names, or the common output-contract footer.
Do not insert solutions, calculated answers, model hints, or extra context.

## Translation rules

- Hindi: natural Devanagari instructions; common technical loanwords are fine.
  Avoid overly formal terminology that changes the intended register.
- Hinglish: natural Roman Hindi-English code switching, not merely the English
  source and not a mechanical transliteration of formal Hindi. Use no Devanagari.
- Preserve every requirement, prohibition, condition, exception, and ambiguity.
  Keep the original numbering, bullet hierarchy, and round-specific intent.
- Preserve every placeholder such as `$WORKSPACE` and `$MOCK_API_BASE` exactly,
  including occurrence counts. Never substitute local Windows paths.
- Preserve all text inside backticks, double quotes/curly double quotes, and
  fenced code blocks exactly. These often carry filenames, keys, enum values,
  required headings, markers, output phrases, JSON examples, or commands.
- Preserve numeric values and their formatting, dates, units, limits, comparison
  operators, inclusive/exclusive bounds, order of steps, and negative conditions.
  Use the same Arabic digits as the source.
- Preserve unquoted literal tokens when they define a contract: filenames,
  headings required in the output, keys, IDs, and fixed vocabulary. The automated
  checker cannot reliably discover all such tokens, so check these manually.
- Output artifacts remain English or use the exact original schema vocabulary,
  even when the instructions are Hindi or Hinglish. Do not translate expected
  output headings or exact required phrases.

## Authoring and self-review workflow

Work in batches of about five tasks, finishing every round of each task. For each:

1. Read the full original prompt(s) and manifest literals. Read source oracle
   text only if needed to clarify literal contracts; never execute/import it.
2. Enumerate requirements and protected literals mentally or in a short review
   note. Produce both translations while preserving structure and identifiers.
3. Compare both versions against the source clause by clause. Pay special
   attention to "do not", "only", "at least", "at most", "before", "after",
   "unless", "first seen", thresholds, sorting, and missing evidence.
4. Independently restate each translated clause in English and compare that
   restatement with the original. This is AI self-review, not a human or
   independent bilingual review. Correct omissions and changed meaning.
5. Record a task review with only genuinely completed checks in
   `dataset/translation_reviews.json`, keyed by task ID. Use this shape:

```json
{
  "<task_id>": {
    "reviewer": "AI self-review",
    "model": "GPT-6 Luna (user-selected chat model)",
    "independent_human_review": false,
    "checks": {
      "requirements": true,
      "negations": true,
      "numbers_and_dates": true,
      "round_order": true,
      "no_new_hints": true,
      "technical_literals": true,
      "hindi_naturalness": true,
      "hinglish_naturalness": true,
      "backtranslation_comparison": true
    },
    "notes": "Concrete ambiguity or non-obvious literal decision, or an empty string.",
    "unresolved_issues": []
  }
}
```

Do not mark checks true without completing the corresponding review. Do not
change `validation.release_eligible` to true: oracle and runtime validation are
still pending. Update only translation status and semantic-review fields in the
manifest, keeping exclusions, source hashes, round order, and selection intact.

## Static checks

Run from `C:\Users\prish\Desktop\AgenticHarnessIndic\indic-harness-bench`:

```powershell
& 'C:/Users/prish/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 -m bench.translations
& 'C:/Users/prish/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 -m bench verify-reference
```

The translation checker verifies all expected files, UTF-8, unchanged English
bodies, the common footer, placeholders, backtick literals, quoted literals,
code blocks, numeric tokens, Hindi script, Roman Hinglish, and review provenance.
Passing it does not prove semantic equivalence; perform the clause review too.
Do not weaken the checker to hide a translation error. If a check is a false
positive, document the exact source/translation fragment for Sol.

## Final handoff

Create `reports/luna_translation_handoff.md` with task/file counts, checker result,
review provenance, unresolved issues, and the explicit statement that oracle
validation and evaluation have not run. Copy this report and
`reports/translation_check.json` to this chat's
`outputs/indic-harness-bench-review` folder. Do not copy credentials or old results.

The handoff to GPT-6.1 Sol should list these remaining stages:

- Validate correct workspaces and meaningful negative/forbidden-edit cases for
  every retained task; run hooks/graders only in containers.
- Complete OpenClaw image, isolated task helpers, credential relay, authoritative
  usage logging, separate grading, safe exports, and emergency stop.
- Validate the complete runtime boundary; the existing Python-image checks
  prove only the base Docker controls, not the finished harness integration.
- Freeze prompts, images, protocol, and selection; configure credentials locally;
  run up to 120 attempts with rotating language order and quota-aware stopping.
- Produce metrics and a paper methods/limitations report. Report exact completed
  counts, infrastructure failures, and incomplete triplets without inflating claims.

Then stop, ask the user to switch back to GPT-6.1 Sol, and wait for confirmation.
