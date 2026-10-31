# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Check prizes.csv: every row has the required fields, known values and a dated source.

Usage: python check_prizes.py [path]   (default: prizes.csv next to this file)
Prints "ok N rows" and exits 0, or lists each problem and exits 1.

Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import csv
import io
import os
import re
import sys

VERSION = "0.1.0"
FIELDS = ["id", "prize", "organiser", "entry_language", "edition", "deadline", "deadline_note",
          "top_prize", "ai_policy", "mostly_ai_text", "human_revision_required", "disclosure_where",
          "records_on_request", "entrant_rule", "quote", "quote_language", "source_url",
          "source_type", "checked"]
REQUIRED = ["id", "prize", "organiser", "entry_language", "edition", "ai_policy", "mostly_ai_text",
            "human_revision_required", "disclosure_where", "records_on_request", "quote",
            "quote_language", "source_url", "source_type", "checked"]
ALLOWED = {
    "ai_policy": {"ai_required", "allowed_with_disclosure", "banned"},
    # How much AI-written text the rules let a work contain.
    "mostly_ai_text": {"required", "yes", "one_per_entrant", "human_revised_only",
                       "no_limit_stated", "no"},
    "human_revision_required": {"yes", "no", "not_stated", "not_applicable"},
    "records_on_request": {"yes", "no", "not_stated", "not_applicable"},
    "source_type": {"official", "secondary"},
}
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LANG = re.compile(r"^[a-z]{2}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read(fh):
    reader = csv.DictReader(fh)
    return reader.fieldnames, list(reader)


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return read(fh)


def parse(text):
    return read(io.StringIO(text, newline=""))


def problems(fieldnames, rows):
    if fieldnames != FIELDS:
        return ["header: expected " + ",".join(FIELDS)]
    out = []
    seen = set()
    for n, row in enumerate(rows, start=2):
        where = "line %d (%s)" % (n, row.get("id") or "?")
        if None in row or None in row.values():
            out.append("%s: wrong number of fields" % where)
            continue
        for name in REQUIRED:
            if not row[name].strip():
                out.append("%s: %s is empty" % (where, name))
        for name, values in ALLOWED.items():
            if row[name] and row[name] not in values:
                out.append("%s: %s %r is not one of %s" % (where, name, row[name], sorted(values)))
        if row["id"] and not ID.match(row["id"]):
            out.append("%s: id must be lower-case words joined by hyphens" % where)
        if row["id"] in seen:
            out.append("%s: duplicate id" % where)
        seen.add(row["id"])
        for name in ("entry_language", "quote_language"):
            if row[name] and not LANG.match(row[name]):
                out.append("%s: %s must be a two-letter code" % (where, name))
        if row["deadline"] and not DATE.match(row["deadline"]):
            out.append("%s: deadline must be YYYY-MM-DD" % where)
        if row["checked"] and not DATE.match(row["checked"]):
            out.append("%s: checked must be YYYY-MM-DD" % where)
        if row["source_url"] and not row["source_url"].startswith("https://"):
            out.append("%s: source_url must start with https://" % where)
        banned = row["ai_policy"] == "banned"
        if banned != (row["mostly_ai_text"] == "no"):
            out.append("%s: mostly_ai_text must be 'no' exactly when ai_policy is 'banned'" % where)
        if banned and (row["human_revision_required"], row["records_on_request"]) != ("not_applicable",) * 2:
            out.append("%s: a banned row has nothing to revise or record (use not_applicable)" % where)
        if not banned and "not_applicable" in (row["human_revision_required"], row["records_on_request"]):
            out.append("%s: not_applicable is only for banned rows" % where)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "prizes.csv")
    fieldnames, rows = load(path)
    found = problems(fieldnames, rows)
    for p in found:
        print(p)
    if found:
        return 1
    print("ok %d rows" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
