---
name: updatex
description: Update history.md, TODO.md, and README.md in the current working directory to reflect the work done in the current conversation, then trim history.md to a rolling window. Use when the user says "updatex", "/updatex", or otherwise asks to record the session into those files. ONLY for a repo whose tracker is a hand-edited TODO.md: if the repo has an items/ store (items/*.md with items/scripts/itemlib.py), stop and use /updateitems instead, even when a TODO.md also exists — a stale hand-authored TODO.md often sits alongside a live item store.
tools: Read, Edit, Write, Bash
---

# updatex

Record the work done in the current conversation into the three canonical
project files. Mirror image of `/wherex` — that one *reads* history.md /
README.md / TODO.md to orient; this one *writes* them to record.

## Step 0 — check for an item store FIRST (mandatory)

Before touching `TODO.md`, before anything else:

```bash
ls items/scripts/itemlib.py 2>/dev/null; ls items/*.md 2>/dev/null | head -3
```

If either produces output, this project's tracker is the **item store**, not
`TODO.md`. **Stop and tell the user to run `/updateitems` instead.** Do not edit
`TODO.md`.

This check is unconditional and comes first. It is NOT conditional on `TODO.md`
being missing — a repo can have both: a live `items/` store *and* a stale
hand-authored `TODO.md` still sitting at the repo root from before the store
existed, large and entirely plausible-looking. Writing this session into that
file records it somewhere nobody reads, and the real tracker never learns the
work happened. **The presence of `TODO.md` proves nothing. The presence of
`items/` is decisive.**

The same applies to a `TODO.md` that is *generated* from the store: it carries a
"do not hand-edit" line, and any edit is destroyed by the next export.

## What to update

In the current working directory, in this exact order:

1. **`history.md`** — add one or more dated entries at the TOP (newest first).
2. **`TODO.md`** — mark completed items finished with a date; add follow-ups the
   conversation surfaced; leave the structure and ordering as found.
3. **`README.md`** — only if substantive architecture, concepts, or workflows
   changed. Most conversations don't need a README touch.

If any of these is missing, note it and continue with the rest. Do NOT create
one from scratch unless the user explicitly asks — the project may legitimately
not have it.

## Gathering facts (do this BEFORE writing)

Don't write from memory alone — the conversation may have been compacted and
details drift. Pull facts from authoritative sources:

- **`git log --oneline -20`** — recent commits in this session. Each commit
  message is the canonical record of what changed and why.
- **`git log -p <commit>`** for the specific commits the conversation touched, to
  recover file specifics that may have fallen out of context.
- **`git diff HEAD~N`** to see the cumulative effect of several commits at once.
- **`date +%Y-%m-%d`** for today's date — never trust a date from earlier in the
  conversation; sessions can span midnight.

If git isn't available or the work is uncommitted, fall back to the conversation
context, but flag the entry as "(uncommitted)" so it's clear the record may
shift.

## How to write each file

### history.md

- **Newest entries at the top.** This is what the trimmer below depends on.
- **Heading format**: `## YYYY-MM-DD (time-of-day or qualifier) — short summary`.
  Read the current top entry first and match the prevailing style.
- **Body voice**: technical, narrative, mid-length. Cite file paths when
  referencing code. Quote commit short-hashes when the conversation produced
  commits.
- **One entry per logical chunk of work** — if the session bundled three
  features that landed in three commits, write three entries (or one entry with
  three sections), matching what the existing file does.
- **Don't duplicate commit messages verbatim** — those live in `git log`. The
  history entry is the *narrative around* the commits: why this came up, what
  was tried, what was decided, what's still open.
- **After prepending, trim `history.md` to a rolling window** so it never grows
  to megabytes. Older entries are MOVED, never deleted, into
  `history-archive.md`. The trimmer ships with this skill:

  ```bash
  python3 "$CLAUDE_PLUGIN_ROOT/skills/updatex/trim_history.py"        # 7-day window
  python3 "$CLAUDE_PLUGIN_ROOT/skills/updatex/trim_history.py" 30     # 30 days
  ```

  If `$CLAUDE_PLUGIN_ROOT` is not set (the skill was copied into
  `~/.claude/skills/` by hand rather than installed as a plugin), the trimmer is
  at `~/.claude/skills/updatex/trim_history.py`. Run it from the repo root — it
  operates on `./history.md`.

  It splits on `## YYYY-MM-DD` headings, keeps sections newer than the cutoff,
  prepends the rest to `history-archive.md` (both stay newest-first), preserves
  content exactly, never reorders within a group, and does nothing when nothing
  is stale. If it reports that `history-archive.md` is NEW and untracked, run
  `git add history-archive.md` so the next commit includes it (`git commit -a`
  skips untracked files) — but still don't commit.

### TODO.md

- Read the whole file first, and match its existing structure and markers
  — whatever they are. Don't impose a new scheme.
- For each item the conversation finished: change its status marker the way the
  file already does it (an inline `[FIXED <date>]`, a move to a "landed"
  section, a checkbox — copy the neighbours), and append a one-sentence
  reference to the commit that did it.
- For new items the conversation discovered — open follow-ups, deferred work,
  regressions — add them under the appropriate section, matching neighbouring
  formatting. Include enough context that this is pickup-able cold.
- **Don't delete entries** unless the user asks. Completed entries usually stay,
  marked finished, as a record.

### README.md

- Skip unless the conversation introduced something the README's structure
  currently misses: a new subsystem, a new build target, a new convention, a new
  external dependency, a new file-format invariant, or an architectural change.
- A bug fix, a parameter tuning, or a refactor that doesn't change the concept
  model does NOT warrant a README touch.
- When you do touch it, find the most relevant existing section and extend it.
  Don't add a new top-level section unless the change is genuinely new
  architecture.

## When to stop

After the three files are updated, stop. **Don't commit** — that's a separate
step the user will ask for explicitly. Report what changed in one or two
sentences, and say so if you skipped a file.

## Don't

- Don't write fabricated facts. If you're unsure whether something is in the
  commit, check `git log` / `git diff`.
- Don't reorder existing history entries — only prepend. (The trimmer relocating
  old entries into the archive is not reordering; it preserves order exactly.)
- Don't truncate or summarize existing TODO entries while editing — preserve
  them.
- Don't `git add` or commit the doc edits. **Sole exception:** a *newly created*
  `history-archive.md` must be `git add`ed, because `git commit -a` silently
  skips untracked files and the archive would be lost. Staging that one new file
  is not committing.
