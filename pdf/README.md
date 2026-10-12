# Experiment report

`Indic_Harness_Bench_Experiment_Report.pdf` is the 15-page report of the completed GPT-OSS-20B / OpenClaw campaign. It combines the initial 40 tasks and additional 14 tasks, using only the 46 original tasks whose three primary language attempts contain no terminal infrastructure failure. There are 138 analyzed conditions, not 138 independent task samples.

Eight whole tasks are excluded. The separately authorized task 037 Hindi recovery does not replace the failed primary condition. Budget-exhausted outcomes remain in the analysis. Earlier discarded pilots and older Indic-attempt results are not pooled.

The report contains nine chart figures, task-level scores, paired bootstrap intervals, category results, resource and token diagnostics, evidence-grounded failure examples, engineering history, security controls, and study limitations. The observed language differences have intervals crossing zero. Only 46 matched tasks meet the requested filter, four below the requested minimum of 50.

## Supporting evidence

- `report_data/analysis_summary.json`: derived statistics, settings, provenance, and diagnostic evidence.
- `report_data/included_condition_metrics.csv`: all 138 included language conditions.
- `report_data/included_task_scores.csv`: original scores and statuses for the 46 matched tasks.
- `report_data/excluded_task_ledger.csv`: excluded IDs and infrastructure causes, without their performance scores.
- `report_data/report_validation.json`: data checks, preservation checks, PDF checksum, and visual review record.
- `figures/`: chart exports in PNG and SVG formats.

The included-condition CSV and exclusion ledger are also embedded as PDF attachments. No credentials, private oracle solutions, or ground-truth fixtures are included in this package.

## Rebuild

From the project root, run `python -X utf8 scripts/build_experiment_report.py` in a Python environment with ReportLab, pypdf, NumPy, and Matplotlib. The builder also checks `tmp/pdf-report-deps` for project-scoped chart dependencies used for this build. It reads the primary journal in SQLite read-only mode and performs no inference or benchmark execution. Rebuilding changes report generation metadata; verify the new PDF and refresh its validation record after any change.

The primary results, frozen runtime, source reference, and vendor code are unchanged by report generation. Page-render evidence is organized under `tmp/pdfs/experiment-report/render`.
