# Preparing a private remote

The completed results and frozen implementation remain unchanged. This
preparation changes Git packaging/documentation, not settings, outputs or scores.

## Included and local-only material

Implementation, prompts, fixtures, validation/provenance, reports, aggregate
exports and research figures remain tracked. The supplied reference snapshot
remains available so the local implementation resolves its original inputs.

Encrypted credential stores, `.env` variants, journals/WAL files, raw attempt
workspaces, Python environments and `tmp/` are excluded. Untracking changes the
Git index only; local bytes remain available to existing report builders. The
duplicate `output/indic results.rar` is local-only; the canonical PDF and data ZIP
remain under `output/pdf/`.

Ignore rules do not remove files from earlier commits. The original commit is
retained, so its temporary files and workstation paths remain in Git history.
The current credential store was absent from that commit. The local audit found
no configured-key or generic-secret matches in reachable Git contents and the
inspected archive members. This applies to the audited revision, not later files.

## Frozen bytes and reproducibility

`.gitattributes` disables automatic newline conversion. Prompts, fixtures, source
and preservation records are hashed byte-for-byte; changing LF/CRLF during clone
would invalidate hashes. Existing local bytes are staged without editing the
underlying files or changing recorded freezes.

Fresh clones can read reports and run trusted offline tests. Resuming/rebuilding
private campaigns additionally requires excluded journals, attempt outputs,
validated images and preservation evidence. Historical records use absolute
workstation paths. Preserve those records and document any future migration.
Do not rewrite them to make an old study appear portable. Never execute source
task modules, agents, submitted commands, hooks or graders on the host.

The cross-platform entry point is `python -m scripts.portable check` / `summary`;
see [Windows/macOS setup](PORTABILITY.md). It uses the standard library and the
published exports, so it does not fail on missing private journals or Windows DLLs.
`publication/manifest.json` records the byte hashes of the published study inputs,
implementation and reports. Keep it consistent when intentionally revising future
published inputs; do not alter historical freeze records.

## Before a later push

Use a private repository unless permission to redistribute the supplied reference
tasks/code has been established. Its root has no LICENSE file; no license is
invented here. A public release needs a separate review of redistribution
permission and historical workstation metadata.

Push the reviewed Git commit rather than uploading the entire local folder, which
bypasses ignore rules. Verify staged paths and repeat a secret scan after adding
files. Never force-add credentials, journals, environment files or raw workspaces.

Git author identity uses the locally configured name/email. No remote is added,
no history is rewritten and no commit is pushed by this preparation.
