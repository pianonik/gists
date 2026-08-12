# project-docs

Five skills for a project that keeps its state in three markdown files at the
repo root.

| File | Holds |
| --- | --- |
| `history.md` | A running narrative log of what was done and why, **newest entry at the top**, under `## YYYY-MM-DD` headings. |
| `TODO.md` | The open work, grouped into sections. Hand-edited. |
| `README.md` | Architecture and conventions. |

One more appears once you use the skills: `history-archive.md`, where trimmed
history entries move to. They are never deleted.

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

**`/verifytodo`** — finds out which status markers are lying. It checks each
against the code and git history, moves work that has verifiably shipped into
`DONE.md`, brings back any `DONE.md` claim it can't find an implementation for,
and reports anything ambiguous rather than moving it. Every move is listed at
the end so you can reverse it.

This is the one that keeps a `TODO.md` from turning into a changelog with the
real work buried in it. `/planning-review` reports the same drift but never
writes; this one corrects it.

## If your project tracks work as one file per item

Use the **item-tracker** plugin instead. These five have counterparts there that
read an `items/` store, and each one will tell you which sibling to use if it
finds the wrong shape of project.
