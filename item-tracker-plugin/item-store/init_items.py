#!/usr/bin/env python3
"""Convert a hand-written TODO file into an items/*.md store.

The file can be TODO.md, TODO.txt, NOTES.md, or anything else — pass its path.
It does not have to be tidy. What it does have to be is *consistent enough* that
one entry can be told from the next, and this script tells you up front whether
it is:

    init_items.py TODO.md --scan

That prints the structure it detected — how sections are marked, where entry
boundaries fall, which status markers occur and how often — and writes nothing.
Read it, decide the marker mapping, then convert:

    init_items.py TODO.md --map "⬜=backlog,🟡=in-progress,✅=done" --dry-run
    init_items.py TODO.md --map "⬜=backlog,🟡=in-progress,✅=done"

Two rules this script will not break:

  * It never modifies or deletes the source file. Renaming the old TODO once you
    are satisfied is a separate, deliberate step.
  * It refuses to write into a store that already has items, unless you pass
    --force. Converting twice into the same directory silently merges two
    interpretations of the same file, which is very hard to unpick afterwards.

Everything is written through itemlib, so slugs, quoting and front-matter order
match the rest of the store exactly.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itemlib as il  # noqa: E402

STATUSES = il.STATUSES

# Markers seen in the wild. Used for DETECTION only — never for mapping, because
# the same glyph means different things in different projects and guessing wrong
# mislabels the whole store on day one. The user supplies --map.
MARKER_RE = re.compile(
    r"(\[[ xX~\-]\]"                       # - [ ] / [x] / [~]
    r"|\[[A-Z][A-Z ]{1,14}\]"              # [FIXED] [IN PROGRESS] [WONTFIX]
    r"|[☀-➿⬀-⯿\U0001F300-\U0001FAFF])"  # emoji
)
HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")


class Entry:
    __slots__ = ("title", "section", "markers", "detail", "line")

    def __init__(self, title, section, markers, line):
        self.title, self.section, self.markers, self.line = title, section, markers, line
        self.detail = []


def strip_markers(text: str) -> tuple[str, list[str]]:
    found = MARKER_RE.findall(text)
    cleaned = MARKER_RE.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" \t-–—:·")
    return cleaned, found


def detect_entry_level(lines: list[str]) -> str:
    """Guess what constitutes one entry: 'header:N', 'bullet', or 'para'."""
    headers = collections.Counter()
    for ln in lines:
        m = HEADER_RE.match(ln)
        if m:
            headers[len(m.group(1))] += 1
    # The deepest header level used at least 3 times is almost always the item
    # level; shallower ones are sections.
    deep = [lvl for lvl, n in sorted(headers.items()) if n >= 3]
    if len(deep) >= 2:
        return f"header:{deep[-1]}"
    top_bullets = sum(1 for ln in lines if (m := BULLET_RE.match(ln)) and len(m.group(1)) == 0)
    if top_bullets >= 3:
        return "bullet"
    if deep:
        return f"header:{deep[-1]}"
    return "para"


def parse(lines: list[str], entry_level: str) -> list[Entry]:
    entries: list[Entry] = []
    section = "Uncategorized"
    cur: Entry | None = None
    want_hdr = int(entry_level.split(":")[1]) if entry_level.startswith("header:") else None

    def close():
        nonlocal cur
        if cur is not None:
            entries.append(cur)
            cur = None

    for i, raw in enumerate(lines, 1):
        ln = raw.rstrip("\n")
        hm = HEADER_RE.match(ln)
        if hm:
            lvl, text = len(hm.group(1)), hm.group(2).strip()
            if want_hdr is not None and lvl >= want_hdr:
                close()
                title, marks = strip_markers(text)
                cur = Entry(title, section, marks, i)
            else:
                close()
                section = strip_markers(text)[0] or "Uncategorized"
            continue

        bm = BULLET_RE.match(ln)
        if bm and entry_level == "bullet" and len(bm.group(1)) == 0:
            close()
            title, marks = strip_markers(bm.group(2).strip())
            cur = Entry(title, section, marks, i)
            continue

        if entry_level == "para" and not ln.strip():
            close()
            continue
        if entry_level == "para" and cur is None and ln.strip():
            title, marks = strip_markers(ln.strip())
            cur = Entry(title, section, marks, i)
            continue

        if cur is not None:
            cur.detail.append(ln)
        # text before the first entry (preamble) is deliberately dropped: it is
        # legend and instructions, not work.
    close()
    return [e for e in entries if e.title]


def inline(text: str) -> str:
    """Escape, then translate the markdown inline spans the store uses in HTML."""
    s = html.escape(text, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    return s.strip()


def blocks(detail: list[str]) -> list[tuple[str, list[str]]]:
    """Group the entry's lines into ('p', [text]) and ('ul', [items]) blocks.

    A non-bullet, non-blank line following a bullet is a *lazy continuation* of
    that bullet in markdown, not a new paragraph. Treating it as a new paragraph
    is what shreds a wrapped source file into fragments, so it is joined back on.
    """
    out: list[tuple[str, list[str]]] = []
    mode = None
    for raw in detail:
        line = raw.rstrip()
        if not line.strip():
            mode = None
            continue
        bm = BULLET_RE.match(line)
        if bm:
            if mode != "ul":
                out.append(("ul", [])); mode = "ul"
            out[-1][1].append(bm.group(2).strip())
        elif mode == "ul":
            out[-1][1][-1] += " " + line.strip()          # lazy continuation
        else:
            if mode != "p":
                out.append(("p", [])); mode = "p"
            out[-1][1].append(line.strip())
    return out


def to_html(entry: Entry) -> str:
    """First <p> is the one-line summary; the rest of the entry follows as detail."""
    body = blocks(entry.detail)

    # The summary should say something the title doesn't. Prefer the entry's
    # first prose line; fall back to the title when the entry is title-only.
    summary, rest = None, body
    if body and body[0][0] == "p":
        first = " ".join(body[0][1])
        if first and first.strip() != entry.title.strip():
            summary = first if len(first) <= 300 else first[:297].rsplit(" ", 1)[0] + "…"
            remainder = body[0][1][1:] if len(body[0][1]) > 1 else []
            rest = ([("p", remainder)] if remainder else []) + body[1:]
    out = [f"<p>{inline(summary or entry.title)}</p>"]

    for kind, lines in rest:
        if not lines:
            continue
        out.append("")
        if kind == "ul":
            out.append("<ul>")
            # checkbox markers stay as literal text inside the <li> -- that is
            # how progress is tracked in the store and how it is grepped for
            out.extend(f"  <li>{inline(l)}</li>" for l in lines)
            out.append("</ul>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out).strip()


def parse_map(spec: str) -> dict:
    out = {}
    for pair in filter(None, (p.strip() for p in spec.split(","))):
        if "=" not in pair:
            sys.exit(f"init_items: bad --map entry {pair!r}; expected MARKER=status")
        marker, status = (x.strip() for x in pair.split("=", 1))
        if status not in STATUSES:
            sys.exit(f"init_items: unknown status {status!r}; one of {', '.join(STATUSES)}")
        out[marker] = status
    return out


def scan(path, lines, entries, entry_level):
    print(f"file            {path}  ({len(lines)} lines)")
    print(f"entry boundary  {entry_level}")
    print(f"entries found   {len(entries)}")
    secs = collections.Counter(e.section for e in entries)
    print(f"sections        {len(secs)}")
    for s, n in secs.most_common():
        print(f"                  {n:4}  {s}")
    marks = collections.Counter(m for e in entries for m in e.markers)
    if marks:
        print("markers         (decide what each MEANS, then pass --map)")
        for m, n in marks.most_common():
            ex = next(e.title for e in entries if m in e.markers)
            print(f"                  {n:4}  {m!r:12} e.g. {ex[:58]}")
    else:
        print("markers         none found — every entry takes --default-status")
    nomark = sum(1 for e in entries if not e.markers)
    if nomark:
        print(f"unmarked        {nomark} entries have no marker -> --default-status")
    print("sample entries  (check these ARE items — a file's own title line or a")
    print("                legend can look like one when there are no headers)")
    for e in entries[:6]:
        print(f"                  line {e.line:5}  {e.title[:66]}")
    if len(entries) > 6:
        print(f"                  ... and {len(entries) - 6} more")
    print("\nNothing was written. Re-run with --map to convert.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a hand-written TODO file into an item store.")
    ap.add_argument("source", help="the TODO file (any name)")
    ap.add_argument("--items-dir", default=None, help="default: <repo>/items next to itemlib")
    ap.add_argument("--scan", action="store_true", help="analyze and print; write nothing")
    ap.add_argument("--entry-level", default=None, help="header:N | bullet | para (default: auto)")
    ap.add_argument("--map", default="", help='e.g. "[x]=done,[ ]=backlog,🟡=in-progress"')
    ap.add_argument("--default-status", default="backlog", choices=STATUSES)
    ap.add_argument("--default-priority", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true", help="print what would be written")
    ap.add_argument("--force", action="store_true", help="write into a non-empty store")
    args = ap.parse_args()

    if not os.path.isfile(args.source):
        sys.exit(f"init_items: no such file: {args.source}")
    lines = open(args.source, encoding="utf-8").read().splitlines()
    entry_level = args.entry_level or detect_entry_level(lines)
    if entry_level != "bullet" and entry_level != "para" and not entry_level.startswith("header:"):
        sys.exit(f"init_items: bad --entry-level {entry_level!r}")
    entries = parse(lines, entry_level)
    if not entries:
        sys.exit(f"init_items: found no entries with --entry-level {entry_level}. "
                 f"Run with --scan, or set --entry-level explicitly.")

    if args.scan:
        scan(args.source, lines, entries, entry_level)
        return 0

    items_dir = args.items_dir or il.ITEMS_DIR
    existing = ([f for f in os.listdir(items_dir)
                 if f.endswith(".md") and f not in ("PLAN.md", "README.md")]
                if os.path.isdir(items_dir) else [])
    if existing and not args.force:
        sys.exit(f"init_items: {items_dir} already holds {len(existing)} item(s). "
                 f"Converting into a populated store merges two readings of the same "
                 f"file. Use --force only if that is what you mean.")

    mapping = parse_map(args.map)
    if not mapping:
        print("init_items: no --map given; every entry gets "
              f"--default-status {args.default_status}", file=sys.stderr)

    today = datetime.date.today().isoformat()
    if not args.dry_run:
        os.makedirs(items_dir, exist_ok=True)

    seen: dict[str, int] = {}
    written, by_status, unmapped = [], collections.Counter(), collections.Counter()
    for e in entries:
        status = args.default_status
        for m in e.markers:
            if m in mapping:
                status = mapping[m]
                break
        else:
            for m in e.markers:
                unmapped[m] += 1

        slug = il.slugify(e.title)
        if slug in seen:                       # deterministic disambiguation
            seen[slug] += 1
            hint = il.slugify(e.section)[:16]
            slug = il.slugify(f"{e.title} {hint}") or slug
            if slug in seen:
                slug = f"{slug}-{seen[slug if slug in seen else e.title]}"
        seen.setdefault(slug, 1)

        fm = {"id": slug, "title": e.title[:120], "section": e.section, "status": status,
              "priority": args.default_priority, "needs_spec": False,
              "created": today, "updated": today, "tests": []}
        by_status[status] += 1
        if args.dry_run:
            written.append(f"  {status:14} [{slug}]  {e.title[:64]}")
        else:
            written.append(il.write_item(items_dir, fm, to_html(e)))

    if args.dry_run:
        print("\n".join(written))
        print(f"\n-- dry run: {len(written)} item(s) NOT written to {items_dir}")
    else:
        print(f"wrote {len(written)} item(s) to {items_dir}")
    print("by status:", dict(by_status))
    if unmapped:
        print(f"NOTE {sum(unmapped.values())} entries had a marker absent from --map "
              f"and fell back to '{args.default_status}': "
              + ", ".join(f"{m!r}x{n}" for m, n in unmapped.most_common()))
    print(f"source {args.source} was NOT modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
