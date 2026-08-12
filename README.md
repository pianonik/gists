# gists

Claude Code skills, packaged as a
[plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins).
Twenty-one skills in five plugins.

They grew inside one large audio project and were then rewritten to hold no
knowledge of it. Every project-specific fact — build command, base branch,
commit-message style, tracker layout, test runner — is either detected from the
repo at run time or asked for once. Nothing is guessed. A skill that cannot work
out what it needs stops and says what the repo is missing.

## Installing

```
/plugin marketplace add pianonik/gists
/plugin install project-docs@pianonik-gists
```

Install whichever plugins you want; they don't depend on each other. `/plugin`
with no arguments shows what you have.

To install by hand instead, copy any `*/skills/<name>/` directory into
`~/.claude/skills/`.

## project-docs

A working loop for a project that keeps its state in three files at the repo
root: `history.md` (a running narrative log, newest first), `TODO.md` (open
work), and `README.md`.

| Skill | Does |
| --- | --- |
| `/wherex` | Reads all three and says where things stand. Read-only. |
| `/updatex` | Writes the session back into them, then trims the history to a rolling window — old entries move to `history-archive.md` rather than being deleted. |
| `/addtodo` | Files one item, routed to the section it belongs in. |
| `/planning-review` | Audits the planning docs against the actual code: what is built and verified versus only planned, doc drift, dead code by confidence, the open work buried among finished items. |
| `/verifytodo` | Checks the status markers against the real code and git log rather than trusting them. Work that verifiably shipped moves to `DONE.md`; anything ambiguous is reported rather than moved, and every move is listed so you can reverse it. |

## item-tracker

The same five for a project that tracks work as **one markdown file per item**
under `items/`, with the `status:` field as the source of truth and `TODO.md`
generated from it.

`/inititems`, `/whereitems`, `/additem`, `/updateitems`, `/verifyitems`,
`/planning-items-review`.

**Start with `/inititems`.** It creates the store, installs the two helper
scripts, and — if the repo already has a hand-edited `TODO.md` — converts each
entry into an item, asking you how to map the file's status markers rather than
guessing. It never edits or deletes the original: that gets renamed to
`TODO.legacy.md` with a banner, so you can compare the two and delete it
yourself once satisfied.

The file format is in
[item-tracker-plugin/ITEM-STORE-FORMAT.md](item-tracker-plugin/ITEM-STORE-FORMAT.md).

In a repo with no `items/` directory all five skills stop cleanly and point you
at the flat-`TODO.md` versions above, so installing this costs nothing either
way.

## worktree-batch

Git worktrees as disposable workspaces, and batches of unattended jobs that pile
their work onto a single branch.

`/mkwt <name>` makes a worktree at `<repo>/.claude/worktrees/<name>` on branch
`worktree-<name>` and moves the session into it. `/wtmerge` and `/fwtmerge` land
the work: commit locally, merge into the base branch inside the base branch's
own worktree, push the base branch. The feature branch is never pushed — only
the base branch is, so there is no remote-branch bookkeeping for something that
lives two days.

**`/sequencework`** is the ambitious one. It asks how many jobs you want and
what to pick them for, reviews the project, carves the findings into that many
jobs, and gets each one approved individually with a suggested model. Then it
runs them in sequence: each job cut from a `pending` branch, run headless,
fast-forward merged back into pending, its worktree deleted. One build at the
end with everything in it. You get one branch to review.

It records progress in a state file, so if the machine reboots mid-batch,
`run.sh --resume` picks up inside the interrupted job's surviving worktree
rather than starting over.

**`/projectreview`** is the lighter half. It reviews recent commits against the
tracker and writes — but does not run — a script that sets up one worktree per
follow-up job, each with a prompt written to stand alone in a fresh session. You
run them when you feel like it, or never.

## iterate

`/itrm` macOS, `/itri` connected iOS device, `/itrs` iOS Simulator, `/itrp`
macOS including audio-plugin formats.

They loop build, test, fix and keep going until the change works, rather than
stopping when it compiles. They refuse to drive an application with AppleScript
and refuse to screenshot with `screencapture`; verification goes through the
project's own test automation.

They need one target in your Makefile. `itr-info` prints `key=value` lines
saying what the build command is, how to launch the app so a script can drive
it, where the tests live, and so on. The full list and a copy-paste example are
in [iterate-plugin/README.md](iterate-plugin/README.md). If the target is
missing the skill asks once and offers to write it. It will not guess a build
command.

## dev-utils

`/commit` writes the message from the conversation rather than from reading the
diff, matches whatever commit-subject convention your log already shows, and
uses your repo's commit wrapper if it has one.

`/diskusage` surveys a Mac's disk in safety tiers and never deletes without
approval. Give it a keep-out list at `~/.claude/disk-keepout.md` and it will not
recommend touching anything on it.

## Two things worth knowing

**Nothing here assumes a particular project.** Base branch, tracker, build
command, commit convention — all detected from the repo or asked for once. Where
a skill cannot work something out it stops and says what is missing rather than
falling back to a default. That is deliberate: the alternative is an unattended
session confidently building the wrong target at three in the morning.

**[CONVENTIONS.md](CONVENTIONS.md)** states the working habits the skills were
built around — newest-first history files, local-only worktree branches, no
skill committing on your behalf, no caching without a measurement. You do not
have to adopt all of it, but a few are load-bearing and the skills say which.

## Contributing

Fork it and change what you like. If a skill assumes something it should have
detected, that is a bug worth reporting — open an issue saying which skill and
what it assumed.

[MAINTAINING.md](MAINTAINING.md) covers how this repo is edited and released.

## License

MIT. See [LICENSE](LICENSE).
