# Tag-tracked releases instead of master-HEAD pulls

## Context

Users run CocktailBerry from a `git` checkout and update in-place via `src/updater.py`.
The updater advertised "update to `vX.Y.Z` available" (comparing the local version to
the latest tag) but then ran `origin.pull()` — landing on whatever was at the tip of
`master`. Because feature PRs merge `dev → master` as they complete (release-drafter
runs on push to `master`), `master` accumulates un-released commits between releases.
So both a fresh `git clone` and an in-place update could leave a user on a partial,
un-released state. This worked by accident only because the post-publish version-bump
PR pushed `master` HEAD to the released version.

## Decision

The **tag** is the unit users track, not the `master` branch tip.

- **Updater** (`src/updater.py`): `update()` does `fetch` + `reset --hard <latest-tag>`
  while staying on the `master` branch (no detached HEAD, so the existing
  "must be on master" guard at `check_for_updates()` still passes).
- **Install** (`scripts/all_in_one.sh`): after cloning `master`, `git fetch --tags`
  + `git reset --hard <latest-tag>` (stays on `master`). The dev-flag path still
  checks out `dev`.
- **Version bump moves before the tag.** A `prepare-release` `workflow_dispatch`
  reads the current draft's resolved version, bumps `pyproject.toml` + `uv.lock` on a
  branch, and opens a PR to `master`. The maintainer approves/merges it (the existing
  master gate), then publishes the draft — so the tag points at a commit that already
  contains its own version. The post-publish `update-version` job in
  `release-build.yml` is removed; the Docker and web-client jobs (on `release: published`)
  are unchanged.

`dev`, the `dev → master` feature flow, and release-drafter-on-`master` are unchanged.
No `stage` branch is introduced.

## Consequences

- Every user — fresh clone or update — sits on an exact tagged release commit while
  remaining "on `master`," and the pyproject version at that commit equals its tag, so
  update detection and version-keyed migrations settle correctly.
- `reset --hard` discards modifications to *tracked* files (vs `pull`, which would
  conflict). User data is safe — config, databases, `.version.ini`, and untracked
  addon files are all gitignored or untracked, and `reset --hard` never removes
  untracked files.

## Considered alternatives

- **Branch-gated `master` / `stage` branch** — enforce "master only advances at
  release" via branch discipline. Rejected: tag-tracking enforces the invariant in
  code, so the extra branch carries no weight.
- **Updater derives version from `git describe` instead of pyproject** — only a
  partial fix; version-keyed migrations still read the pyproject version, so a stale
  tagged pyproject would misfire them.
