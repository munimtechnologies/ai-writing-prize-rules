# Changelog: census.py

## Note (2026-11-04, later): what the Wergle Flomp 307 is

A follow-up probe on 2026-11-04 at 06:21 UTC fetched the Wergle Flomp contest page and the site's home page once with the census's user agent and once with a desktop browser's user agent, without following redirects. The saved answers are in [`census/2026-11/wergle-probe-2026-11-04.json`](census/2026-11/wergle-probe-2026-11-04.json). All four answers were the same:

- HTTP 307 with **no Location header**, which confirms the 0.1.1 erratum below.
- `Server: Sucuri/Cloudproxy` and an `x-sucuri-id` header. The body is a "You are being redirected..." page that says "Javascript is required" and runs an obfuscated script.

So the page is behind the site firewall's JavaScript challenge. A browser that runs the script gets through, but a reader that does not run JavaScript never sees the page, whatever its user agent. The 0.1.1 erratum said the fault "lies with the site". More exactly, the site's firewall blocks automated readers. A future census records such pages as **blocked to automated readers (JavaScript challenge)**, not as unreachable, and does not try to get past the challenge. The 2026-11 census's exclusion and its results are unchanged.

## 0.1.1 (2026-11-04)

The 2026-11 census in `census/2026-11/` was made with 0.1.0. Its files, primary coding and graded result are unchanged. The next census will use 0.1.1.

- **Erratum on Wergle Flomp.** `census/2026-11/RESULT.md` says the Wergle Flomp Humor Poetry Contest was unreachable because of "an HTTP 307 redirect that `census.py` 0.1.0 did not follow". The run's saved error is exactly `HTTP Error 307: Temporary Redirect`. With Python's urllib that means the 307 response carried **no Location header**, so there was nowhere to follow. A redirect loop would have produced a different message, and a redirect elsewhere would have been followed. The contest's exclusion stands, but the cause is the site's response, not a missing redirect rule in the tool. On 2026-11-04 the page still answered 307 to an automated reader.
- **Unfollowable redirects are now recorded.** When a 3xx response cannot be followed, the page entry in `census.json` gets a `location` field: the response's Location header, or `null` when it has none. A future census can then tell a missing Location from a blocked or looping redirect.
- **A cookie jar per fetch.** Each fetch now keeps its own cookies while following redirects, so a site that sets a cookie and redirects back to itself is read instead of looping. Nothing is shared between fetches. This is the same fetch the companion census tool, `programs.py` in [tech-writing-ai-rules](https://github.com/munimtechnologies/tech-writing-ai-rules), has always used. It is a general fix and would not have changed the Wergle Flomp result.
- **Curly apostrophes.** The ban cue knew "can't" and "won't" only with a straight apostrophe, so a rule written "won’t be accepted" was read as an allow cue ("accepted"). Cues are now matched on a copy of each sentence with curly apostrophes made straight. Sentences are still saved exactly as found.
- `fetch()` takes an optional `proxies` argument (`{}` turns proxies off), which the tests use. New offline tests run a small server on 127.0.0.1. They check that a cookie redirect is now read, that a plain urllib opener without cookies loops and fails with 307, and that a 307 without a Location header comes back with `location` set to `None`.

Not changed: the listings, the pages followed, the sentence splitter, the label set and the other cues. The first pass is a screen. The census's primary coding is done by reading every saved sentence.

## 0.1.0 (2026-11-02)

First release, used for the pre-registered census in `census/2026-11/`.

Made by MV2 of Munim, Inc., with AI agents working in his name. Apache-2.0.
