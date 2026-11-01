# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Re-check every quote in prizes.csv against its live source page.

Usage: python verify_quotes.py [--csv FILE ...] [--out-dir DIR] [--save-text]
                               [--insecure-retry] [--report-only]

Each source_url is fetched once. The page is turned into text and every piece of the row's
quote (pieces are joined with " / ") is looked for in it:
  exact      found as written, after HTML entities are decoded and runs of whitespace folded
  in_source  found only in the page source outside the visible text (scripts, JSON data)
  folded     found only after Unicode NFKC, case and quote-mark folding and removing all
             whitespace (a line break inside a Japanese sentence, a curly apostrophe)
  missing    not found
Writes verify.json and VERIFY.md to --out-dir. Exits 1 if a piece is missing or a page
could not be fetched, unless --report-only.

Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
"""
import argparse
import html
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request

import check_prizes

VERSION = "0.1.0"
USER_AGENT = ("ai-writing-prize-rules-verify/%s (+https://github.com/munimtechnologies/"
              "ai-writing-prize-rules)" % VERSION)
LEVELS = ["exact", "in_source", "folded", "missing"]
CHARSET_ALIASES = {"shift_jis": "cp932", "shift-jis": "cp932", "sjis": "cp932", "x-sjis": "cp932",
                   "euc-kr": "cp949", "ks_c_5601-1987": "cp949", "gb2312": "gb18030", "gbk": "gb18030"}
META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?([A-Za-z0-9_.:-]+)""", re.I)
HIDDEN = re.compile(r"<(script|style|noscript|template)\b.*?</\1\s*>|<!--.*?-->", re.I | re.S)
TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")
UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")
QUOTE_MARKS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                             "«": '"', "»": '"'})


def pieces(quote):
    return [p.strip() for p in quote.split(" / ") if p.strip()]


def decode(body, header_charset=None):
    """Bytes to text: the HTTP charset, then a <meta> charset, then UTF-8; returns (text, charset)."""
    tried = []
    m = META_CHARSET.search(body[:8192])
    for cs in (header_charset, m.group(1).decode("ascii") if m else None, "utf-8"):
        if not cs:
            continue
        cs = CHARSET_ALIASES.get(cs.lower(), cs.lower())
        if cs in tried:
            continue
        tried.append(cs)
        try:
            return body.decode(cs), cs
        except (LookupError, UnicodeDecodeError):
            pass
    return body.decode("utf-8", errors="replace"), "utf-8 (with replacements)"


def fold_space(text):
    return SPACE.sub(" ", text).strip()


def visible_texts(page):
    """Two readings of the visible text: tags dropped, and tags replaced by a space."""
    body = HIDDEN.sub(" ", page)
    return [fold_space(html.unescape(TAG.sub(sep, body))) for sep in ("", " ")]


def source_text(page):
    page = UNICODE_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), page)
    return fold_space(html.unescape(page.replace("\\/", "/")))


def folded(text):
    text = unicodedata.normalize("NFKC", text).translate(QUOTE_MARKS).casefold()
    return SPACE.sub("", text)


def level(piece, page):
    """How well one quote piece is found in a decoded page (one of LEVELS)."""
    want = fold_space(piece)
    texts = visible_texts(page)
    if any(want in t for t in texts):
        return "exact"
    source = source_text(page)
    if want in source:
        return "in_source"
    want_f = folded(piece)
    if any(want_f in folded(t) for t in texts + [source]):
        return "folded"
    return "missing"


def fetch(url, insecure_retry=False, timeout=30):
    """Returns a dict with status, charset, tls and body (bytes or None) and error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "text/html,application/xhtml+xml,*/*"})
    contexts = [("verified", None)]
    if insecure_retry:
        contexts.append(("unverified", ssl._create_unverified_context()))
    error = None
    for tls, ctx in contexts:
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return {"status": resp.status, "charset": resp.headers.get_content_charset(),
                        "tls": tls, "body": resp.read(), "error": None}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "charset": None, "tls": tls, "body": None, "error": str(e)}
        except (urllib.error.URLError, ssl.SSLError, OSError) as e:
            error = str(getattr(e, "reason", e))
            if "CERTIFICATE" not in error.upper():
                break
    return {"status": None, "charset": None, "tls": None, "body": None, "error": error}


def verify(rows, fetcher=fetch, pause=1.0):
    """Check every row's quote pieces; each URL is fetched once."""
    pages = {}
    results = []
    for row in rows:
        url = row["source_url"]
        if url not in pages:
            if pages and pause:
                time.sleep(pause)
            got = fetcher(url)
            text, charset = decode(got["body"], got["charset"]) if got["body"] is not None else (None, None)
            pages[url] = dict(got, text=text, decoded_as=charset)
        page = pages[url]
        found = [{"piece": p, "level": level(p, page["text"]) if page["text"] is not None else "missing"}
                 for p in pieces(row["quote"])]
        if page["text"] is None:
            result = "fetch_failed"
        elif all(f["level"] == "exact" for f in found):
            result = "exact"
        elif any(f["level"] == "missing" for f in found):
            result = "missing"
        else:
            result = "found_with_folding"
        results.append({"id": row["id"], "source_url": url, "status": page["status"],
                        "tls": page["tls"], "decoded_as": page["decoded_as"], "error": page["error"],
                        "result": result, "pieces": found})
    return results, pages


def markdown(results, checked_at):
    lines = ["# Quote check (%s)" % checked_at, "",
             "verify_quotes.py %s. One row per prize; a piece is a sentence of the quote." % VERSION, "",
             "| id | HTTP | TLS | pieces exact / all | result |", "|---|---|---|---|---|"]
    for r in results:
        exact = sum(1 for p in r["pieces"] if p["level"] == "exact")
        lines.append("| %s | %s | %s | %d / %d | %s |" % (r["id"], r["status"] or r["error"], r["tls"] or "-",
                                                         exact, len(r["pieces"]), r["result"]))
    bad = [r for r in results if r["result"] != "exact"]
    if bad:
        lines += ["", "## Not exact", ""]
        for r in bad:
            lines.append("- %s (%s): %s" % (r["id"], r["result"], "; ".join(
                "%s = %s" % (p["piece"][:60], p["level"]) for p in r["pieces"] if p["level"] != "exact")
                or r["error"]))
    counts = {k: sum(1 for r in results if r["result"] == k)
              for k in ("exact", "found_with_folding", "missing", "fetch_failed")}
    lines += ["", "Totals: " + ", ".join("%s %d" % kv for kv in counts.items()), ""]
    return "\n".join(lines)


def main(argv=None, fetcher=fetch):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", action="append", help="prize table(s) to check (default: prizes.csv)")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--save-text", action="store_true", help="also save each page's visible text")
    ap.add_argument("--insecure-retry", action="store_true",
                    help="if a certificate cannot be verified, read the page anyway and mark it")
    ap.add_argument("--report-only", action="store_true", help="always exit 0")
    ap.add_argument("--pause", type=float, default=1.0)
    args = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    rows = []
    for path in args.csv or [os.path.join(here, "prizes.csv")]:
        fieldnames, got = check_prizes.load(path)
        found = check_prizes.problems(fieldnames, got)
        if found:
            print("%s: %s" % (path, found[0]))
            return 2
        rows += got
    results, pages = verify(rows, fetcher=lambda u: fetcher(u, args.insecure_retry), pause=args.pause)
    checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "verify.json"), "w", encoding="utf-8") as fh:
        json.dump({"version": VERSION, "checked_at": checked_at, "results": results}, fh,
                  ensure_ascii=False, indent=1)
    report = markdown(results, checked_at)
    with open(os.path.join(args.out_dir, "VERIFY.md"), "w", encoding="utf-8") as fh:
        fh.write(report)
    if args.save_text:
        os.makedirs(os.path.join(args.out_dir, "pages"), exist_ok=True)
        for r in results:
            text = pages[r["source_url"]]["text"]
            if text is not None:
                with open(os.path.join(args.out_dir, "pages", r["id"] + ".txt"), "w", encoding="utf-8") as fh:
                    fh.write(visible_texts(text)[1])
    print(report)
    if args.report_only:
        return 0
    return 0 if all(r["result"] == "exact" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
