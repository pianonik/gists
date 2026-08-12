# gists

Claude Code skills shared from Nick Porcaro's setup, packaged as a
[plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins).

These grew inside one large audio project and were then rewritten to hold no
knowledge of it. Every project-specific fact — build command, branch name,
commit-message style, tracker layout, test runner — is now either detected from
the repo at run time or asked for once. Nothing is guessed. A skill that cannot
work out what it needs stops and says exactly what the repo is missing.

## Install

```
/plugin marketplace add pianonik/gists
/plugin install project-docs@pianonik-gists
```

Then `/wherex`, `/updatex`, and so on. `/plugin` with no arguments lists what is
installed.

To install by hand instead, copy any `*/skills/<name>/` directory into
`~/.claude/skills/`.

## The plugins

### project-docs

A working loop for a repo whose state lives in three files at the root:
`history.md` (a running narrative log, newest first), `TODO.md` (open work), and
`README.md`.

| Skill | Does |
| --- | --- |
| `/wherex` | Reads all three, tells you where the project stands. Read-only. |
| `/updatex` | Writes the current conversation back into all three, then trims `history.md` to a rolling window (older entries move to `history-archive.md`, never deleted). |
| `/addtodo` | Drops one new item into `TODO.md`, routed to the section it actually belongs in. |
| `/planning-review` | Audits the whole project: docs against code, dead code, stale items, what is really built versus only planned. |
| `/updateplan` | Re-derives a `TODO-parallel.md` structural plan from `TODO.md`, verifying every status claim against the code and git log first. |

### item-tracker

The same loop for a repo that tracks work as **one markdown file per item**
under `items/`, where each file's `status:` field is the open/done state and
`TODO.md` / `DONE.md` are generated views. See
[item-tracker-plugin/ITEM-STORE-FORMAT.md](item-tracker-plugin/ITEM-STORE-FORMAT.md)
for the format and the two helper scripts a repo must provide.

`/whereitems`, `/additem`, `/updateitems`, `/updateitemplan`,
`/planning-items-review` — the item-store counterparts of the five above. Each
one checks for the store first and sends you to the flat-`TODO.md` sibling if
there isn't one.

### worktree-batch

Git worktrees as disposable workspaces, and batches of unattended jobs that
accumulate on one branch.

| Skill | Does |
| --- | --- |
| `/mkwt <name>` | Creates a worktree at `<repo>/.claude/worktrees/<name>` on branch `worktree-<name>`, and moves the session into it. |
| `/wtmerge` | Commits the worktree branch locally, merges it into the base branch and pushes the base branch, then merges the base branch back down. |
| `/fwtmerge` | The same, forward only — no merge back down. |
| `/projectreview` | Reviews recent commits across one or more repos against the tracker, then writes (does not run) a script that sets up one worktree per follow-up job, each with a prompt a fresh session can act on cold. |
| `/sequencework` | Reviews the project, gets a small number of jobs approved one at a time, then runs them in sequence — each in its own worktree, each fast-forward merged into a single `pending` branch. Resumable after a kill. |

### iterate

Build → test → fix loops that keep going until the change actually works, rather
than stopping when it compiles. Testing goes through the project's own
automation; screenshots go through the project's own capture path, never through
desktop screen-scraping.

`/itrm` (macOS), `/itri` (connected iOS device), `/itrs` (iOS Simulator),
`/itrp` (macOS including audio-plugin formats).

These read one declared Makefile target, `itr-info`, for the commands they need.
See [iterate-plugin/README.md](iterate-plugin/README.md) — it is about eight
lines to add to a repo, and the skill offers to write them for you.

### dev-utils

| Skill | Does |
| --- | --- |
| `/commit` | Commits the session's work, matching whatever commit-subject convention the repo's own log shows. Uses the repo's commit wrapper script if it has one. |
| `/diskusage` | Surveys a Mac's disk and recommends what to delete, compress, or make online-only, in safety tiers. Never deletes without approval, and reads a user-supplied list of things that must not be touched. |

## Conventions these assume

[CONVENTIONS.md](CONVENTIONS.md) states the working habits the skills were built
around — fail loud rather than degrade, newest-first history files, local-only
worktree branches, never commit on the user's behalf. Worth a read before
adopting them; several skills refer to it.

## License

MIT. See [LICENSE](LICENSE).
