# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Tests for verify_quotes.py, with fake pages instead of the network."""
import json
import os
import tempfile
import unittest

import check_prizes as cp
import verify_quotes as vq

HERE = os.path.dirname(os.path.abspath(__file__))


def page(body, charset="utf-8", status=200):
    return {"status": status, "charset": charset, "tls": "verified", "body": body, "error": None}


class Pieces(unittest.TestCase):
    def test_split_on_slash(self):
        self.assertEqual(vq.pieces("One. / Two. "), ["One.", "Two."])

    def test_slash_inside_a_sentence_is_kept(self):
        self.assertEqual(vq.pieces("and/or process"), ["and/or process"])

    def test_every_shipped_row_has_pieces(self):
        _, rows = cp.load(os.path.join(HERE, "prizes.csv"))
        for row in rows:
            self.assertTrue(vq.pieces(row["quote"]), row["id"])


class Decode(unittest.TestCase):
    def test_header_charset_wins(self):
        self.assertEqual(vq.decode("生成AI".encode("cp932"), "Shift_JIS"), ("生成AI", "cp932"))

    def test_meta_charset(self):
        body = b'<meta charset="euc-kr">' + "제작".encode("cp949")
        self.assertEqual(vq.decode(body)[1], "cp949")
        self.assertIn("제작", vq.decode(body)[0])

    def test_wrong_header_falls_back_to_utf8(self):
        self.assertEqual(vq.decode("é".encode("utf-8"), "ascii"), ("é", "utf-8"))

    def test_undecodable_is_replaced(self):
        text, how = vq.decode(b"\xff\xfe\xfa")
        self.assertIn("replacements", how)


class Level(unittest.TestCase):
    def test_exact_across_inline_tags_and_entities(self):
        html = "<p>AI is <strong>not</strong>&nbsp;accepted.</p>"
        self.assertEqual(vq.level("AI is not accepted.", html), "exact")

    def test_hidden_text_is_not_visible(self):
        html = "<script>var rule = 'AI is not accepted.';</script><p>Rules</p>"
        self.assertEqual(vq.level("AI is not accepted.", html), "in_source")

    def test_unicode_escaped_json(self):
        html = '<script>{"t":"\\uc81c\\uc791"}</script>'
        self.assertEqual(vq.level("제작", html), "in_source")

    def test_line_break_inside_japanese_sentence_is_folded(self):
        html = "<p>具体的な使用方法を\n明記すること。</p>"
        self.assertEqual(vq.level("具体的な使用方法を明記すること。", html), "folded")

    def test_curly_apostrophe_and_case_are_folded(self):
        html = "<p>Texts originating from AI aren’t eligible.</p>"
        self.assertEqual(vq.level("texts originating from AI aren't eligible.", html), "folded")

    def test_full_width_is_folded(self):
        self.assertEqual(vq.level("AI", "<p>ＡＩ</p>"), "folded")

    def test_missing(self):
        self.assertEqual(vq.level("AI is welcome.", "<p>AI is not accepted.</p>"), "missing")

    def test_exact_needs_every_word(self):
        self.assertEqual(vq.level("AI is not accepted.", "<p>AI is accepted.</p>"), "missing")

    def test_script_rendered_page_has_no_rule_text(self):
        # Pages built by JavaScript (like the Naver notice left out of the table) come back as a title only.
        self.assertEqual(vq.level("생성형 AI", "<title>웹소설::공지사항</title><div id=app></div>"), "missing")


ROWS = [dict(id="a", source_url="https://example.org/1", quote="One rule. / Two rule."),
        dict(id="b", source_url="https://example.org/1", quote="Three rule."),
        dict(id="c", source_url="https://example.org/2", quote="Gone."),
        dict(id="d", source_url="https://example.org/3", quote="Bent rule.")]
PAGES = {"https://example.org/1": page(b"<p>One rule.</p><p>Two rule.</p>"),
         "https://example.org/2": {"status": 403, "charset": None, "tls": "verified", "body": None,
                                   "error": "HTTP Error 403: Forbidden"},
         "https://example.org/3": page(b"<p>bent RULE.</p>")}


class Verify(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def fetcher(url):
            self.calls.append(url)
            return PAGES[url]
        self.results, _ = vq.verify(ROWS, fetcher=fetcher, pause=0)

    def test_each_url_fetched_once(self):
        self.assertEqual(self.calls, ["https://example.org/1", "https://example.org/2", "https://example.org/3"])

    def test_results(self):
        self.assertEqual([r["result"] for r in self.results], ["exact", "missing", "fetch_failed", "found_with_folding"])

    def test_report_lists_problems(self):
        md = vq.markdown(self.results, "2026-10-31T00:00:00Z")
        self.assertIn("| a | 200 | verified | 2 / 2 | exact |", md)
        self.assertIn("- b (missing): Three rule. = missing", md)
        self.assertIn("- c (fetch_failed): Gone. = missing", md)
        self.assertIn("Totals: exact 1, found_with_folding 1, missing 1, fetch_failed 1", md)


class Main(unittest.TestCase):
    def run_main(self, *extra):
        out = tempfile.mkdtemp()
        fake = lambda url, insecure: page(b"<p>AI use must be disclosed.</p>")
        csv_text = ",".join(cp.FIELDS) + "\n" + ",".join([
            "x-1", "X", "Y", "en", "1", "", "", "", "allowed_with_disclosure", "yes", "no", "form",
            "not_stated", "", "AI use must be disclosed.", "en", "https://example.org/x", "official",
            "2026-10-31"]) + "\n"
        path = os.path.join(out, "t.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(csv_text)
        code = vq.main(["--csv", path, "--out-dir", out, "--save-text", "--pause", "0"] + list(extra), fetcher=fake)
        return code, out

    def test_writes_reports_and_text(self):
        code, out = self.run_main()
        self.assertEqual(code, 0)
        with open(os.path.join(out, "verify.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["results"][0]["result"], "exact")
        self.assertTrue(os.path.exists(os.path.join(out, "VERIFY.md")))
        with open(os.path.join(out, "pages", "x-1.txt"), encoding="utf-8") as fh:
            self.assertIn("AI use must be disclosed.", fh.read())

    def test_bad_table_is_refused(self):
        out = tempfile.mkdtemp()
        path = os.path.join(out, "bad.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("id,quote\nx,y\n")
        self.assertEqual(vq.main(["--csv", path, "--out-dir", out]), 2)


if __name__ == "__main__":
    unittest.main()
