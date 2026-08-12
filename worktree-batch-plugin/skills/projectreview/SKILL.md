---
name: projectreview
description: Optionally wait a while, then review recent commits on the default branch of one or more repos against the project tracker — flagging partially-completed, obviously broken, or inefficient work — then generate a ready-to-run script that creates one git worktree per follow-up job, each with a prompt detailed enough to hand to a fresh unattended session. Read-only with respect to the repos; it writes the script but never runs it. Use when the user says "projectreview" or "/projectreview".
tools: Bash, Read, Write, Grep, Glob, Agent
---

# projectreview

Review what has recently landed on the default branch of one or more repos,
compare it against the project's tracker, and turn the findings into a set of
worktrees that are ready to open — each with a prompt detailed enough to hand to
a fresh session that has never seen the review.

**This skill is read-only with respect to every repo it reviews.** No commits,
no tracker edits, no builds, no launching applications — other sessions may be
running them. It writes exactly two things, both under its own state directory:
the state file, and the generated script (step 7). It does **not** run that
script; creating worktrees mutates the repo, and that is the user's call.

## Arguments

All optional, whitespace-separated, any order:

- `<path>` — a repo to review. Give it more than once for several repos. With
  none given, review the repo containing the current working directory.
- `now` — skip the wait and review immediately. This is the default when no
  duration is given.
- `<N>h` / `<N>m` — wait this long before reviewing.
- `since=<sha|date>` — override the review-window start for every repo, e.g.
  `since=2026-07-04` or `since=27b76f85`. Otherwise the window comes from the
  state file.

## Where state and output go

Under `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/projectreview}/`:

- `state.json` — the last reviewed commit per repo, keyed by absolute repo path.
- `out/<YYYY-MM-DD>/` — the generated script and its prompt files.

Nothing is ever written inside the repos being reviewed.

## Procedure

### 1. The wait

Skip this entirely unless the user asked for a duration.

Compute the delay in seconds and start it with the Bash tool using
**`run_in_background: true`**:

```bash
sleep 14400
```

Then tell the user the wall-clock time the review will begin, and stop — end the
turn. Do **not** poll the background task and do **not** schedule extra wakeups.
When the sleep exits, the harness re-invokes the session; begin step 2 then.

Give one caveat at kickoff: the wait lives inside this session, so if the
session is closed before the sleep finishes, the review never runs. For fully
unattended scheduling, a scheduled cloud agent is the right tool instead.

### 2. Resolve the review window, per repo

The state file's shape:

```json
{ "/abs/path/to/repo": { "last_reviewed": "<sha>", "at": "<iso-date>" } }
```

Per repo:

- Window **start**: the `since=` argument if given, else that repo's
  `last_reviewed` SHA from the state file, else `--since="30 days ago"` on a
  first run.
- Window **end** — the tip. Fetch first, best effort, then prefer the remote
  branch when it's ahead. **Resolve the default branch name per repo rather than
  assuming it**; repos in the same review can differ.

```bash
git -C "$REPO" fetch origin --quiet || echo "fetch failed — reviewing local refs only"
BR=$(git -C "$REPO" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
if [ -z "$BR" ]; then
  git -C "$REPO" show-ref -q --verify refs/heads/master && BR=master || BR=main
fi
git -C "$REPO" rev-parse -q --verify "$BR" >/dev/null \
  || { BR=$(git -C "$REPO" branch --show-current); echo "no master/main — using checked-out branch $BR"; }
TIP="$BR"
if git -C "$REPO" rev-parse -q --verify "origin/$BR" >/dev/null \
   && git -C "$REPO" merge-base --is-ancestor "$BR" "origin/$BR"; then
  TIP="origin/$BR"
fi
echo "$REPO: branch=$BR tip=$TIP"
```

If a repo has no `master` or `main`, say so in the report and fall back to its
checked-out branch — don't silently substitute. If local and remote have
diverged, review the local one and flag the divergence itself as a finding.

The window deliberately extends to *review* time, not kickoff time, so commits
that land during any wait are included.

### 3. Gather the commits

```bash
git -C "$REPO" log --stat --date=short "<START>..$TIP"
```

Skim the full list once to cluster commits by feature or area. If the repo's
commit subjects carry a branch tag or a scope prefix, the clusters are usually
obvious from that. Then `git show` the commits that matter.

**Fan out when the window is big:** if the combined window exceeds roughly 30
commits, split the clusters across `Explore` agents launched in ONE message —
one per repo, or one per feature cluster — each returning findings in the shape
of step 5, and synthesize their results. Small windows: review inline.

### 4. Load the tracker (read-only)

Detect which kind the project uses:

- **Item store** — `items/*.md` with `items/scripts/itemlib.py`. Load it
  read-only; do NOT run the export script, which writes:
  ```bash
  cd "$REPO" && python3 - <<'PY'
  import sys, collections
  sys.path.insert(0, "items/scripts")
  import itemlib as il
  items = il.load_items()
  print("STORE:", len(items), "items —", dict(collections.Counter(f["status"] for f in items)))
  for f in items:
      if f["status"] != "done":
          print(f"{f['status']:14} P{f.get('priority',3)}  [{f['id']}]  {f['title']}")
  PY
  ```
- **Flat `TODO.md`** — read it, and derive its live section headers rather than
  assuming a scheme.
- **Neither** — say so; every finding is then simply untracked, which is itself
  worth reporting.

Also skim the top of `history.md` if there is one, for context on recent rounds.

### 5. What to look for

Cross-reference commits against tracker entries. Every finding needs a pointer:
the commit SHA, the file and enclosing symbol where relevant, and the tracker
item it relates to — or "untracked".

**Partially completed:**

- The commit subject or tracker item promises more than the diff delivers — a
  change made on one platform when the item covers two, a new component without
  the configuration or assets its siblings all have.
- "Phase N" or "round M" language whose follow-up phases exist nowhere in the
  tracker.
- Items marked done whose promised gate tests don't exist or aren't wired to any
  build target. **Find the repo's live test directory before judging this** —
  a project can have a dead legacy test tree alongside the real one, in which
  case a new test added to the dead tree is itself a finding, not evidence the
  gate exists.
- In-progress or awaiting-review items with recent commits — state precisely
  what remains.
- Commit clusters with **no** corresponding tracker entry at all — suggest
  tracking them.

**Obviously broken or suspicious — static review only, do not build:**

- Newly introduced `TODO` / `FIXME` / `HACK` / `XXX`, disabled code blocks, or
  commented-out sections.
- Tests disabled or skipped, or gates weakened or removed.
- **Silent fallbacks added** — a path that quietly degrades instead of failing.
  Flag every one; a fallback hides the logic error that caused it.
- Backward-compatibility shims added to a project that hasn't shipped yet.
- Half-reverted or contradictory changes across the window, where one commit
  adds what another removes.

**Inefficient — flag only real ones, not micro-optimizations:**

- Per-frame or per-block allocations, locks, or quadratic loops on a hot path.
- Caching added with no demonstrated performance need.
- Duplicated logic that already exists in a shared helper.

### 6. Report the findings

Print inline; write no files into the repos:

```
## Review window
<repo>:  <start>..<tip>  (<n> commits)

## Findings
### Partially completed
### Broken / suspicious
### Inefficient
(each finding: what it is + SHA + file and symbol + tracker item id)
```

Mark which findings **you verified yourself** versus which came back from a
fan-out agent. A claim you re-checked in the code carries more weight than one
you relayed, and the user should be able to tell them apart.

Say what is verifiably *clean*, too, briefly. "All 26 call sites got the change,
none remain" is worth a line — it stops the next round re-investigating.

### 7. Carve the findings into worktrees, and generate the script

The point is a set of jobs the user can open **whenever they like**, and the
recommendation is **one at a time**. Jobs merge back into the same base branch,
so two running at once means resolving their overlap by hand at merge time, and
the second job never sees the first one's work. `/sequencework` exists to run a
queue like this properly: each job cut from the previous one's result, merged
before the next starts.

So don't carve for parallelism, and don't rank jobs by whether they could run
simultaneously. Carve by **what makes one coherent job**:

- One worktree per *theme a single session can hold in its head* — a subsystem,
  a file cluster, one round's follow-ups. A job needing two unrelated mental
  models is two jobs.
- Size for one sitting. Fifteen findings in one job means split it.
- **Keep the same file in ONE worktree** where you can. Two worktrees editing
  one file is legal and usually merges, but it costs a conflict resolution — so
  it needs a reason, and you should state the reason.
- **At most ONE worktree may touch shared code that lives outside the repo** — a
  sibling checkout, a linked package, a shared library directory. Worktrees do
  not isolate anything outside the repo, so a second job touching it corrupts
  the first no matter when it runs.
- Name each `<verb-or-area>` in kebab-case, giving branch `worktree-<name>` at
  `.claude/worktrees/<name>`.
- Anything that must happen *after* several jobs land — a history sweep, a
  tracker pass, a change to shared test infrastructure every job imports — is
  its own **follow-up** job. Call it out and say what it waits on. That's
  sequencing, not parallelism.

Then **write** — do not run — a script at
`${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/projectreview}/out/<YYYY-MM-DD>/make-worktrees.sh`,
with one prompt file per job beside it as `<name>.prompt.md`.

**Be exact about where the script stops.** It sets work up; it does not start
work. It makes the repo copies, puts the instructions inside them, prints one
command per job, and exits with nothing running. Say that in the script's header
comment and again in its closing output, in those words — not "fires them off",
not "launches", not left to inference. A script that looks like it might have
started four sessions is a script nobody dares run twice.

The script must:

1. Resolve the main repo root the way `/mkwt` does —
   `git worktree list --porcelain | awk '/^worktree /{print substr($0,10); exit}'` —
   so it works from inside another worktree. Note this reads the **working
   directory**, not the script's own location, so bake in the expected repo root
   and check a path only that repo has; if it doesn't match, fail with the
   `cd <repo> && …` fix spelled out.
2. Ensure `.claude/worktrees/` is in
   `$(git rev-parse --git-common-dir)/info/exclude` — per-clone, not versioned,
   so check every time.
3. Per job: skip with a message if the branch or directory already exists —
   never `-f`, never delete — else
   `git worktree add -b worktree-<name> "$MAIN/.claude/worktrees/<name>" <base>`,
   using the base branch resolved in step 2.
4. Copy that job's `<name>.prompt.md` into the worktree as
   `.worktree-prompt.md`. The leading dot plus the `.claude/worktrees/`
   exclusion keeps it out of any commit.
5. Print, per job, the one line that starts it, wrapped in a subshell so the
   `cd` doesn't strand the user's terminal inside the worktree:

   ```
   (cd "<dir>" && claude --bg -n "<name>" --permission-mode bypassPermissions "$(cat .worktree-prompt.md)")
   ```

   `--bg` starts a background agent and returns immediately, so the user can
   start the next one; `-n` names it so several are tellable apart. Print a
   `for j in …; do …; done` form too, and one line warning that N simultaneous
   builds will bog the machine down.
6. Print how to watch the running agents, where to *read* a job's instructions
   without starting it, and how a finished job gets back to the base branch
   (`/wtmerge`).
7. For any job that waits on another, print what it waits on **and why in one
   plain sentence** — "it edits the file every other job's tests import" beats
   "shared infrastructure". Do not create those worktrees: a branch cut today is
   out of date by the time its predecessor merges.
8. Report progress with `echo`, not `#` comments — the user reads the output.
9. Take `--dry-run` to print what it would make and exit 0, and accept job names
   as arguments to make only those.

Set `set -u`. On macOS, bash 3.2 treats `"${arr[@]}"` on an empty array as an
unbound-variable error, so guard on `${#arr[@]}` before expanding.

After creating a worktree in an LFS repo, check
`git lfs ls-files | awk '$2=="-"'`; if it returns rows, print the
`TMPDIR="$MAIN/.git/lfs/tmp" git lfs pull` fix rather than running it.

**Syntax-check the script (`bash -n`) and run it with `--dry-run`** before
handing it over. A generated script that fails on first use is worse than no
script.

**Each prompt file must stand alone.** Assume the session reading it has never
seen this review and that nobody is watching — it runs unattended with
permissions bypassed, so anything left implicit will not get asked about.

Open every prompt with these three blocks, in this order, before any detail:

1. **`## GOAL`** — one or two sentences saying what is *true* when the job is
   finished. A state, not a task list.
2. **`## DONE WHEN`** — the checkable lines that add up to the goal. Each must
   be something a session can look at and answer yes or no to. "The gate passes"
   is weak; "you have shown each assertion going red on purpose" survives an
   unattended run. Include the specific command that settles each one.
3. **`## HOW TO WORK`** — the build → test → fix loop in this repo's own terms.
   Name an iteration skill only if one is installed and fits the platform.
   Otherwise write the commands out. Then, in these words: **stay in the loop
   until every line above is true, and do not stop at the first green run.**
   Then: if a DONE WHEN line turns out to be wrong or impossible, say so plainly
   and stop — do not quietly drop it and report success on the rest.

Then a `---` rule, then the detail:

- **The job** in one sentence, then the findings it covers, each with the commit
  SHA, the file *and the enclosing symbol* — line numbers rot — and the tracker
  item id or "untracked".
- **Why it's wrong**, concretely: what breaks, or what the code claims that the
  code doesn't do. Enough that the session can disagree with you.
- **Constraints that apply**, quoted from this repo's own `CLAUDE.md` or
  `AGENTS.md` rather than from memory, because a fresh session won't recall
  them.
- **How to check it worked** — the specific test, build target, or iteration
  round. If verification needs a running application, say which platform.
- **Anything deliberately out of scope**, so two jobs don't fix one thing twice.
- **How to land it**: `/wtmerge` or `/fwtmerge`.

Finish the report with a compact table — name, one-line job, files it owns —
then the path to the script and the one command that runs it. In plain English,
say what running it will and will not do: it makes the repo copies and writes
the instructions into them, it does not start any session and does no work, and
afterwards the user starts whichever jobs they want by pasting the printed
lines. State that you did not run it yourself.

### 8. Update state

After the report, write the reviewed tip SHAs and today's date to the state
file, keyed by absolute repo path, so the next run's window starts where this
one ended.

## Don't

- Don't build, run tests, or launch applications — static review only. Runnable
  verification becomes a job in a worktree.
- Don't **run** the generated script, create worktrees, or check out branches.
  Generating is the deliverable; running is the user's call.
- Don't edit the tracker, `history.md`, or commit anything.
- Don't poll a background sleep or schedule extra wakeups.
- Don't carve for parallelism or invent "streams" — carve by coherence, state
  the real ordering constraints, and recommend running them in sequence.
- Don't pad the findings. If the window is clean, say so in three lines and
  generate no worktrees.
