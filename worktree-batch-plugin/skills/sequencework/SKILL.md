---
name: sequencework
description: Works on ANY git repo. Ask up front how many jobs the batch should be and what to pick them for (critical bug fix / critical feature fix / critical feature addition / low risk and easy), review the project with /planning-items-review or /planning-review, carve the findings into that many worktree jobs, get each one approved ONE AT A TIME (worktree name, goal, justification, suggested model), then generate and run a script that runs the jobs IN SEQUENCE — each job's branch cut from a `pending` worktree, fast-forward merged back into it when it finishes, its tracker item flipped to awaiting-review, its worktree deleted — and builds once at the end with every merge in it. Refuses to start if a `pending` worktree already exists. The generated runner records progress in a state file and is resumable with --resume after a kill or shutdown, including mid-job. Base branch, tracker, build command and commit convention are all detected per repo, never assumed. Use when the user says "sequencework", "/sequencework", or asks to review-then-run a queued batch of worktree jobs that accumulate into one branch.
tools: Read, Bash, Grep, Glob, Write, Agent, AskUserQuestion, Skill
---

# sequencework

Turn a project review into a queue of unattended jobs that run one after another
and pile up on a single branch.

The shape, end to end:

1. Refuse to start if a `pending` worktree or `worktree-pending` branch exists.
2. Ask **how many jobs** the batch should be, and **what they should be picked
   for**, before doing any work.
3. Review the project, read-only.
4. Carve the findings into at most that many jobs — each one a worktree name, a
   goal, the tracker item(s) it covers, a justification, and a suggested model.
5. **Approve them one at a time.** Nothing is created until every job has been
   accepted, edited or skipped, and the final order confirmed.
6. Generate a runner script and run it.
7. The script creates the `pending` worktree first, then for each job in order:
   cuts the job branch **from pending's current tip**, runs one headless session
   in it, fast-forward merges it back into pending, flips that job's tracker
   item(s) to awaiting-review, and deletes the job worktree.
8. After the last job, one build in the pending worktree, containing every
   merge.

`pending` is the whole point: at the end there is exactly one branch holding
everything, sitting in a worktree, waiting for the user to look at it and land
it with `/fwtmerge`. This skill never touches the base branch and never pushes.

## Why jobs are cut from pending, not from the base branch

A fast-forward merge only exists when the branch being merged is a straight-line
descendant of the target. Cutting job N from `worktree-pending`'s tip — *after*
job N−1 has merged — is what makes `git merge --ff-only` always succeed. Cutting
everything from the base branch would fast-forward exactly once and then fail.

This has a second effect worth using deliberately: **each job sees every earlier
job's work already in its tree.** Ordering is a tool, not a limitation — put the
job that lays groundwork first and say in the later prompt that it can rely on
it. It also means one job's mistake is visible to the next, so say in the prompt
if a job should not build on something.

## This skill is repo-neutral — work out the conventions, don't assume

It runs anywhere. All it truly needs is a git repo, the `claude` CLI, and
worktrees. Everything else is **detected per repo** in step 0 and carried
through. Never hardcode one project's answer into a generated script or prompt.

| What | How to settle it |
| --- | --- |
| Base branch | `git symbolic-ref --short refs/remotes/origin/HEAD` if it resolves, else `master` if it exists, else `main`. This is `BASE`. |
| Tracker | `items/*.md` plus `items/scripts/itemlib.py` → item store. Else a hand-authored `TODO.md`. Else no tracker. |
| Review skill | Item store → `/planning-items-review`. Otherwise → `/planning-review`. |
| Build command | Ask the user in step 4; propose what the repo actually uses — a target from `make help`, a `package.json` script, the README's build line. |
| Commit convention | Match the repo's own `git log` subjects. Reproduce any consistent prefix; keep it plain if they are plain. |
| Iteration skill | Only name one that is installed on this machine and suits this repo. Otherwise spell out the repo's own build → test → fix commands. |
| Job environment | Only what this repo's unattended jobs need — for instance an environment variable that enables a test-control interface so a launched app can be driven by script. Usually empty. |
| Process discipline | Whatever the repo's own docs mandate. Some projects forbid killing processes by name pattern because several checkouts build identically-named binaries; if so, use the repo's own tool. |

Read the repo's `CLAUDE.md` and `AGENTS.md` before writing any prompt — that is
where these conventions live, and a prompt contradicting them will have an
unattended session doing the wrong thing all night with nobody watching.

**Without a tracker the batch still runs.** Every step works the same except the
status flip, which has nothing to write to. Say that out loud in step 1 and
again in the final confirmation: the work will land on `pending` and be recorded
nowhere but the log and the commits. Do not invent a tracker to fill the gap.

## Step 0 — the refusal check, FIRST

Before the review, before anything. The review takes real time; do not spend it
and then discover the batch can't run.

```bash
MAIN=$(git worktree list --porcelain | awk '/^worktree /{print substr($0,10); exit}')
[ -n "$MAIN" ] || { echo "BLOCKED: not in a git repo"; exit 1; }
echo "main=$MAIN"
[ -e "$MAIN/.claude/worktrees/pending" ] && echo "BLOCKED: worktree dir 'pending' exists"
git -C "$MAIN" show-ref --verify -q refs/heads/worktree-pending && echo "BLOCKED: branch worktree-pending exists"
command -v claude >/dev/null || echo "BLOCKED: the 'claude' CLI is not on PATH"

# repo conventions -- carried through every later step, never assumed
BASE=$(git -C "$MAIN" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
[ -n "$BASE" ] || { git -C "$MAIN" show-ref -q --verify refs/heads/master && BASE=master || BASE=main; }
git -C "$MAIN" rev-parse -q --verify "$BASE" >/dev/null || echo "BLOCKED: base ref '$BASE' does not exist"
if   [ -f "$MAIN/items/scripts/itemlib.py" ];           then TRACKER=items
elif [ -f "$MAIN/TODO.md" ] || [ -f "$MAIN/TODO.txt" ]; then TRACKER=todo
else                                                         TRACKER=none; fi
echo "base=$BASE tracker=$TRACKER"
git -C "$MAIN" --no-pager log --oneline -5      # the commit-subject convention to match
```

If anything is BLOCKED, **stop the whole skill** and say why in one paragraph.

For an existing `pending`, do not offer to delete it and do not delete it — it
holds work somebody has not reviewed. Print the two commands the user would run
themselves once they have landed it:

```
git -C "$MAIN" worktree remove "$MAIN/.claude/worktrees/pending"
git -C "$MAIN" branch -d worktree-pending
```

Also report — but do not abort on — a dirty main worktree. The batch cuts from
the committed tip of `$BASE`, so uncommitted changes there simply won't be in
it, and the user should know that before jobs start.

Report the detected conventions in one line before going on — base branch,
tracker kind, commit-subject convention — so a wrong guess is caught here and
not at three in the morning.

## Step 1 — bound the batch, before any work

Ask both questions in ONE AskUserQuestion call, before the review. The answers
bound everything that follows, and asking after a review has already carved
eleven jobs wastes the review.

**Question 1 — "How many jobs should this batch run?"** Offer `2`, `3`
(recommended), `1`, `5`; "Other" takes any number. Say in the descriptions what
a number costs: the jobs run one after another, so five jobs is five sittings of
wall-clock time back to back, and every one is merged into the same branch
before the user sees any of it.

**Question 2 — "What should the jobs be picked for?"** `multiSelect: true`:

- **Critical bug fix** — something is wrong now: a crash, a wrong result, a gate
  that fails or was weakened.
- **Critical feature fix** — a shipped feature that doesn't do what it claims,
  or only does it on one platform or one path.
- **Critical feature addition** — something the project needs and has never had.
- **Low risk and easy** — small, well-specified, self-contained. Good for
  filling out a batch, or for a run where nothing should be at stake.

"Other" takes free text; treat it as the selection filter verbatim.

If step 0 found **no tracker**, say so in this same message: nothing will be
flipped to awaiting-review, and the batch's only record will be the commits on
`pending` and the logs.

If the user picks several, spread the jobs across what they picked and label
each job with which one it satisfies. If the argument after `/sequencework`
named a focus area, that narrows *where* to look; these answers decide *what
kind* of work and *how much*.

Carry both answers into steps 3 and 4, and repeat them in the final
confirmation so the user can see what they asked for against what they got.

## Step 2 — the review

Run the review skill that matches the tracker step 0 found, with the Skill tool:
an item store → `planning-items-review`; anything else → `planning-review`. If
neither is installed, do the review directly: read the tracker, the docs and the
git history, and fan out read-only agents comparing the docs against the source.
The review is a prerequisite either way, not an optional preamble.

Review the whole project — a finding outside the criteria is still worth
knowing. The step 1 answers filter the *carving*, not the *looking*. Where the
fan-out has a choice about depth, spend it on the areas the criteria points at.

Take from it: the true state of each in-flight item, status drift, doc drift,
dead code by confidence, and the genuinely open work list. Keep the report; the
justifications in step 4 are quotations from it, with file references and item
ids.

## Step 3 — carve the jobs

**At most the number agreed in step 1, and only work meeting the criteria agreed
in step 1.** Two rules follow, and they matter more than the carving heuristics:

- **Don't pad.** If only two findings clear the bar and the user asked for five,
  propose two and say why there aren't five. A padded batch spends a night of
  unattended sessions on work nobody asked for.
- **Say what you left out.** After the approved sequence, list in one or two
  lines the findings that would have made good jobs but didn't fit the count or
  the criteria, so the user can raise the number if they want them.

Then the ordinary carving rules:

- One worktree per theme a single session can hold in its head. Two unrelated
  mental models is two jobs.
- Size for one sitting. A finding too big for one job is a candidate to drop,
  not a reason to exceed the count — say it's too big and needs its own batch.
- **With a tracker, every job must name the item(s) it covers**, by id. That is
  what gets flipped afterwards. A job covering no item is allowed, but say so at
  approval time: nothing will be flipped for it, and the work will be invisible
  in the tracker. With no tracker, every job is in that position; say it once
  and move on.
- **Order them.** Groundwork first, dependants after, tracker and history sweeps
  last. Say in each job's justification what earlier job it relies on, if any.
- **At most ONE job may touch shared code that lives OUTSIDE this repo** — a
  sibling checkout, a linked package, a submodule the worktree does not
  duplicate. Say so in that job's prompt: the change lands in the shared
  checkout, every worktree sees it immediately, and **the pending branch does
  not carry it**. The final build will include it; the merge will not.
- Name each in kebab-case: `<name>` → branch `worktree-<name>` at
  `.claude/worktrees/<name>`.

For each job, also pick a **model** and be able to say why in one line. Check
what the installed CLI advertises (`claude --help`) and pass an alias, not a
dated model id. Suggest the strongest model for anything needing judgment —
ambiguous specs, cross-cutting refactors, debugging with an unknown cause — and
a cheaper one for narrow, fully-specified, mechanical work where the finding
already says exactly what to change. Do not claim a model is "better at"
something you can't support; the user overrides this at approval anyway.

## Step 4 — approve ONE AT A TIME

This is the part the skill exists for. Do not batch it into one big yes/no.

For each job, in the order you propose to run them, print this block, then call
**AskUserQuestion** for that job alone:

```
Job <i> of <n>:  <name>            (branch worktree-<name>)
KIND         <which step-1 criterion this satisfies>
GOAL         <one or two sentences: what is TRUE when this is done>
ITEMS        <id> — <title>            [what gets flipped afterwards]
WHY          <the finding, quoted: file / symbol / SHA / item id>
DEPENDS ON   <earlier job name, or "nothing — could run first">
MODEL        <alias> — <one line of why>
```

The AskUserQuestion call asks two questions:

1. *Run this job?* — **Approve** (recommended) / **Skip it** / **Change the
   goal**. "Other" gives free text; treat it as the replacement goal or as an
   instruction to re-scope, and re-present the job once before moving on.
2. *Which model?* — your suggestion first, labelled "(Recommended)", then the
   other aliases.

Carry the answers forward. Do not re-ask an approved job.

When every job has an answer, print the final sequence — number, name, kind,
model, items, one-line goal — with the step 1 answers restated above it
(`asked for: 3 jobs, critical bug fix + low risk and easy` / `proposing: 2`),
and the one or two lines of what you left out. Then ask once more, in a single
AskUserQuestion:

- *Start the batch?* — **Start now** / **Start after a delay** / **Write the
  script but don't run it** / **Cancel**.
- *Final build?* — the command to run in `pending` once everything is merged.
  Propose what **this** repo actually uses, named from its own `make help`,
  `package.json` or README rather than guessed, and say in the description if it
  launches something. Always offer "no build" as well — some repos have nothing
  worth building unattended.

Say plainly, before that question: nothing has been created yet, and cancelling
here leaves the repo exactly as it was.

## Step 5 — generate the script

Write to
`${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/sequencework}/out/<YYYY-MM-DD-HHMMSS>/`:

- `run.sh` — the batch runner, jobs baked in, no prompting.
- `<name>.prompt.md` — one per job.
- `review.md` — the review report, so the batch is auditable later.

`run.sh` requirements. Use `set -u`; macOS ships bash 3.2, so guard
`${#arr[@]}` before expanding any array.

0. Bake the step 0 findings in as literals at the top — `BASE`, `TRACKER`, the
   commit-subject convention, the build command, the per-job environment. The
   script must not re-derive them and must not carry another project's
   defaults.
1. Resolve `MAIN` from `git worktree list --porcelain`, which works from inside
   a worktree. Guard that it is the intended repo: check a path only this repo
   has, and bake in the expected repo root, failing with the `cd <repo> && …`
   fix spelled out if not. Running a batch against the wrong checkout is the one
   mistake nothing downstream can undo.
2. Re-run the step 0 refusal check. A batch generated an hour ago must not stomp
   on a `pending` created since.
3. Ensure both exclusions are in
   `$(git rev-parse --git-common-dir)/info/exclude` — `**/.claude/worktrees/`
   and `.worktree-prompt.md`. Per-clone, not versioned, so check every time. The
   second matters: inside a linked worktree the prompt file sits at the repo
   root, and a job committing with `git add -A` would otherwise drag it onto the
   branch.
4. Create pending **first**, from the base branch step 0 resolved:
   `git -C "$MAIN" worktree add -b worktree-pending "$WTROOT/pending" "$BASE"`,
   then the LFS smudge check below — skip that check entirely in a repo that
   doesn't use LFS.
5. Define the repo's commit-subject convention **once**, as a function, since
   the batch commits on two different branches and some conventions name the
   branch the work lands on:

```bash
# a convention that tags the branch:
subject() { printf '<prefix>%s %s' "$1" "$2"; }
# most repos -- the message, nothing prepended:
# subject() { printf '%s' "$2"; }
```

6. Then, per job, in order — the fragments that are easy to get wrong:

```bash
# (a) cut the job branch from pending's CURRENT tip -- this is what makes the
#     merge in (c) a fast-forward, and what lets this job see earlier work.
git -C "$MAIN" worktree add -b "worktree-$name" "$dir" worktree-pending || exit 1

# LFS: rows whose second column is '-' are un-smudged pointers -- the build
# would link a text stub. TMPDIR must be on the repo's own filesystem or
# git-lfs fails with 'cross-device link'.
if git -C "$dir" lfs ls-files 2>/dev/null | awk '$2 == "-"' | grep -q .; then
  mkdir -p "$GITCOMMON/lfs/tmp"
  TMPDIR="$GITCOMMON/lfs/tmp" git -C "$dir" lfs pull || echo "WARNING: lfs pull failed"
fi

cp "$OUTDIR/$name.prompt.md" "$dir/.worktree-prompt.md" || exit 1

# (b) one unattended session. stdin from /dev/null so it can never block on the
#     terminal. $JOB_ENV is whatever THIS repo's jobs need, decided in step 0.
#     Usually empty -- but still DEFINE it (JOB_ENV=""), because set -u makes an
#     unset variable fatal.
BEFORE=$(git -C "$PENDING" rev-parse HEAD)
( cd "$dir" && env $JOB_ENV \
    claude -p --dangerously-skip-permissions --model "$model" \
      "$(cat "$dir/.worktree-prompt.md")" ) </dev/null 2>&1 | tee "$log"
rc=${PIPESTATUS[0]}

# sweep anything the session left uncommitted (add -A picks up new files; build
# output is gitignored). Plain git commit, subject matching THIS repo's
# convention -- never a wrapper that pushes, because these branches are local.
if [ "$rc" -eq 0 ] && [ -n "$(git -C "$dir" status --porcelain)" ]; then
  git -C "$dir" add -A
  git -C "$dir" commit -m "$(subject "worktree-$name" "$name: sweep uncommitted work")"
fi

# (c) fast-forward into pending. A failure here is a real logic error --
#     something moved pending behind our back. Stop the batch.
git -C "$PENDING" merge --ff-only "worktree-$name" || { echo "FF MERGE FAILED"; exit 1; }
AFTER=$(git -C "$PENDING" rev-parse HEAD)
```

```bash
# (d) ITEM-STORE REPOS ONLY. Flip this job's items to pending-review -- and ONLY
#     if the merge actually advanced pending. A job that produced no commits has
#     nothing to review, and marking its item would be a lie.
#     Omit this whole block from the generated script when TRACKER != items.
if [ "$AFTER" != "$BEFORE" ] && [ -n "$items" ]; then
  ( cd "$PENDING" && python3 - $items <<'PY'
import datetime, os, sys
sys.path.insert(0, "items/scripts")
import itemlib as il
today = datetime.date.today().isoformat()
for iid in sys.argv[1:]:
    path = os.path.join(il.ITEMS_DIR, iid + ".md")
    fm = il.load_item(path)              # raises if the id is wrong -- good
    old = fm["status"]
    if old == "pending-review":
        print(f"{iid}: already pending-review"); continue
    fm["status"] = "pending-review"
    fm["updated"] = today
    il.write_item(il.ITEMS_DIR, fm, fm["body"])
    print(f"{iid}: {old} -> pending-review")
PY
    python3 items/scripts/export_todo.py
    git add items
    git diff --cached --quiet || \
      git commit -m "$(subject worktree-pending "items: $items -> pending-review after $name")" )
fi

# (e) the worktree has served its purpose -- its work is in pending.
git -C "$MAIN" worktree remove "$dir" \
  && git -C "$PENDING" branch -d "worktree-$name" \
  || echo "WARNING: could not remove $dir -- left in place, remove it by hand"
```

`itemlib.ITEMS_DIR` is derived from the module's own location, so running it
from inside `$PENDING` edits **pending's** copy of the store. That is correct by
construction — do not pass a path.

`branch -d` (lowercase) refuses an unmerged branch, which is the safety net: run
it with `-C "$PENDING"` so "merged" is measured against pending's HEAD. Never
`-D`, never `worktree remove --force`.

7. On a **non-zero session exit**: do not merge, do not flip, do not delete —
   stop the whole batch and report, because everything downstream is cut from
   pending and the state is uncertain. Accept a `--keep-going` flag that moves
   to the next job instead. That is safe: the next branch is cut from pending,
   which simply lacks the failed job's work.
8. After the last job, the build the user approved, run **in the pending
   worktree**, with every merge in it:

```bash
( cd "$PENDING" && $BUILD_CMD ) 2>&1 | tee "$LOGDIR/build.log"
brc=${PIPESTATUS[0]}
```

   Take the exit status from `PIPESTATUS`, never from the pipe — `cmd | tee`
   reports the *tee's* status, and a failed build then reads as success. Print
   where the artifact landed. If the command also launches something, say that a
   window appearing is not by itself proof the new binary ran; on macOS, `open`
   activates an already-running instance of the same bundle id if one exists.
9. Accept `--dry-run`: print the plan, create nothing, exit 0.
10. **Survive interruption — the batch must be resumable after a kill or a
    shutdown.** Three pieces, all mandatory in the generated script:

    - **A state file, `$LOGDIR/state`.** Append one line per event as it
      happens: `start <name>`, `done <name>` (only after that job's merge, item
      flip and worktree removal have all finished), `failed <name> exit-<rc>`,
      `build exit-<rc>`. The session log is NOT a substitute: `claude -p` prints
      nothing until the session ends, so a killed job's log is empty — the state
      file and the worktree's own `git log` are the only record of where the
      batch died.
    - **`--resume` (no argument).** Reads the state file: every job with a
      `done` line is skipped; the first job without one is the resume point.
      Expects `pending` to exist; refuses if there is no state file. Keep
      `--resume-from <name>` as the manual override. Both skip the step 0
      refusal check — and when a plain invocation is BLOCKED by a `pending` that
      this batch's own state file accounts for, say to use `--resume` rather
      than only refusing.
    - **The interrupted-job path.** On resume, if the resume-point job's
      worktree already exists, do NOT `worktree add` — it would fail — and do
      NOT re-run the prompt as if from scratch. Run a fresh session in the
      existing worktree with the original prompt prefixed by an interruption
      preamble: a previous unattended session on this job was interrupted, its
      committed and uncommitted work is already in this worktree, verify every
      DONE WHEN line against what is actually there and finish only what is
      missing. Then the normal sweep, merge, flip and remove. The DONE WHEN
      lines are what make this correct by construction: whether the dead session
      had finished is checkable, so nothing is assumed either way.

    Print the resume command — the absolute path to `run.sh` plus `--resume` —
    in the startup banner and again in every job header, so whoever finds the
    machine after a reboot has the recovery in front of them.
11. Report progress with `echo`, not `#` comments. Final report: per job (exit
    code, merged yes/no, items flipped, worktree removed yes/no), pending's SHA
    and `git --no-pager log --oneline` since base, the build result, the log
    directory, and the landing instruction — `cd` into the pending worktree,
    then `/fwtmerge`, or the plain merge the repo normally uses. Plus one line:
    `worktree-pending` is local-only; never push it.

`bash -n` the script and run it with `--dry-run` before doing anything else. A
generated script that fails on first use is worse than no script.

## The prompt files

Each must stand alone: assume the session reading it has never seen the review,
and that nobody is watching — it runs unattended with permissions bypassed, so
anything left implicit will not get asked about.

Open with these three blocks, in this order, before any detail:

1. **`## GOAL`** — one or two sentences saying what is *true* when the job is
   finished. A state, not a task list.
2. **`## DONE WHEN`** — checkable lines that add up to the goal, each one
   something a session can look at and answer yes or no to, naming the actual
   command that settles it in **this** repo.
3. **`## HOW TO WORK`** — the build → test → fix loop in this repo's own terms.
   Name an iteration skill only if one is installed and fits the platform;
   otherwise write out the commands. Then, in these words: **stay in the loop
   until every line above is true, and do not stop at the first green run.**
   Then: if a DONE WHEN line turns out to be wrong or impossible, say so plainly
   and stop — do not quietly drop it and report success on the rest.

Then a `---` rule, then the detail — and these batch-specific rules, which a
fresh session cannot guess and which are the difference between a clean merge
and a mess:

- **Commit locally, on this branch, and nothing else.** Plain `git commit`, with
  a subject matching this repo's convention — spell the convention out. **Do not
  use a wrapper that pushes**; name it if the repo has one. Do not push. Do not
  merge into the base branch. Do not run `/wtmerge` or `/fwtmerge`. The batch
  fast-forward merges this branch into `pending` when the session exits.
- **This worktree is deleted after the merge.** Anything not committed is gone.
- **Do not touch the `pending` worktree** or any other worktree.
- **Do not edit any tracker item's status** — the batch flips the covered items
  after the merge. Improving an item's *body* is fine.
- **Earlier jobs' work may already be in your tree** — this branch was cut from
  pending after they merged. Name the earlier job if this one builds on it.
- The house rules a fresh session won't recall, quoted from **this** repo's
  `CLAUDE.md` or `AGENTS.md` rather than from memory. Go and read them.
- What is deliberately **out of scope**, so the next job doesn't redo it.

## Step 6 — run it

Unless the user chose "write the script but don't run it": start `run.sh` with
the Bash tool and **`run_in_background: true`** — a multi-hour batch will blow a
foreground timeout — then report the log directory and stop the turn. The
harness re-invokes the session when it exits.

One caveat at kickoff, in one line: the batch lives inside this session, so
closing the session kills it; the alternative is to paste the printed command
into a terminal and let it run there. Add that a kill is recoverable either way:
`run.sh --resume` continues from the state file, re-entering an interrupted job
in its surviving worktree. If the user asked for a delay, put the `sleep` inside
the backgrounded run (`sleep N && ./run.sh`) and say the wall-clock start time;
nothing is created during the wait.

When it finishes, read the logs and report: what merged, what didn't, which
items are now awaiting review, the build result, and the single next action —
review `pending`, then `/fwtmerge` from inside it. Do not land it yourself.

## Don't

- Don't assume any particular project. Every project-specific name in this file
  is an example of a convention to look up, not a default to reach for.
- Don't go forward when a `pending` worktree or `worktree-pending` branch
  exists, and don't delete one to make room. That is the user's call and their
  unreviewed work.
- Don't cut job branches from the base branch — the fast-forward merges depend
  on cutting from pending's tip.
- Don't skip the two bounding questions, and don't ask them after the review —
  an unbounded batch is what this skill exists to prevent.
- Don't exceed the agreed number of jobs, and don't pad to reach it.
- Don't approve jobs in bulk. One at a time, with a justification and a model.
- Don't create anything before the final confirmation — up to that moment,
  cancelling must leave the repo untouched.
- Don't push anything: not the job branches, not `worktree-pending`, not the
  base branch.
- Don't use a commit wrapper that pushes anywhere in the batch, and don't merge
  into the base branch.
- Don't mark a tracker item fully done, and don't flip an item for a job that
  produced no commits. In a repo with no tracker, don't invent one.
- Don't `worktree remove --force` or `branch -D`.
- Don't take a build's exit status from a pipe.
- Don't read an empty job log as "the job did nothing" — `claude -p` buffers all
  output until the session exits, so a killed job's log is always empty. The
  state file and the job worktree's `git log` are the record.
- Don't keep going after a failed fast-forward merge — that means pending moved
  unexpectedly, and every later job is cut from it.

## The one deliberate exception to the review skill's read-only rule

`/planning-items-review` is read-only and explicitly does not flip statuses or
regenerate the exports. This skill does both, after a merge, for the items a
completed job covered. That is intentional: the review phase in step 2 stays
read-only, and the writes happen only in the pending worktree, only after work
has actually landed. Do not "fix" this back.
