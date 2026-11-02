# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Census of what writing contests' own pages say about AI.

Usage: python census.py --contests census/2026-11/contests.csv --out-dir OUT [--save-text]
                        [--pause 1.0] [--prereg-path census/2026-11/PREREGISTRATION.md]

For every contest in the frame (a CSV built from public contest listings), it fetches the contest's page(s)
and up to MAX_FOLLOW same-site links whose text or path looks like rules, terms, FAQ or submission guidelines.
From the visible text it keeps, word for word, every sentence that mentions AI (the capitalised token "AI",
"artificial intelligence", ChatGPT, LLM, generative, machine-generated and similar). It also fetches the
listing pages, keeps their AI sentences, and checks that each contest URL really appears in its listing.

A deterministic first-pass label is given to each contest (see classify()); the census's primary coding is
done afterwards by reading the saved sentences against the rubric in the pre-registration, and both are
published.

Writes census.json, sentences.csv, listings.json and CENSUS_AUTO.md to --out-dir (and pages/*.txt with
--save-text). Standard library only. Made by MV2 of Munim, Inc., with AI agents working in his name.
Apache-2.0.
"""
import argparse
import csv
import html
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

VERSION = "0.1.0"
USER_AGENT = ("ai-writing-prize-rules-census/%s (+https://github.com/munimtechnologies/"
              "ai-writing-prize-rules)" % VERSION)
REPO_API = "https://api.github.com/repos/munimtechnologies/ai-writing-prize-rules/commits"
MAX_FOLLOW = 5
MIN_CHARS = 500  # a contest whose pages all have less visible text than this is "unreadable"

LISTINGS = {
    "W-ND": "https://wroteabook.org/writing-competitions-november-december-2026/",
    "NCW": "https://www.newcastlecreativewriters.com.au/post/writing-competitions-closing-november-2026",
    "W-FREE": "https://wroteabook.org/free-writing-contests-october-2026/",
}

# "AI" is matched case-sensitively so that words such as "aim", "said" or "Maine" never count.
AI_TOKEN = re.compile(r"(?<![A-Za-z0-9])A\.?Is?(?![A-Za-z0-9])")
AI_WORDS = re.compile(
    r"artificial[\s-]+intelligence|chat\s?gpt|\bLLMs?\b|large[\s-]+language[\s-]+models?|\bgenerative\b|"
    r"machine[\s-]+generated|computer[\s-]+generated|\bchat\s?bots?\b|\bgrammarly\b|\bcopilot\b|"
    r"\bclaude\b|\bgemini\b|\bmidjourney\b|text[\s-]+generat\w*", re.I)

BAN_CUE = re.compile(
    r"\b(not|no|never|nor|prohibit\w*|ban|bans|banned|disqualif\w*|ineligible|cannot|can't|won't|"
    r"forbid\w*|reject\w*|exclud\w*|refuse\w*)\b|"
    r"must be (?:\w+ )?(?:your own|original|human)|human[\s-]+(?:written|authored|created|made)|"
    r"written by (?:a )?human|entirely human", re.I)
ASSIST_CUE = re.compile(r"assist\w*|aided|\bany (?:use|form|kind)|\btools?\b|in any (?:way|form|part)|"
                        r"partial\w*|\bedit\w*|grammar|spell", re.I)
ALLOW_CUE = re.compile(r"\b(allow\w*|permit\w*|welcome\w*|may use|can use|accept\w*|disclos\w*|declar\w*|"
                       r"acknowledg\w*)\b", re.I)
TRAIN_CUE = re.compile(r"\btrain(?:s|ing|ed)?\b|\bscrap\w*|\bdatasets?\b|\bmachine learning\b", re.I)

FOLLOW_TEXT = re.compile(r"\b(rules?|terms|guidelines?|faqs?|eligibility|conditions|how to enter|"
                         r"submissions?|submit|enter)\b", re.I)
FOLLOW_PATH = re.compile(r"rules|terms|guideline|faq|eligib|condition|how-to-enter|submi", re.I)
BINARY = re.compile(r"\.(pdf|docx?|jpe?g|png|gif|zip|mp3|mp4)$", re.I)

SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td", "th",
              "section", "article", "header", "footer", "nav", "table", "blockquote", "dd", "dt", "form",
              "main", "aside", "figcaption", "hr", "label", "option", "summary", "details"}
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[\"'“‘(\[]?[A-Z0-9])")
SPACE = re.compile(r"\s+")


class Extract(HTMLParser):
    """Visible text with line breaks at block elements, plus every link (href, anchor text)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links = [], []
        self.skip = 0
        self.href, self.anchor = None, []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.anchor = []

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "a" and self.href is not None:
            self.links.append((self.href, SPACE.sub(" ", "".join(self.anchor)).strip()))
            self.href = None

    def handle_data(self, data):
        if self.skip:
            return
        self.parts.append(data)
        if self.href is not None:
            self.anchor.append(data)


def extract(page):
    p = Extract()
    try:
        p.feed(page)
        p.close()
    except Exception:  # malformed HTML: keep what was parsed
        pass
    lines = [SPACE.sub(" ", line).strip() for line in "".join(p.parts).split("\n")]
    return "\n".join(line for line in lines if line), p.links


def sentences(text):
    out = []
    for line in text.split("\n"):
        for s in SENTENCE_END.split(line):
            s = s.strip()
            if s:
                out.append(s)
    return out


def mentions_ai(sentence):
    return bool(AI_TOKEN.search(sentence) or AI_WORDS.search(sentence))


def ai_sentences(text, limit=800):
    found, seen = [], set()
    for s in sentences(text):
        if mentions_ai(s):
            s = s if len(s) <= limit else s[:limit] + " [...]"
            if s not in seen:
                seen.add(s)
                found.append(s)
    return found


def host(url):
    h = urllib.parse.urlsplit(url).hostname or ""
    return h[4:] if h.startswith("www.") else h


def follow_links(base_url, links, limit=MAX_FOLLOW):
    """Same-site links that look like rules/terms/FAQ/guidelines, in page order. Returns (follow, documents)."""
    follow, docs, seen = [], [], {urllib.parse.urldefrag(base_url)[0]}
    for href, text in links:
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        url = urllib.parse.urldefrag(urllib.parse.urljoin(base_url, href))[0]
        if not url.startswith(("http://", "https://")) or host(url) != host(base_url) or url in seen:
            continue
        path = urllib.parse.urlsplit(url).path
        if not (FOLLOW_TEXT.search(text or "") or FOLLOW_PATH.search(path)):
            continue
        seen.add(url)
        if BINARY.search(path):
            docs.append(url)
        elif len(follow) < limit:
            follow.append(url)
    return follow, docs


def classify(pages, sents):
    """Deterministic first-pass label. pages: list of dicts with 'chars'; sents: AI sentences found.

    unreachable  no page could be read          unreadable  every page read has < MIN_CHARS visible chars
    silent       no AI sentence                 training_only  AI sentences only about training/scraping
    ban          an AI sentence (not about training) has a prohibition cue; scope 'assisted' if a banning
                 sentence also mentions assistance, tools, editing or any use, else 'generated'
    allow_or_conditional  no ban cue, but an allow/disclose cue     other_mention  anything else
    """
    read = [p for p in pages if p.get("chars") is not None]
    if not read:
        return "unreachable", None
    if not sents:
        if all(p["chars"] < MIN_CHARS for p in read):
            return "unreadable", None
        return "silent", None
    rule = [s for s in sents if not TRAIN_CUE.search(s)]
    if not rule:
        return "training_only", None
    bans = [s for s in rule if BAN_CUE.search(s)]
    if bans:
        return "ban", "assisted" if any(ASSIST_CUE.search(s) for s in bans) else "generated"
    if any(ALLOW_CUE.search(s) for s in rule):
        return "allow_or_conditional", None
    return "other_mention", None


CHARSET_ALIASES = {"shift_jis": "cp932", "euc-kr": "cp949", "gb2312": "gb18030", "gbk": "gb18030"}
META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?([A-Za-z0-9_.:-]+)""", re.I)


def decode(body, header_charset=None):
    m = META_CHARSET.search(body[:8192])
    for cs in (header_charset, m.group(1).decode("ascii") if m else None, "utf-8"):
        if not cs:
            continue
        cs = CHARSET_ALIASES.get(cs.lower(), cs.lower())
        try:
            return body.decode(cs)
        except (LookupError, UnicodeDecodeError):
            pass
    return body.decode("utf-8", errors="replace")


def fetch(url, timeout=45):
    """{'status', 'tls', 'final_url', 'text' (decoded HTML or None), 'error'}; one unverified retry on a
    certificate error, marked as such."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                                               "Accept-Language": "en"})
    error = None
    for tls, ctx in (("verified", None), ("unverified", ssl._create_unverified_context())):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                ctype = resp.headers.get("Content-Type", "")
                body = resp.read(5_000_000)
                if ctype and "html" not in ctype and "text" not in ctype:
                    return {"status": resp.status, "tls": tls, "final_url": resp.geturl(), "text": None,
                            "error": "not html: %s" % ctype}
                return {"status": resp.status, "tls": tls, "final_url": resp.geturl(),
                        "text": decode(body, resp.headers.get_content_charset()), "error": None}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "tls": tls, "final_url": url, "text": None, "error": str(e)}
        except (urllib.error.URLError, ssl.SSLError, OSError) as e:
            error = str(getattr(e, "reason", e))
            if "CERTIFICATE" not in error.upper():
                break
    return {"status": None, "tls": None, "final_url": url, "text": None, "error": error}


def read_contests(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate contest id")
    for r in rows:
        for code in r["listings"].split(";"):
            if code not in LISTINGS:
                raise ValueError("%s: unknown listing %s" % (r["id"], code))
        if not r["url"].startswith(("http://", "https://")):
            raise ValueError("%s: bad url" % r["id"])
    return rows


def contest_urls(row):
    return [row["url"]] + [u for u in (row.get("extra_urls") or "").split(";") if u.strip()]


def url_in_listing(url, listing_html):
    if listing_html is None:
        return None
    return url in listing_html or html.escape(url) in listing_html or url.replace("&", "&amp;") in listing_html


def census(rows, fetcher=fetch, pause=1.0):
    listings, results, texts = {}, [], {}
    calls = [0]

    def get(url):
        if calls[0] and pause:
            time.sleep(pause)
        calls[0] += 1
        return fetcher(url)

    for code, url in LISTINGS.items():
        got = get(url)
        text = extract(got["text"])[0] if got["text"] is not None else None
        if text is not None:
            texts["listing-" + code] = text
        listings[code] = {"url": url, "status": got["status"], "error": got["error"], "html": got["text"],
                          "ai_sentences": ai_sentences(text) if text else []}
    for row in rows:
        pages, sents, docs, done = [], [], [], set()
        queue = contest_urls(row)
        main_urls = set(queue)
        while queue:
            url = queue.pop(0)
            if url in done:
                continue
            done.add(url)
            got = get(url)
            entry = {"url": url, "final_url": got["final_url"], "status": got["status"], "tls": got["tls"],
                     "error": got["error"], "chars": None, "followed": url not in main_urls}
            if got["text"] is not None:
                text, links = extract(got["text"])
                entry["chars"] = len(text)
                texts["%s-%d" % (row["id"], len(pages))] = text
                for s in ai_sentences(text):
                    sents.append({"page": url, "sentence": s})
                if url in main_urls:
                    more, d = follow_links(got["final_url"] or url, links)
                    docs += d
                    queue += [u for u in more if u not in done]
            pages.append(entry)
        unique = []
        for s in sents:
            if s["sentence"] not in [u["sentence"] for u in unique]:
                unique.append(s)
        label, scope = classify(pages, [s["sentence"] for s in unique])
        in_listing = {}
        for code in row["listings"].split(";"):
            found = [url_in_listing(u, listings[code]["html"]) for u in contest_urls(row)]
            in_listing[code] = None if found[0] is None else any(found)
        results.append({"id": row["id"], "name": row["name"], "listings": row["listings"],
                        "fee": row["fee"], "deadline_listed": row["deadline_listed"],
                        "url_in_listing": in_listing, "pages": pages, "documents_not_read": docs,
                        "ai_sentences": unique, "auto_label": label, "auto_scope": scope,
                        "mentions_training": any(TRAIN_CUE.search(s["sentence"]) for s in unique)})
    for v in listings.values():
        v.pop("html")
    return results, listings, texts


def prereg_commit(path, opener=None):
    """Date of the first commit that added the pre-registration (None if not on main yet)."""
    url = REPO_API + "?" + urllib.parse.urlencode({"path": path, "per_page": 100})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    try:
        data = json.loads((opener or (lambda r: urllib.request.urlopen(r, timeout=60).read()))(req))
    except Exception as exc:
        return {"committed_at": None, "error": type(exc).__name__}
    if not isinstance(data, list):
        return {"committed_at": None, "error": "unexpected API answer"}
    if not data:
        return {"committed_at": None, "error": "no commit touches %s yet" % path}
    first = data[-1]
    return {"committed_at": first["commit"]["committer"]["date"], "sha": first["sha"], "error": None}


def report(results, listings, started, finished, prereg):
    labels = ["ban", "allow_or_conditional", "other_mention", "training_only", "silent", "unreadable",
              "unreachable"]
    counts = {k: sum(1 for r in results if r["auto_label"] == k) for k in labels}
    lines = ["# Writing-contest AI rules: automatic first pass", "",
             "census.py %s. Pages fetched %s to %s UTC. Pre-registration first committed: %s." % (
                 VERSION, started, finished, prereg.get("committed_at") or "not found (%s)" % prereg.get("error")),
             "", "This is the deterministic first pass, not the census's primary coding (see the "
             "pre-registration). Every AI sentence is in sentences.csv, word for word.", "",
             "| Auto label | Contests |", "|---|---|"]
    lines += ["| %s | %d |" % (k, counts[k]) for k in labels]
    bans = [r for r in results if r["auto_label"] == "ban"]
    lines += ["", "Ban scope (auto): assisted %d, generated only %d." % (
        sum(1 for r in bans if r["auto_scope"] == "assisted"), sum(1 for r in bans if r["auto_scope"] == "generated")),
        "Contests whose AI sentences mention training or scraping: %d." % sum(1 for r in results if r["mentions_training"]),
        "", "| id | fee | auto label | scope | pages read | AI sentences | URL in listing |", "|---|---|---|---|---|---|---|"]
    for r in results:
        read = sum(1 for p in r["pages"] if p["chars"] is not None)
        lines.append("| %s | %s | %s | %s | %d/%d | %d | %s |" % (
            r["id"], r["fee"], r["auto_label"], r["auto_scope"] or "", read, len(r["pages"]),
            len(r["ai_sentences"]), ", ".join("%s %s" % kv for kv in r["url_in_listing"].items())))
    lines += ["", "## Listings", ""]
    for code, v in listings.items():
        lines.append("- %s (%s): HTTP %s, %d AI sentence(s)" % (code, v["url"], v["status"] or v["error"],
                                                               len(v["ai_sentences"])))
    lines += ["", "Made by MV2 of Munim, Inc., with AI agents working in his name. Data CC BY 4.0, code Apache-2.0.", ""]
    return "\n".join(lines)


def main(argv=None, fetcher=fetch, opener=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--contests", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--save-text", action="store_true")
    ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--prereg-path", default="census/2026-11/PREREGISTRATION.md")
    ap.add_argument("--no-prereg-check", action="store_true")
    a = ap.parse_args(argv)
    rows = read_contests(a.contests)
    prereg = {"committed_at": None, "error": "not checked"} if a.no_prereg_check else prereg_commit(a.prereg_path, opener)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results, listings, texts = census(rows, fetcher, a.pause)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "census.json"), "w", encoding="utf-8") as fh:
        json.dump({"version": VERSION, "started": started, "finished": finished, "prereg": prereg,
                   "contests": results}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out_dir, "listings.json"), "w", encoding="utf-8") as fh:
        json.dump(listings, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out_dir, "sentences.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["contest_id", "page", "sentence"])
        for r in results:
            for s in r["ai_sentences"]:
                w.writerow([r["id"], s["page"], s["sentence"]])
    text = report(results, listings, started, finished, prereg)
    with open(os.path.join(a.out_dir, "CENSUS_AUTO.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    if a.save_text:
        os.makedirs(os.path.join(a.out_dir, "pages"), exist_ok=True)
        for key, t in texts.items():
            with open(os.path.join(a.out_dir, "pages", key + ".txt"), "w", encoding="utf-8") as fh:
                fh.write(t)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
