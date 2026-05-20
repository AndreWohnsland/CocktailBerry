# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  | Status   |
| -------------------------- | -------------------- | ---------------------------------------- | -------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  | new      |
| `needs-info`               | `incomplete`         | Waiting on reporter for more information | existing |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  | new      |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            | new      |
| `wontfix`                  | `wontfix`            | Will not be actioned                     | new      |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from the second column.

## Creating the new labels

The four "new" labels above don't exist on the GitHub repo yet. The first time a triage skill needs one, create it with `gh`:

```sh
gh label create needs-triage    --description "Maintainer needs to evaluate this issue" --color fbca04
gh label create ready-for-agent --description "Fully specified, ready for an AFK agent" --color 0e8a16
gh label create ready-for-human --description "Requires human implementation"           --color 0e8a16
gh label create wontfix         --description "Will not be actioned"                    --color cccccc
```

`incomplete` already exists on the repo and is reused for `needs-info` — don't create a duplicate.
