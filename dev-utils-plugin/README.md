# dev-utils

Two skills that don't belong to a workflow.

## `/commit [message]`

Commits the session's work. The message is written from **what happened in this
conversation**, not from reading the diff — the conversation knows why a change
was made, and the diff doesn't.

What it does that a plain `git commit -am` doesn't:

- **Matches the repo's own commit-subject convention**, read live out of
  `git log`. A branch tag, a `type(scope):` prefix, a ticket id — whatever the
  last twenty commits consistently do, yours does too.
- **Uses the repo's own commit wrapper if it has one** — many projects have a
  script that stamps the subject, signs, pushes, or runs a formatter — and warns
  you if that wrapper pushes, before it pushes.
- **Handles nested independent repos.** If the session touched files in a
  sibling or nested checkout that the outer repo ignores, `git commit -a` in the
  outer one silently misses them. The skill finds them and commits each
  separately.
- **Recovers from a rejected push** by rebasing rather than leaving you to
  notice the failure scrolled past.

By default it sweeps everything modified, and says so. If you want a subset,
say which files.

## `/diskusage`

Surveys the Mac's disk and produces **prioritized, safety-tiered
recommendations** for reclaiming space. It defaults to analysis: nothing is
deleted or evicted until you approve a tier or specific items.

It knows the things that make disk cleanup on a Mac confusing:

- **A big directory is not automatically garbage.** It checks what something is
  before recommending anything, and asks about anything it can't classify.
- **Deleting on APFS often doesn't move the free-space number**, because a local
  snapshot still references the blocks. The space is *purgeable* rather than
  free. The skill explains this every time rather than letting you think the
  delete failed.
- **Cloud-storage folders can be made online-only** — visible in Finder, present
  in the cloud, just not taking local space. Usually the single biggest lever,
  and reversible, which is why it ranks above deletion.

### Tell it what not to touch

Write `~/.claude/disk-keepout.md` — a plain list, one item per line, of paths
that must never be recommended for deletion, with a word about why:

```
~/Backups/server        live backup, runs nightly via launchd
~/Library/Application Support/MobileSync/Backup   device backups, keep
~/Dropbox/Work          in use; online-only at most, never delete
```

The skill reads it first. Without it, the skill asks before recommending
anything it can't prove is regenerable — which is safe but slower, and the same
questions every time.
