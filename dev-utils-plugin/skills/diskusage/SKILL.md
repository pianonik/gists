---
name: diskusage
description: Analyze disk usage on this Mac and recommend what to delete, compress, or set online-only to reclaim space, in safety tiers. Never deletes or evicts anything without explicit approval, and reads a user-supplied keep-out list first. Use when the user says "diskusage", "/diskusage", "analyze disk usage", or asks how to free up space or what is eating the disk.
tools: Read, Bash, Write
---

# diskusage

Survey disk usage on this machine and produce **prioritized, safety-tiered
recommendations** for reclaiming space. Default to *analysis and suggestions* —
never delete or evict anything until the user explicitly approves a tier or
specific items.

## Golden rules

- **Suggest first, act only on approval.** Present a tiered plan; wait for a
  clear go-ahead before deleting. When approved, capture `df -h /` before and
  after.
- **Never delete without checking what something is.** A 184 GB directory can be
  a *live* backup rather than garbage. Size is not evidence of disposability.
- **Fail loud.** If a command errors, report it. Don't paper over it and don't
  silently skip a directory you couldn't read.
- **Verify deletions landed**, but don't expect `df` to reflect them
  immediately. See the APFS snapshot section.

## Step 0 — Read the keep-out list FIRST

```bash
cat ~/.claude/disk-keepout.md 2>/dev/null
```

A plain list, one path per line, with a note about why — things that must never
be recommended for deletion. Read it before surveying, and exclude everything on
it from every recommendation. If a keep-out item is enormous, you may *report*
its size for context, clearly marked as off-limits.

**If the file doesn't exist**, say so once and proceed more cautiously: anything
you can't prove is regenerable gets surfaced as a question rather than a
recommendation. At the end, offer to write the file from what you learned, so
the next run doesn't re-ask.

## Step 1 — Free space and top-level survey

```bash
df -h /                                          # free space (includes purgeable)
du -sh "$HOME"/* 2>/dev/null | sort -rh | head -15
```

Then drill into the biggest hitters — typically `~/Library`, wherever the user
keeps code, `~/Music`, `~/Pictures`:

```bash
du -sh "$HOME"/Library/* 2>/dev/null | sort -rh | head -12
du -sh "$HOME"/Library/Caches/* 2>/dev/null | sort -rh | head -12
du -sh "$HOME/Library/Application Support/"* 2>/dev/null | sort -rh | head -12
```

Big `du` runs are slow. Launch them with `run_in_background: true` and read the
output when they finish, rather than blocking.

## Step 2 — Classify into tiers

**Tier 1 — safe and regenerable (delete freely on approval):**

- Build output and derived data: `build/`, `DerivedData`, `*.build`, `target/`,
  `node_modules` in projects not currently being worked on.
  ```bash
  find "$HOME" -maxdepth 5 -type d \( -name build -o -name DerivedData -o -name "*.build" \) 2>/dev/null
  ```
- `~/Library/Caches/*` — browser, package-manager, toolchain caches. All
  regenerate.
- `~/Library/Developer/Xcode/DerivedData` and `~/Library/Developer/CoreSimulator`.
  Orphaned simulators: `xcrun simctl delete unavailable`.
- Git LFS caches: `du -sh <repo>/.git/lfs`, pruned with `git lfs prune` **run
  inside that repo**. Check the repo's own docs first — a project using a custom
  LFS transfer agent may not support every prune flag, and a repo whose LFS
  history is shallow will reclaim almost nothing because every object is still
  referenced.

**Tier 2 — stale backups and archives (review, then delete or compress):**

- Old dated archive directories, e.g. mail archives — compress to `.tar.gz` if
  keeping.
- Throwaway clones, zip files of failed experiments, old downloads.

**Tier 3 — redundant full git clones (delete only after confirming pushed):**

- Extra copies of a repo: old trees, feature-branch clones, second checkouts.
- Before deleting any clone, confirm nothing is stranded in it:
  ```bash
  git -C <dir> status
  git -C <dir> log --branches --not --remotes --oneline   # commits not on any remote
  ```
  A clone with unpushed commits or uncommitted changes is not redundant. Say so
  and leave it.

**Tier 4 — cloud storage set to online-only, and other large media.** See step 3.

## Step 3 — Cloud storage: online-only analysis

Third-party cloud folders under `~/Library/CloudStorage/` are usually the single
biggest lever, and the safest, because nothing is deleted: the files stay
visible in Finder and present in the cloud, and only the local bytes are
released. They rehydrate on open, which needs an internet connection.

Find the biggest folders and the **newest modification date** in each, as a
proxy for staleness:

```bash
/usr/bin/python3 - <<'PY'
import os, time
base = os.path.expanduser("~/Library/CloudStorage")   # or a specific subfolder
rows = []
for name in os.listdir(base):
    p = os.path.join(base, name); size = 0; newest = 0
    if os.path.isfile(p):
        st = os.lstat(p); size = st.st_size; newest = st.st_mtime
    else:
        for r, ds, fs in os.walk(p):
            for f in fs:
                try:
                    st = os.lstat(os.path.join(r, f)); size += st.st_size
                    if st.st_mtime > newest: newest = st.st_mtime
                except OSError:
                    pass
    rows.append((size, newest, name))
rows.sort(reverse=True); now = time.time()
print(f"{'SIZE':>8}  {'NEWEST':<12} {'AGE':>6}  NAME")
for sz, mt, name in rows[:22]:
    d = time.strftime('%Y-%m-%d', time.localtime(mt)) if mt else '-'
    age = f"{int((now-mt)/86400)}d" if mt else '-'
    print(f"{sz/1e9:7.1f}G  {d:<12} {age:>6}  {name}")
PY
```

**Caveats to state every time:**

- A modification time can be bumped by a **re-sync touch** rather than a real
  edit. A cluster of folders sharing one recent date is a sync event, not
  activity. Trust the combination of an old date *and* a name that says the
  content is finished — a year, "archive", a completed project name.
- Recommend online-only for **archival** content: finished projects, photo
  libraries, old recordings. Not for anything in active use.
- **How to do it:** Finder right-click → "Make Online-Only." There is no
  documented command-line tool for third-party File Provider eviction — do NOT
  guess one. (`brctl` is iCloud-only and does not apply.) If the user wants to
  batch it, research the specific provider first rather than experimenting on
  their files.

## Step 4 — Present, and on approval execute

Give a markdown table per tier: size, age, and a one-line note. Lead with the
total reclaimable per tier. Then ask which tiers or items to execute.

On approval: `df -h / | tail -1` before, delete, `df -h / | tail -1` after, and
confirm the directories are actually gone (`ls -d`).

## The APFS snapshot caveat — explain this every time `df` looks unchanged

Deleting files on APFS does **not** immediately free space if a local Time
Machine snapshot still references those blocks. The space becomes *purgeable*,
and `df` keeps reporting the old free number. macOS purges it automatically
under pressure. To reclaim it now:

```bash
tmutil listlocalsnapshots /                        # see the snapshots
sudo tmutil thinlocalsnapshots / 40000000000 4     # urgently free ~40 GB
```

This removes only *local* restore points; real Time Machine backups on an
external disk are untouched. `sudo` needs a terminal, so ask the user to run it
themselves rather than trying to run it for them.

## Things that look like garbage and are not

Check for these before recommending anything in their neighbourhood:

- **Backup destinations that run on a schedule.** Look for a launchd job
  (`launchctl list`) or cron entry pointing at a directory before calling it
  stale.
- **Device backups** under `~/Library/Application Support/MobileSync/Backup` —
  large, irreplaceable if the device is lost, and not regenerable.
- **Active project trees and shared cloud folders in use** — online-only at
  most, never delete.
- **Anything you didn't create and can't prove is regenerable.** Surface it as a
  question; don't recommend removing it.
