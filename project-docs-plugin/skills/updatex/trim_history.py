#!/usr/bin/env python3
"""Trim ./history.md to a rolling window of recent days.

Older entries are MOVED (never deleted) into ./history-archive.md. Both files
keep newest-entries-first. Sections are delimited by top-level '## ' headings
that contain a YYYY-MM-DD date; '### ' sub-headings and body text stay attached
to their parent '## ' section. Any leading preamble before the first dated
section (the '# Title' line, intro paragraphs) is always kept in history.md.

Idempotent: re-running the same day moves nothing new. A missing history.md is
treated as "nothing to do" (the project may legitimately not have one); a
section whose heading has no parseable date is KEPT (never archived on a guess)
and reported as a warning.

Usage:  trim_history.py [DAYS]        (DAYS defaults to 7; run from the repo root)
        trim_history.py -d DAYS
"""
import datetime
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_DAYS = 7
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
HISTORY = Path("history.md")
ARCHIVE = Path("history-archive.md")
ARCHIVE_TITLE = "# Development History — Archive (older entries trimmed from history.md)\n"


def parse_date(heading):
    m = DATE_RE.search(heading)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def split_sections(text):
    """(preamble_text, [(date_or_None, section_text), ...]) preserving order.
    A section starts at a line beginning with '## ' (exactly two hashes + space)."""
    preamble, sections, cur = [], [], None
    for line in text.splitlines(keepends=True):
        if line.startswith("## ") and not line.startswith("###"):
            if cur is not None:
                sections.append(cur)
            cur = [line]
        elif cur is None:
            preamble.append(line)
        else:
            cur.append(line)
    if cur is not None:
        sections.append(cur)
    parsed = [(parse_date(sec[0]), "".join(sec)) for sec in sections]
    return "".join(preamble), parsed


def parse_days(args):
    """DAYS from the command line. Bad input is an error, never a silent default."""
    if not args:
        return DEFAULT_DAYS
    if args[0] in ("-d", "--days"):
        if len(args) < 2:
            sys.exit(f"trim_history: {args[0]} needs a number of days")
        raw = args[1]
    else:
        raw = args[0]
    try:
        days = int(raw)
    except ValueError:
        sys.exit(f"trim_history: '{raw}' is not a number of days")
    if days < 0:
        sys.exit("trim_history: days must not be negative")
    return days


def main():
    days = parse_days(sys.argv[1:])

    if not HISTORY.exists():
        print("trim_history: no history.md in this directory — nothing to trim.")
        return 0

    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    preamble, sections = split_sections(HISTORY.read_text())

    keep, archive, undated = [], [], 0
    for d, body in sections:
        if d is None:
            undated += 1
            keep.append(body)            # never archive what we can't date
        elif d >= cutoff:
            keep.append(body)
        else:
            archive.append((d, body))

    if not archive:
        print(f"trim_history: nothing older than {cutoff} "
              f"(kept {len(keep)} section(s)); history.md unchanged.")
        return 0

    archived_text = "".join(body for _, body in archive)
    newly_created = not ARCHIVE.exists()
    if newly_created:
        existing_body = ""
    else:
        old = ARCHIVE.read_text()
        existing_body = old[old.find("\n") + 1:] if old.startswith("# ") else old

    # Newly-archived batch is newer than whatever is already archived → goes on top.
    ARCHIVE.write_text(ARCHIVE_TITLE + "\n" + archived_text + existing_body.lstrip("\n"))
    HISTORY.write_text(preamble + "".join(keep))

    moved = [d for d, _ in archive]
    print(f"trim_history: kept {len(keep)} section(s) (>= {cutoff}), "
          f"archived {len(archive)} section(s) ({min(moved)} … {max(moved)}).")
    if undated:
        print(f"trim_history: WARNING {undated} section(s) had no parseable date — "
              f"kept in history.md to be safe.")
    print(f"trim_history: history.md now {HISTORY.stat().st_size:,} bytes; "
          f"history-archive.md {ARCHIVE.stat().st_size:,} bytes.")

    if newly_created:
        try:
            inside = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True, text=True).stdout.strip()
        except FileNotFoundError:
            inside = ""
        if inside == "true":
            print("trim_history: NOTE history-archive.md is NEW and untracked — run "
                  "`git add history-archive.md` so your next commit includes it "
                  "(git commit -a skips untracked files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
