# Changelog: census.py

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
