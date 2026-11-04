# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Offline tests for census.py (no internet; one test uses a server on 127.0.0.1)."""
import csv
import http.server
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

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

    def test_curly_apostrophe(self):
        # 0.1.1: 0.1.0 read this as allow_or_conditional ("accepted"), missing the curly "won’t".
        page = [{"chars": 1000}]
        self.assertEqual(c.classify(page, ["AI-generated entries won’t be accepted."]), ("ban", "generated"))


class CookieLoop(http.server.BaseHTTPRequestHandler):
    """Redirects to itself (HTTP 307) and sets a cookie until the cookie comes back, as some contest sites do."""

    def do_GET(self):
        if self.path == "/nolocation":  # a 307 with no Location header: urllib cannot follow it
            self.send_response(307)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if "seen=1" in (self.headers.get("Cookie") or ""):
            body = b"<html><body><p>Entries must be your own work.</p></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(307)
            self.send_header("Set-Cookie", "seen=1; Path=/")
            self.send_header("Location", self.path)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def log_message(self, *args):
        pass


class Fetch(unittest.TestCase):
    def setUp(self):
        try:
            self.srv = http.server.HTTPServer(("127.0.0.1", 0), CookieLoop)
        except OSError as exc:  # no loopback sockets in this sandbox
            self.skipTest("cannot listen on 127.0.0.1: %s" % exc)
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:%d/rules" % self.srv.server_address[1]

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def test_cookie_redirect_is_followed(self):
        got = c.fetch(self.url, timeout=10, proxies={})
        self.assertEqual(got["status"], 200, got["error"])
        self.assertIn("Entries must be your own work.", got["text"])
        self.assertEqual(got["final_url"], self.url)

    def test_redirect_without_location_is_recorded(self):
        url = self.url.replace("/rules", "/nolocation")
        got = c.fetch(url, timeout=10, proxies={})
        self.assertEqual(got["status"], 307)
        self.assertEqual(got["error"], "HTTP Error 307: Temporary Redirect")
        self.assertIn("location", got)
        self.assertIsNone(got["location"])
        self.assertIsNone(got["text"])

    def test_without_a_cookie_jar_it_loops(self):
        # How 0.1.0 failed: no cookie jar, so urllib gives up with HTTP 307 after repeated redirects.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with self.assertRaises(urllib.error.HTTPError) as cm:
            opener.open(self.url, timeout=10)
        self.assertEqual(cm.exception.code, 307)
        cm.exception.close()


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
        self.assertEqual(res["version"], "0.1.1")
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
