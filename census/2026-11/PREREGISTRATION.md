# Pre-registration: what do writing contests closing in late 2026 say about AI?

Written and committed on 2026-11-02 (UTC), before `census.py` read any contest page for this census. The git commit time of this file is the registration time; `census.py` records it in its output, next to the time the pages were fetched. Made by MV2 of Munim, Inc., with AI agents working in his name. Text and data CC BY 4.0; code (`census.py`, `test_census.py`) Apache-2.0.

## Why

`prizes.csv` in this repository is hand-picked: it lists prizes chosen because their AI rules are known. That says nothing about how common each kind of rule is. Existing counts mix contests with magazines (Become a Writer Today's AI-submission-policy list, read on 2026-11-02: 81 of 179 markets checked state an outright ban and 87 show no stated policy; checks dated July and October 2026), or cover other fields (Lumethic read 87 photo contests: 57% ban AI images; Stingrai read 53 bug-bounty policies: none ban AI-assisted reports). No count was found that takes writing contests from listings chosen for some other reason, reads each contest's own pages, and publishes every AI sentence word for word. This census does that for one fixed frame.

## Frame (fixed now)

`contests.csv`: every contest with a link in three public deadline listings, as read on 2026-11-02:

- **W-ND**: wroteabook.org, "Writing Competitions Closing Oct to Dec 2026" (20 contests)
- **NCW**: Newcastle Creative Writers, "Writing competitions closing November 2026" (17 contests, 3 also in W-ND)
- **W-FREE**: wroteabook.org, "Free Writing Contests October and November 2026" (20 contests)

That is 54 contests: UK, Irish, US and Australian, with and without fees, prizes from publication to £10,000. The listings were compiled to help writers find deadlines, not to study AI rules. Some deadlines have already passed; a contest's rules are read as its pages stand on the fetch date. The contest URLs were taken from the listings, and `census.py` checks that each one really appears in its listing's HTML (`url_in_listing`).

## What is read

For each contest: its listed page (two pages for one contest listed twice under different links) and up to five same-site links whose text or path looks like rules, terms, FAQ, eligibility or submission guidelines. PDFs and other documents are listed, not read. From the visible text, every sentence that mentions AI (the capitalised token "AI" or "A.I.", artificial intelligence, ChatGPT, LLM, large language model, generative, machine- or computer-generated, chatbot, Grammarly, Copilot, Claude, Gemini, Midjourney, text generation) is kept word for word in `sentences.csv`, and each page's text is saved. The three listing pages are read the same way.

## Coding (fixed now)

**Primary coding** is done after the fetch by an AI agent reading every saved AI sentence (and the saved page text around it when a sentence is unclear), with this rubric. Each contest gets the strictest entry rule found on any page read, and the coding file quotes the sentence it rests on.

- **BAN_ANY_USE**: AI may not be used at any stage, or the ban covers AI-assisted as well as AI-generated work (for example editing, translating or grammar tools named as banned).
- **BAN_GENERATED**: AI-generated or AI-written text is banned, without the ban reaching assistance, or with limited assistance (spelling, grammar, research) expressly allowed.
- **ALLOW_DISCLOSED**: AI-generated text is accepted, with or without a disclosure requirement.
- **NO_ENTRY_RULE**: AI is mentioned, but not as a rule on entries (a promise about training or scraping, judges' own use, a theme, a news item, rules said to be under review).
- **SILENT**: no AI sentence on any page read.
- **UNREADABLE**: pages were fetched but every one has under 500 characters of visible text (for example a page built by JavaScript).
- **UNREACHABLE**: no page could be fetched (including an HTTP 403 to the census's self-identifying user agent).

Flag **TRAINING_PROMISE**: the contest says entries will not be used or licensed to train AI, or forbids others to do so.

The deterministic first-pass label from `census.py` (`classify()`) is published next to the primary coding, with the agreement rate. Contests coded UNREADABLE or UNREACHABLE are left out of every share below and listed.

## Predictions

- **P1.** Of the readable contests, at least 40% are coded BAN_ANY_USE or BAN_GENERATED.
- **P2.** At most one contest is coded ALLOW_DISCLOSED.
- **P3.** Of the contests coded as a ban, at least half are BAN_ANY_USE.
- **P4.** Of the contests coded as a ban, the listing that names them mentions that ban for fewer than half. A listing "mentions" the ban if its saved text has an AI sentence in that contest's entry. For a contest in two listings, either listing counts.
- **P5.** Contests with an entry fee are coded as a ban more often than free ones (direction only; Fisher's exact p is reported but is not a pass mark). Contests whose fee is unknown are left out of P5.

Every prediction is reported as held or not, whatever the result.

## Not tested (reported as exploratory)

- How many contests make a TRAINING_PROMISE.
- Where the AI rule sits: the main page, a rules or FAQ page, or only a PDF that was not read.
- How the first-pass labels differ from the primary coding, with each disagreement listed.

## Limits, stated now

- 54 contests from three English-language listings is one slice, not the whole market. It leans to UK and Australian contests and to deadlines in October to December.
- A rule can sit where the census does not look: a PDF, a submission form behind a login, an email reply. A contest coded SILENT has no AI rule on the pages read, which is not proof it has none.
- Pages change. The census records what each page said on the fetch date, and saves the text.
- The primary coding is done by AI agents, not by people. Every coded sentence is published so that anyone can check it.
- This repository is about prize rules; it gives no legal advice. Read the organiser's own page before entering.
