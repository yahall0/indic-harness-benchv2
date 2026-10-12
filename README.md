# Indic Harness Bench

A matched evaluation of English, Hindi and Hinglish instructions with OpenClaw,
Ollama Cloud GPT-OSS-20B and Nemotron 3 Super. The completed comparison contains
**50 task units, 150 scored conditions per model and 300 scored conditions total**.
Instruction language varies; fixtures, required English prose outputs, literal
contracts and original deterministic graders remain fixed.

## Completed research

- [Combined 50-task report](output/pdf/Indic_Harness_Bench_50_Task_Combined_Report.pdf)
- [Research data and editable figures](output/pdf/Indic_Harness_Bench_50_Task_Research_Data.zip)
- [Combined data description](output/pdf/report_data/README.md)
- [Original GPT-OSS report](pdf/Indic_Harness_Bench_Experiment_Report.pdf)

The original GPT-OSS campaign evaluated 54 tasks across three languages; its strict
analysis retained 46 whole task groups after primary infrastructure exclusions.
Nemotron evaluated that scope with recorded infrastructure recoveries. Four unused
tasks were then evaluated on both models: exactly 24 new primaries, with no new
INFRA or retries. They extend the same logical studies to 50 tasks. Prior outcomes,
scores, accounting and the original PDF remain preserved.

Nemotron's overall mean was 51.21/100, compared with 39.98/100 for GPT-OSS. Hindi
had the highest mean for both configurations. Paired language intervals include
zero, so the selected task set establishes neither consistent degradation nor
language equivalence. The report records uncertainty, recovery sensitivity,
runtime revisions, scope expansion and translation limitations.

**The campaigns are finished.** Historical readiness/launch handoffs are
provenance, not pending work. Do not rerun, refreeze, retranslate or replace saved
attempts when setting up the repository.

## Repository contents

| Location | Contents |
| --- | --- |
| `bench/`, `runtime/`, `docker/` | Original controller and contained runtime |
| `nextbench/`, `nextbench_repair/` | Nemotron campaign and transport repair |
| `extension50/` | Frozen four-task continuation for both models |
| `tasks/`, `dataset/`, `campaigns/shared/` | Prompts, scope and frozen configuration |
| `vendor/harnessbench/` | Preserved supplied reference; do not modify |
| `provenance/`, `reports/`, `campaigns/` | Historical validation/execution evidence |
| `pdf/`, `output/pdf/` | Reports, aggregate exports and PNG/SVG figures |
| `tests/`, `tests_nextbench/`, `tests_nextbench_repair/` | Offline controller tests |

Raw journals, attempt workspaces, encrypted credentials and temporary files remain
local and are excluded from Git. A clone contains reports/exports and implementation,
not a resumable copy of private campaigns. Absolute paths in immutable provenance
identify the original workstation; they are not portable setup instructions.

## Offline checks

Use Python 3.12 or later. A fresh Windows/macOS clone needs no private journals,
keys, Docker, local dependency cache or reporting packages for these commands:

```sh
python -B -X utf8 -m scripts.portable check
python -B -X utf8 -m scripts.portable summary
python -B -X utf8 -m unittest discover -s tests_portable -v
```

Use `python3` on macOS or `py -3.12` on Windows if `python` is unavailable. See
[platform setup and limits](docs/PORTABILITY.md). The portable check verifies file
integrity, original frozen bytes and the saved 300-condition statistics.

The historical controller suites below use synthetic temporary journals and mocked
provider/Docker operations. They make no cloud calls and are checked on Windows:

```powershell
python -B -X utf8 -m unittest discover -s tests -v
python -B -X utf8 -m unittest discover -s tests_nextbench -v
python -B -X utf8 -m unittest discover -s tests_nextbench_repair -v
```

The trusted controller uses the standard library. Optional report-analysis tools:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-report.txt
```

On macOS use `python3 -m venv .venv` and `.venv/bin/python -m pip install -r requirements-report.txt`.

Reporting scripts can use installed packages when the local `tmp/pdf-report-deps`
cache is absent. Historical rebuilds also require private read-only journals and
preservation records; some rendering paths use Windows fonts and Poppler. Read
completed reports without rebuilding to retain original publication artifacts.

## Execution and credentials

Actual agents, commands, hooks and graders run entirely inside hardened Docker;
see [AGENTS.md](AGENTS.md). Agents receive no host folders, Docker control interfaces
or real keys. A local Windows DPAPI store holds credentials; never commit/upload
it or copy it as credential setup for another workstation. New inference requires
separate authorization and validated containment, accounting and exclusive locks.

## Remote preparation

See [publishing notes](docs/PUBLISHING.md). Temporary files are untracked without
being deleted. `.gitattributes` preserves frozen bytes on checkout. Original Git
history and immutable evidence are retained; earlier commits still contain their
temporary files and workstation metadata.

**Use a private remote unless redistribution permission is established.** The
supplied reference root has no LICENSE file. No license or redistribution rights
for those tasks/code are invented here. Setup performs no remote publication or
new benchmark execution.
