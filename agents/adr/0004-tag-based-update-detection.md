# Update detection from git tags, GitHub API only for release notes

## Context

`check_for_updates()` in `src/updater.py` asked the GitHub releases API which versions exist.
Unauthenticated API access is limited to 60 requests per hour per public IP.
Other devices behind the same router (for example a Home Assistant instance polling GitHub) can use up that budget.
Once the IP is over the limit, every request answers 403, including conditional requests with an ETag.
The affected machine then either reported an error or, with a cached response present, silently kept a stale release list and never noticed new releases.

ADR 0001 already made the tag the unit users track: the release drafter creates the tag when a release is published, and updating means moving the checkout to a tag.
So the tag set is a complete list of published releases, and the updater already runs `git fetch --tags` before every check.

## Decision

- **Detection reads the local tags after the fetch.** Every tag that parses as a version and is newer than the installed version is an available Update. No HTTP request besides git.
- **The fetch prunes tags.** `fetch(tags=True, prune=True, prune_tags=True)` keeps the local tag set identical to the remote, so a tag the release guard deleted again does not linger as a phantom release.
- **The GitHub API only supplies release notes, best effort.** It is called only when at least one newer tag exists. The ETag cache stays. When the request fails, the versions keep empty notes and each front end shows a fallback sentence; the check itself cannot fail because of the API any more.

## Consequences

- Update detection works on a network whose GitHub API budget is permanently exhausted. Only the notes degrade.
- An up-to-date machine makes no API call at all.
- A release is visible a minute or two before its web client asset is built, since the tag is created at publish time and the asset by a workflow afterwards. `update()` downloads the asset first and aborts cleanly if it is missing, so a user in that window retries a little later.
- Tags that exist only locally are deleted by every check. Installed machines have none.
- Pre-releases would need a tag convention that `Version` rejects or a filter; none exist today.

## Considered alternatives

- **Atom feed (`releases.atom`) as the release list.** No API quota, but only the ten newest entries, and notes arrive as HTML. Rejected: tags are already fetched and authoritative per ADR 0001.
- **`releases/latest` redirect as confirmation.** One extra request to protect against the seconds-long tag-then-delete window. Rejected in favour of pruning, which needs no second network source.
- **Optional GitHub token for a 5000 per hour budget.** Solves it for power users only and adds configuration. Rejected.
- **Drop release notes entirely.** Rejected: on most networks the API works and the notes are useful; the best-effort path keeps them at no cost to detection.
