#!/usr/bin/env python3
"""Regenerate the human-readable TODO / DONE views FROM the item store.

Writes into items/exports/ rather than over a repo-root TODO.md, so adopting
the store does not clobber a hand-authored file on day one. Point it at the
repo root later if you want it to own those files.

  items/exports/TODO.generated.md   — every non-done item, by section
  items/exports/DONE.generated.md   — every done item, by section

The generated files are build artifacts. Never hand-edit them; edit the items
and re-run this.

Usage:
  python3 items/scripts/export_todo.py

Install: copy this file and itemlib.py to <repo>/items/scripts/.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

EMOJI = {"backlog": "⬜", "needs-spec": "❓", "in-progress": "🟡",
         "pending-review": "⏳", "done": "✅"}
STATUS_RANK = {s: i for i, s in enumerate(
    ["pending-review", "in-progress", "needs-spec", "backlog", "done"])}


def project_name() -> str:
    """The repo directory's name — used only for the generated page titles."""
    return os.path.basename(il.REPO) or "Project"


def section_key(section: str, items: list[dict]) -> tuple[float, str]:
    """Sort sections by the smallest legacy section number they contain.

    Items migrated from a hand-authored TODO carry `legacy_num`, which keeps the
    generated view in the order people already know. A store with no legacy
    numbers at all falls through to alphabetical, which is at least stable.
    """
    nums = []
    for f in items:
        ln = str(f.get("legacy_num", "")).strip()
        try:
            nums.append(float(ln))
        except ValueError:
            pass
    return (min(nums) if nums else 999.0, section.lower())


def split_summary(body: str) -> tuple[str, str]:
    """(summary, the rest of the body).

    An item's one-line summary IS its body's first paragraph: HTML bodies open
    with <p>...</p>, markdown ones with text up to the first blank line. A body
    that opens with a list, a heading, or any other HTML block has no summary.
    """
    b = body.lstrip()
    if b.startswith("<p>"):
        end = b.find("</p>")
        if end < 0:
            return b.strip(), ""
        return b[: end + 4].strip(), b[end + 4:].strip()
    if not b or b[0] in "<#" or b[:2] in ("- ", "* ", "+ "):
        return "", b.strip()
    head, _, rest = b.partition("\n\n")
    return head.strip(), rest.strip()


def render(items: list[dict], title: str, blurb: str) -> str:
    by_section: dict[str, list[dict]] = {}
    for f in items:
        by_section.setdefault(f.get("section", "Uncategorized"), []).append(f)
    order = sorted(by_section, key=lambda s: section_key(s, by_section[s]))

    out = [f"# {title}", "", blurb,
           "", "_Generated from `items/*.md` by `export_todo.py` — do not hand-edit._", ""]
    for section in order:
        rows = sorted(by_section[section],
                      key=lambda f: (f.get("priority", 3),
                                     STATUS_RANK.get(f["status"], 9), f["title"].lower()))
        out.append(f"## {section}")
        out.append("")
        for f in rows:
            num = f" §{f['legacy_num']}" if str(f.get("legacy_num", "")).strip() else ""
            out.append(f"### {EMOJI[f['status']]} {f['title']}{num}  ·  P{f.get('priority', 3)}")
            out.append("")
            summary, detail = split_summary(f["body"])
            if summary:
                out.append(summary)
                out.append("")
            if f.get("tests"):
                out.append("_Tests: " + ", ".join(f"`{t}`" for t in f["tests"]) + "_")
                out.append("")
            # full detail — the body minus the summary paragraph, already shown
            if detail:
                out.append(detail)
                out.append("")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    items = il.load_items()
    open_items = [f for f in items if f["status"] != "done"]
    done_items = [f for f in items if f["status"] == "done"]

    exports = os.path.join(il.ITEMS_DIR, "exports")
    os.makedirs(exports, exist_ok=True)

    name = project_name()
    todo_md = render(open_items, f"{name} — TODO (generated)",
                     f"{len(open_items)} open items. Source of truth is `items/*.md`.")
    done_md = render(done_items, f"{name} — DONE (generated)",
                     f"{len(done_items)} completed items.")

    with open(os.path.join(exports, "TODO.generated.md"), "w", encoding="utf-8") as fh:
        fh.write(todo_md)
    with open(os.path.join(exports, "DONE.generated.md"), "w", encoding="utf-8") as fh:
        fh.write(done_md)

    print(f"wrote items/exports/TODO.generated.md  ({len(open_items)} open)")
    print(f"wrote items/exports/DONE.generated.md  ({len(done_items)} done)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
