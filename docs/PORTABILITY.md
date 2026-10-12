# Windows and macOS clones

The portable entry point requires only Python 3.12+ and the Git-tracked files. It
does not require Docker, Ollama, credentials, private journals, installed reporting
libraries or the original Windows directory. Run from the cloned project root.

Windows (PowerShell):

```powershell
py -3.12 -B -X utf8 -m scripts.portable check
py -3.12 -B -X utf8 -m scripts.portable summary
py -3.12 -B -X utf8 -m unittest discover -s tests_portable -v
```

macOS (Terminal, with Python 3.12+):

```sh
python3 -B -X utf8 -m scripts.portable check
python3 -B -X utf8 -m scripts.portable summary
python3 -B -X utf8 -m unittest discover -s tests_portable -v
```

`check` validates published file hashes, normalizes historical Windows separators
only for reading freeze records, verifies the original frozen file bytes, validates
all 50 matched task groups and independently checks means/completion counts against
the saved analysis. It never edits the historical records. `summary` computes
scores from the 300 saved condition rows without importing the historical runner.

Optional report packages use a normal environment instead of copied Windows DLLs:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-report.txt
```

On Windows use `.venv\Scripts\python.exe`. Full historical report builders also
require private journals; some use Windows fonts and Poppler. The completed PDFs
and figures are included and can be opened directly on either platform.

Historical execution controllers, curation scripts and preservation snapshots
retain the original workstation paths and freezes. They are not a fresh-clone
launch interface, and the excluded raw journals are not replaced with empty ones.
The full historical unit suites primarily validate the original Windows runtime;
the portable suite is the cross-platform fresh-clone check.

Actual model evaluation requires Docker containment, validated platform-specific
images and credentials, explicit scope/authorization and fresh provenance. Windows
DPAPI files do not move to a Mac. Review and data analysis on a clone work without
them. No new Mac model campaign, fallback or weakened isolation is introduced here.

## Platform verification

Local preparation checks a clean staged checkout on Windows without private keys,
journals or the dependency cache. It does not claim a live macOS or ARM Docker
benchmark was run. After pushing, the manual `Portable research checks` workflow
can verify the same published data and portable tests on Windows, macOS and Linux.
It uses read-only repository permissions, pinned official actions, no repository
secrets, no reporting-package installation and no model calls. It is not triggered
automatically by a push or pull request.
