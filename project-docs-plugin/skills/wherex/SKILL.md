---
name: wherex
description: Catch up on the current project's state by reading history.md, README.md, and TODO.md (in that order) from the current working directory, then summarize where we are. Use when the user says "wherex", "/wherex", or otherwise asks to be brought up to speed on the project.
tools: Read, Bash
---

# wherex

Bring the user (and yourself) up to speed on the current project by reading the
three canonical context files and summarizing where things stand.

## What to read

From the current working directory, in this exact order:

1. `history.md` — newest entries at top; the running log of what was done and why
2. `README.md` — project overview and architecture
3. `TODO.md` — current work items

If any of these is missing, note it and continue with the rest. Do NOT search
elsewhere or guess — only these three files, only from the current working
directory.

If **none** of the three exists, say so plainly and stop: this project does not
use the convention the skill is for. If there is an `items/` directory with one
markdown file per work item, suggest `/whereitems` instead.

## How to read them

- `history.md` is usually long. Read the top of the file first (most recent
  entries) to get current context. Only read further back if the user asks for
  deeper history.
- `README.md` — read in full if reasonably sized.
- `TODO.md` — read in full.

Prefer parallel Read calls for the initial pass since the three are independent.

## What to output

A concise summary:

- **Where we are** — 1–3 sentences on the current state, drawn from the most
  recent `history.md` entries.
- **Open items** — bullet list of what's pending, drawn from `TODO.md`.
- **Anything notable** — only if there's a recent decision, blocker, or context
  shift worth flagging.

Keep it tight. The user is orienting, not asking for a deep dive — they'll ask
follow-ups if they want more.

## Don't

- Don't dump file contents verbatim.
- Don't read files outside the current working directory unless asked.
- Don't update `history.md` or any other file — this is read-only orientation.
