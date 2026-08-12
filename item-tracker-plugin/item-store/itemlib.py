#!/usr/bin/env python3
"""Shared helpers for the item store (items/*.md).

Reads and writes one-item-per-file markdown with a small YAML-subset front
matter block. Standard library only — no PyYAML dependency, because the front
matter is a controlled format: `key: value` scalars and `- item` lists, nothing
more.

Fails loud on a malformed item file rather than silently skipping it. A skill
that quietly drops an unreadable item reports a work list that is missing
something, which is worse than an error.

Install: copy this file and export_todo.py to <repo>/items/scripts/.
"""
from __future__ import annotations

import os
import re

# The repo root, derived from this file's own location: <repo>/items/scripts/.
# Deriving rather than passing it in is what makes the store work correctly
# inside a git worktree — running the script from a worktree edits THAT
# worktree's copy of the store, which is what you want.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ITEMS_DIR = os.path.join(REPO, "items")

STATUSES = ["backlog", "needs-spec", "in-progress", "pending-review", "done"]

# Front-matter keys in serialization order. Anything not listed is written
# after these, in the order it appears, so an extra field is preserved rather
# than dropped. `legacy_num` is optional: it carries the old section number of
# an item migrated from a hand-authored TODO, and is absent on new items.
FIELD_ORDER = ["id", "title", "section", "legacy_num", "status", "priority",
               "needs_spec", "created", "updated", "tests"]


class ItemError(Exception):
    pass


def _coerce(val: str):
    val = val.strip()
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]
    return val


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Return (front_matter_dict, body). Raises if the block is malformed."""
    if not text.startswith("---"):
        raise ItemError("missing front-matter opening '---'")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise ItemError("missing front-matter closing '---'")
    block, body = m.group(1), m.group(2).lstrip("\n")
    data: dict = {}
    key = None
    for raw in block.splitlines():
        if not raw.strip():
            continue
        li = re.match(r"^\s*-\s+(.*)$", raw)
        if li is not None:
            if key is None or not isinstance(data.get(key), list):
                raise ItemError(f"list item with no preceding list key: {raw!r}")
            data[key].append(_coerce(li.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", raw)
        if kv is None:
            raise ItemError(f"unparseable front-matter line: {raw!r}")
        key, val = kv.group(1), kv.group(2).strip()
        data[key] = [] if val == "" else _coerce(val)
    return data, body


def dump_front_matter(data: dict) -> str:
    keys = [k for k in FIELD_ORDER if k in data] + \
           [k for k in data if k not in FIELD_ORDER]
    out = ["---"]
    for k in keys:
        v = data[k]
        if isinstance(v, list):
            out.append(f"{k}:")
            out.extend(f"  - {item}" for item in v)
        elif isinstance(v, bool):
            out.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, str) and (v == "" or re.search(r"[:#]", v) or v.strip() != v):
            out.append(f'{k}: "{v}"')
        else:
            out.append(f"{k}: {v}")
    out.append("---")
    return "\n".join(out)


def load_item(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    try:
        fm, body = parse_front_matter(text)
    except ItemError as e:
        raise ItemError(f"{os.path.relpath(path, REPO)}: {e}") from e
    fm["body"] = body
    fm["path"] = path
    fm.setdefault("tests", [])
    fm.setdefault("priority", 3)
    if fm.get("status") not in STATUSES:
        raise ItemError(f"{os.path.relpath(path, REPO)}: bad status {fm.get('status')!r}")
    return fm


def load_items(items_dir: str = ITEMS_DIR) -> list[dict]:
    items = []
    for name in sorted(os.listdir(items_dir)):
        if name.endswith(".md") and name not in ("PLAN.md", "README.md"):
            items.append(load_item(os.path.join(items_dir, name)))
    return items


def write_item(items_dir: str, fm: dict, body: str) -> str:
    data = {k: v for k, v in fm.items() if k not in ("body", "path")}
    path = os.path.join(items_dir, f"{data['id']}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(dump_front_matter(data) + "\n\n" + body.strip() + "\n")
    return path


def slugify(title: str, maxlen: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(s) > maxlen:
        s = s[:maxlen].rsplit("-", 1)[0]
    return s or "item"
