# project-docs

Five skills for a project that keeps its state in three markdown files at the
repo root.

| File | Holds |
| --- | --- |
| `history.md` | A running narrative log of what was done and why, **newest entry at the top**, under `## YYYY-MM-DD` headings. |
| `TODO.md` | The open work, grouped into sections. Hand-edited. |
| `README.md` | Architecture and conventions. |

Two more appear once you use the skills: `history-archive.md` (where trimmed
history entries move to — they are never deleted) and, if you use
`/updateplan`, `TODO-parallel.md` (the structural plan: which work can proceed
independently, in what order, and how it gets integrated).

Nothing here requires the files to exist. Each skill checks, says which ones are
missing, and continues with the rest rather than inventing them.

## The skills

**`/wherex`** — reads the three files and summarizes where the project stands.
Read-only; it writes nothing. Use it when picking a project back up.

**`/updatex`** — the mirror image. Writes the current conversation into
`history.md` (prepending a dated entry), marks finished items in `TODO.md`, and
touches `README.md` only if something architectural actually changed. It pulls
facts from `git log` rather than from memory, because conversation context gets
compacted and details drift.

It then runs `trim_history.py`, which moves entries older than a rolling window
(7 days by default) out of `history.md` and into `history-archive.md`. Content is
preserved exactly, both files stay newest-first, and re-running the same day
does nothing. Run it by hand from a repo root if you like:

```bash
python3 trim_history.py        # 7-day window
python3 trim_history.py 30     # 30-day window
```

**`/addtodo <text>`** — files one new item into `TODO.md`, under the section it
actually belongs to. It reads the live section headers rather than assuming any
particular set, so it works on a `TODO.md` organized any way at all.

**`/planning-review`** — the deep audit. Fans out parallel read-only agents to
compare what the planning docs claim against what the source actually contains,
and reports: what is built and verified versus only planned, doc drift, dead and
suspicious code grouped by confidence, and the genuinely open work currently
buried among finished items. Read-only unless you explicitly ask for a safe pass.

**`/updateplan`** — regenerates `TODO-parallel.md` from `TODO.md`, but only after
independently verifying each status claim against the code and git history. Work
that has verifiably shipped moves to `DONE.md`; anything ambiguous is reported
rather than moved. Every move is listed at the end so you can reverse it.

## If your project tracks work as one file per item

Use the **item-tracker** plugin instead. These five have counterparts there that
read an `items/` store, and each one will tell you which sibling to use if it
finds the wrong shape of project.
