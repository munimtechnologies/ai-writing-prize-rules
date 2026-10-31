# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Tests for check_prizes.py, run on the shipped prizes.csv and on broken copies of a row."""
import csv
import io
import os
import unittest

import check_prizes as cp

HERE = os.path.dirname(os.path.abspath(__file__))

GOOD = {
    "id": "example-prize-1", "prize": "Example Prize", "organiser": "Example Press",
    "entry_language": "en", "edition": "1st", "deadline": "2027-01-31", "deadline_note": "",
    "top_prize": "$100", "ai_policy": "allowed_with_disclosure", "mostly_ai_text": "yes",
    "human_revision_required": "no", "disclosure_where": "Entry form", "records_on_request": "not_stated",
    "entrant_rule": "", "quote": "AI use must be disclosed.", "quote_language": "en",
    "source_url": "https://example.org/rules", "source_type": "official", "checked": "2026-10-31",
}


def text(*rows, fields=cp.FIELDS):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def found(**changes):
    row = dict(GOOD, **changes)
    return cp.problems(*cp.parse(text(row)))


class ShippedData(unittest.TestCase):
    def test_prizes_csv_is_clean(self):
        fieldnames, rows = cp.load(os.path.join(HERE, "prizes.csv"))
        self.assertEqual(cp.problems(fieldnames, rows), [])
        self.assertGreaterEqual(len(rows), 9)

    def test_every_policy_is_present(self):
        _, rows = cp.load(os.path.join(HERE, "prizes.csv"))
        self.assertEqual({r["ai_policy"] for r in rows}, cp.ALLOWED["ai_policy"])

    def test_main_reports_ok(self):
        self.assertEqual(cp.main([os.path.join(HERE, "prizes.csv")]), 0)


class Checks(unittest.TestCase):
    def test_good_row_passes(self):
        self.assertEqual(found(), [])

    def test_bad_header(self):
        fields = cp.FIELDS[:-1]
        row = {k: GOOD[k] for k in fields}
        self.assertEqual(len(cp.problems(*cp.parse(text(row, fields=fields)))), 1)

    def test_short_row(self):
        broken = text(GOOD).rstrip("\n").rsplit(",", 1)[0] + "\n"
        self.assertIn("wrong number of fields", cp.problems(*cp.parse(broken))[0])

    def test_empty_required_field(self):
        self.assertIn("quote is empty", found(quote=" ")[0])

    def test_unknown_value(self):
        self.assertIn("ai_policy", found(ai_policy="maybe")[0])

    def test_duplicate_id(self):
        out = cp.problems(*cp.parse(text(GOOD, GOOD)))
        self.assertEqual(out, ["line 3 (example-prize-1): duplicate id"])

    def test_bad_id(self):
        self.assertIn("id must be", found(id="Example Prize")[0])

    def test_bad_dates(self):
        self.assertIn("deadline", found(deadline="31 Jan 2027")[0])
        self.assertIn("checked", found(checked="2026/10/31")[0])

    def test_empty_deadline_is_allowed(self):
        self.assertEqual(found(deadline=""), [])

    def test_http_source(self):
        self.assertIn("https", found(source_url="http://example.org/rules")[0])

    def test_language_code(self):
        self.assertIn("two-letter", found(quote_language="eng")[0])

    def test_banned_needs_no_ai_text(self):
        out = found(ai_policy="banned", human_revision_required="not_applicable",
                    records_on_request="not_applicable")
        self.assertEqual(len(out), 1)
        self.assertIn("mostly_ai_text", out[0])

    def test_banned_row_is_consistent(self):
        self.assertEqual(found(ai_policy="banned", mostly_ai_text="no",
                               human_revision_required="not_applicable",
                               records_on_request="not_applicable"), [])

    def test_banned_needs_not_applicable(self):
        out = found(ai_policy="banned", mostly_ai_text="no")
        self.assertEqual(len(out), 1)
        self.assertIn("not_applicable", out[0])

    def test_not_applicable_only_when_banned(self):
        self.assertIn("only for banned", found(records_on_request="not_applicable")[0])


if __name__ == "__main__":
    unittest.main()
