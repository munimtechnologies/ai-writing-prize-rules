# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for census.py (no network)."""
import csv
import json
import os
import shutil
import tempfile
import unittest

import census as c

PAGE = ("<html><head><title>Prize</title><script>var AI = 1; // AI must not leak</script></head><body>"
        "<nav><a href='/about'>About us</a></nav>"
        "<h1>The Prize</h1><p>Entries close soon. Read the rules before you enter.</p>"
        "<a href='/rules'>Full rules</a> <a href='https://example.com/faq#top'>FAQ</a> "
        "<a href='https://other.org/terms'>terms</a> <a href='/files/rules.pdf'>Rules PDF</a>"
        "<a href='mailto:x@example.com'>Submit by email</a></body></html>")


def ok(text):
    return {"status": 200, "tls": "verified", "final_url": None, "text": text, "error": None}


class Text(unittest.TestCase):
    def test_extract_drops_scripts_and_keeps_links(self):
        text, links = c.extract(PAGE)
        self.assertIn("Entries close soon.", text)
        self.assertNotIn("var AI", text)
        self.assertIn(("/rules", "Full rules"), links)

    def test_sentences_split_on_full_stops_and_lines(self):
        got = c.sentences("One rule. Two rules! Three\nFour.")
        self.assertEqual(got, ["One rule.", "Two rules!", "Three", "Four."])

    def test_ai_mentions(self):
        for s in ("AI-generated work will not be accepted.", "Use of A.I. tools", "No ChatGPT.",
                  "large language models", "Entries made by AIs", "Generative tools are banned."):
            self.assertTrue(c.mentions_ai(s), s)
        for s in ("We aim to publish.", "Writers from Maine", "An AIDS memoir", "she said", "Ai Weiwei"):
            self.assertFalse(c.mentions_ai(s), s)

    def test_ai_sentences_are_verbatim_and_unique(self):
        text = "Welcome. AI-generated entries will not be accepted. Fees apply.\nAI-generated entries will not be accepted."
        self.assertEqual(c.ai_sentences(text), ["AI-generated entries will not be accepted."])


class Links(unittest.TestCase):
    def test_follow_same_site_rules_links_only(self):
        _, links = c.extract(PAGE)
        follow, docs = c.follow_links("https://www.example.com/prize", links)
        self.assertEqual(follow, ["https://www.example.com/rules", "https://example.com/faq"])
        self.assertEqual(docs, ["https://www.example.com/files/rules.pdf"])

    def test_follow_limit(self):
        links = [("/rules-%d" % i, "rules") for i in range(9)]
        follow, _ = c.follow_links("https://a.org/", links, limit=3)
        self.assertEqual(len(follow), 3)


class Classify(unittest.TestCase):
    def test_labels(self):
        page = [{"chars": 1000}]
        self.assertEqual(c.classify([], []), ("unreachable", None))
        self.assertEqual(c.classify([{"chars": None}], []), ("unreachable", None))
        self.assertEqual(c.classify(page, []), ("silent", None))
        self.assertEqual(c.classify([{"chars": 100}], []), ("unreadable", None))
        self.assertEqual(c.classify(page, ["We will not use your entry to train AI models."]),
                         ("training_only", None))
        self.assertEqual(c.classify(page, ["AI-generated work will not be accepted."]), ("ban", "generated"))
        self.assertEqual(c.classify(page, ["Entries written or edited with AI tools are not eligible."]),
                         ("ban", "assisted"))
        self.assertEqual(c.classify(page, ["You may use AI if you disclose it in your cover letter."]),
                         ("allow_or_conditional", None))
        self.assertEqual(c.classify(page, ["The theme this year is AI and the future."]), ("other_mention", None))


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_census_run(self):
        contests = os.path.join(self.dir, "contests.csv")
        with open(contests, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "name", "listings", "deadline_listed", "fee", "url", "extra_urls"])
            w.writerow(["p1", "Prize One", "W-ND", "2026-11-30", "yes", "https://www.example.com/prize", ""])
            w.writerow(["p2", "Prize Two", "NCW;W-FREE", "2026-12-01", "no", "https://two.org/", ""])
        pages = {
            c.LISTINGS["W-ND"]: ok("<p>Prize One: <a href='https://www.example.com/prize'>enter</a></p>"),
            c.LISTINGS["NCW"]: ok("<p>Nothing about it. AI is everywhere these days.</p>"),
            "https://www.example.com/prize": ok(PAGE),
            "https://www.example.com/rules": ok("<p>" + "Long rules text. " * 40 +
                                                "Entries written or edited with AI tools are not eligible.</p>"),
            "https://example.com/faq": ok("<p>Questions and answers.</p>"),
            "https://two.org/": ok("<p>" + "A prize for poems. " * 40 + "</p>"),
        }
        fetched = []

        def fetcher(url):
            fetched.append(url)
            if url in pages:
                got = dict(pages[url])
                got["final_url"] = url
                return got
            return {"status": 404, "tls": "verified", "final_url": url, "text": None, "error": "HTTP Error 404"}

        def opener(req):
            return json.dumps([{"sha": "b", "commit": {"committer": {"date": "2026-11-02T05:00:00Z"}}},
                               {"sha": "a", "commit": {"committer": {"date": "2026-11-02T04:50:00Z"}}}]).encode()

        out = os.path.join(self.dir, "out")
        rc = c.main(["--contests", contests, "--out-dir", out, "--pause", "0", "--save-text"],
                    fetcher=fetcher, opener=opener)
        self.assertEqual(rc, 0)
        self.assertNotIn("https://other.org/terms", fetched)
        with open(os.path.join(out, "census.json"), encoding="utf-8") as fh:
            res = json.load(fh)
        self.assertEqual(res["prereg"]["committed_at"], "2026-11-02T04:50:00Z")
        p1, p2 = res["contests"]
        self.assertEqual((p1["auto_label"], p1["auto_scope"]), ("ban", "assisted"))
        self.assertEqual(p1["url_in_listing"], {"W-ND": True})
        self.assertEqual(p1["documents_not_read"], ["https://www.example.com/files/rules.pdf"])
        self.assertEqual(len(p1["pages"]), 3)
        self.assertEqual(p2["auto_label"], "silent")
        self.assertEqual(p2["url_in_listing"], {"NCW": False, "W-FREE": None})
        with open(os.path.join(out, "listings.json"), encoding="utf-8") as fh:
            listings = json.load(fh)
        self.assertEqual(listings["NCW"]["ai_sentences"], ["AI is everywhere these days."])
        self.assertNotIn("html", listings["NCW"])
        with open(os.path.join(out, "sentences.csv"), newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual([r["contest_id"] for r in rows], ["p1"])
        self.assertEqual(rows[0]["sentence"], "Entries written or edited with AI tools are not eligible.")
        self.assertTrue(os.path.exists(os.path.join(out, "pages", "p1-0.txt")))
        with open(os.path.join(out, "CENSUS_AUTO.md"), encoding="utf-8") as fh:
            self.assertIn("| ban | 1 |", fh.read())


class Frame(unittest.TestCase):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "census", "2026-11", "contests.csv")

    @unittest.skipUnless(os.path.exists(path), "frame file not copied")
    def test_frame_loads(self):
        rows = c.read_contests(self.path)
        self.assertEqual(len(rows), 54)
        self.assertTrue(all(r["fee"] in ("yes", "no", "unknown") for r in rows))


if __name__ == "__main__":
    unittest.main()
