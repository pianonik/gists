---
name: whereitems
description: Catch up on the current project's state by reading history.md, README.md, and the items/*.md store (each file's status field IS its open/done state) from the current working directory, then summarize where we are. Use when the user says "whereitems", "/whereitems", or otherwise asks to be brought up to speed on an item-store project. If the project has a flat hand-edited TODO.md instead, use /wherex.
tools: Read, Bash
---

# whereitems

Bring the user (and yourself) up to speed on the current project by reading the
canonical context files and the **item store**, then summarizing where things
stand. The item-store sibling of `/wherex`: same job, different substrate — the
source of truth is `items/*.md`, one file per item, with `status:` owning
open-versus-done, not a flat `TODO.md`.

## First: confirm this project uses the item store

The store is `items/*.md` at the repo root, each file front matter plus a body
whose first paragraph is the one-line summary. Helper scripts live in
`items/scripts/` (`itemlib.py`, `export_todo.py`).

If there is **no `items/` store**, STOP and tell the user to run `/wherex`
instead. Do not invent an item store.

## What to read

From the current working directory, in this order:

1. `history.md` — newest entries at top; the running log of what was done and why.
2. `README.md` — project overview and architecture.
3. The **item store** (`items/*.md`), via `items/scripts/itemlib.py`, read-only.

If `history.md` or `README.md` is missing, note it and continue. Do NOT search
elsewhere or guess.

## How to read them

- `history.md` is usually long. Read the top of the file first. Only read
  further back if the user asks for deeper history.
- `README.md` — read in full if reasonably sized.
- The **item store** — do NOT read every `items/*.md` by hand, and do NOT run
  `export_todo.py`, which *writes* the generated views (this skill is
  read-only). Load the store read-only with `itemlib` and print a status summary
  plus the open items:

  ```bash
  python3 - <<'PY'
  import sys, collections
  sys.path.insert(0, "items/scripts")
  import itemlib as il                      # fails loud on a malformed item — useful signal
  items = il.load_items()
  by_status = collections.Counter(f["status"] for f in items)
  print("STORE:", len(items), "items —", dict(by_status))
  rank = {s: i for i, s in enumerate(
      ["pending-review", "in-progress", "needs-spec", "backlog", "done"])}
  open_items = [f for f in items if f["status"] != "done"]
  open_items.sort(key=lambda f: (f.get("section", ""), rank.get(f["status"], 9), f.get("priority", 3)))
  sec = None
  for f in open_items:
      if f.get("section") != sec:
          sec = f.get("section"); print(f"\n[{sec}]")
      print(f"  {f['status']:14} P{f.get('priority', 3)}  {f['title']}")
  PY
  ```

  This prints everything whose status is not `done`, grouped by section, most
  actionable status first.

Prefer running the two Reads and this Bash summary together — they're
independent.

## What to output

A concise summary:

- **Where we are** — 1–3 sentences on the current state, from the most recent
  `history.md` entries.
- **Open items** — what's pending, from the store summary. Flag any
  `pending-review` items (done, awaiting the user's sign-off) **separately** from
  `in-progress` and `backlog` — those are waiting on the user, not on work.
- **Anything notable** — only if there's a recent decision, blocker, or context
  shift worth flagging.

Keep it tight. The user is orienting, not asking for a deep dive.

## Don't

- Don't dump file or item contents verbatim.
- Don't run `export_todo.py` or write `TODO.md` / `DONE.md` / `items/exports/*` —
  this skill is read-only orientation. Regenerating the exports is
  `/updateitems`' job.
- Don't edit `items/*.md`, `history.md`, or anything else.
- Don't read files outside the current working directory unless asked.
- Don't invent an item store if there isn't one — send the user to `/wherex`.
