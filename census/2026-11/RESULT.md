# Result: what 54 writing contests closing in late 2026 say about AI

Graded on 2026-11-02 (UTC) against [PREREGISTRATION.md](PREREGISTRATION.md). Made by MV2 of Munim, Inc., with AI agents working in his name. Text and data CC BY 4.0. Not legal advice: read the organiser's own page before entering.

## Timing

- Pre-registration committed: **2026-11-02 04:36:29 UTC** (commit `71c0e04`, as recorded by `census.py` in `census.json`).
- Pages fetched: **04:39:37 to 04:46:06 UTC**, after registration. This is the pre-registered census, not an exploratory one.
- Primary coding: done after the fetch by an AI agent, from the saved AI sentences (`sentences.csv`) and the saved page text around them, using the rubric as written. Every code and the sentence it rests on is in [coding.csv](coding.csv).

## Counts (primary coding)

| Code | Contests |
|---|---|
| BAN_ANY_USE | 18 |
| BAN_GENERATED | 6 |
| ALLOW_DISCLOSED | 1 |
| NO_ENTRY_RULE | 1 |
| SILENT | 25 |
| UNREADABLE | 1 |
| UNREACHABLE | 2 |
| **Total** | **54** |

Left out of every share below: Writory Short Story Competition (UNREADABLE: three pages of under 60 characters, built by JavaScript), Catchment - Poetry of Place (UNREACHABLE: network unreachable) and the Wergle Flomp Humor Poetry Contest (UNREACHABLE: an HTTP 307 redirect that `census.py` 0.1.0 did not follow; a tool limit, not the site's). That leaves **51 readable contests**.

## Predictions

| | Prediction | Result | Held? |
|---|---|---|---|
| P1 | At least 40% of readable contests are coded as a ban | 24 of 51 = **47.1%** | **held** |
| P2 | At most one contest is ALLOW_DISCLOSED | **1** (Missouri Review Jeffrey E. Smith Editors' Prize) | **held** |
| P3 | At least half of the bans are BAN_ANY_USE | 18 of 24 = **75%** | **held** |
| P4 | The listing mentions the ban for fewer than half of the banned contests | 5 of 24 = **20.8%** | **held** |
| P5 | Fee contests are coded as a ban more often than free ones (direction only) | fee 15 of 27 = **55.6%**; free 8 of 23 = **34.8%**; Fisher's exact p = 0.17 two-sided (0.12 one-sided) | **held** (direction; not significant) |

P5 leaves out the Bath Novel Award, whose fee the frame records as unknown (it is coded BAN_ANY_USE).

P4's five mentions: Reedsy Novel Sprint and Writer's Digest Short Short Story Competition (W-ND), CRAFT Short Fiction Prize (NCW), Dinesh Allirajah Prize and Writers of the Future (W-FREE). The other 19 banned contests appear in their listing with fee, length and prize details but no word about AI. The W-ND listing's third AI sentence is about the Commonwealth Short Story Prize's rules review, which matches its code (NO_ENTRY_RULE).

## One reading choice, and the result under the other reading

The rubric gives each contest "the strictest entry rule found on any page read". Read literally, that pulls in three rules written for a different programme run by the same organiser, found on pages the census followed from the contest page:

- **Writers of the Future**: the strictest sentence ("The use of generative tools such as artificial intelligence (AI) or similar technologies is strictly prohibited.") is in the *Illustrators* of the Future rules. The writers' own rules ban work "generated, in whole or in part, by Artificial Intelligence" (BAN_GENERATED).
- **Minotaur Books and MWA First Crime Novel Competition**: the only rule is on MWA's *Edgar Awards* submission page, which bans AI-generated material and allows copy editing and grammar tools. The competition's own pages have no AI sentence.
- **Mslexia Women's Poetry and Pamphlet Competitions**: the only rule is a checkbox on Mslexia's *magazine* submission forms ("I confirm that my submission is not AI generated, nor has AI been used in any part of the creative process."). The competitions' own pages have no AI sentence.

The primary coding above follows the registered wording. Counting only rules that apply to the contest itself (its own pages, or a general submission policy of the organiser), the `scoped_code` column in `coding.csv` gives: BAN_ANY_USE 15, BAN_GENERATED 6, ALLOW_DISCLOSED 1, NO_ENTRY_RULE 2, SILENT 27. **Every prediction still holds**: P1 21 of 51 = 41.2% (just over the 40% mark), P2 1, P3 15 of 21 = 71%, P4 5 of 21 = 24%, P5 fee 13 of 27 = 48.1% vs free 7 of 23 = 30.4% (Fisher p = 0.25 two-sided, 0.16 one-sided).

Three more codes are borderline and are marked in `coding.csv`. The Anthology Travel Writing Competition and the Latino Voices contest ban the "use of generative AI" (coded BAN_ANY_USE because the ban is on use, not only on generated text), and the Deborah Rogers Award's guidelines word their ban as an "expectation". Recoding all three as BAN_GENERATED would make P3 15 of 24 = 62.5%, which still holds.

## Exploratory (not tested)

- **Training promises**: 1 contest. Reedsy's site terms say "we shall not make use of any of your User Content for the purpose of training AI models (or similar)." Two more promise people, not AI, will judge: the Bath Novel Awards ("We do not use generative artificial intelligence to read or judge submissions.") and the Commonwealth Short Story Prize ("entries are read by real people at every stage of the judging process and not put through an AI system"). Neither is a training promise under the rubric.
- **Where the rule sits**: for 13 of the 24 bans, a ban sentence is on the page the listing links to. For the other **11 (46%)**, it is only on a rules, FAQ, guidelines or submission page one click away (London Magazine, Bedford, both Bath awards, both Mslexia competitions, SmokeLong, CRAFT's DNA Prize, Drinking Gourd, Rattle, Minotaur/MWA). A writer who reads only the listing and the contest page it links to will miss the rule for most banned contests.
- **The one contest that accepts AI-made text** is the Missouri Review's Jeffrey E. Smith Editors' Prize (fee contest): "If artificial intelligence has been used to generate any portion of your submission, you must disclose your usage in specific detail within the piece and in your cover letter." The disclosure goes inside the piece itself as well as in the cover letter.
- **The Commonwealth Short Story Prize** has no entry rule on AI on its page. Its page speaks of allegations that AI wrote this year's winning stories and of the need to "evolve our approach", and the W-ND listing says the prize now opens in January 2027 while its rules are reviewed.
- **SILENT is not "allowed"**: the W-FREE listing says AI-generated work is not eligible for the PJI Editor's Prize, but the prize page the census read has no AI sentence. The rule is probably on a submission form the census did not read. This is exactly the limit the pre-registration named: SILENT means no rule on the pages read, not no rule.
- **First pass vs primary coding**: `census.py`'s deterministic labels, mapped to the rubric (ban/assisted to BAN_ANY_USE, ban/generated to BAN_GENERATED, allow_or_conditional to ALLOW_DISCLOSED, other_mention to NO_ENTRY_RULE), agree with the primary coding for **47 of 54 contests (87%)**, and on ban vs no ban for 52 of 54 (96%). The seven disagreements: London Magazine (auto said assisted; "partially generated" is still generation), Bedford and SmokeLong (auto said generated; "with the aid of" and translation reach assistance), Anthology and Latino Voices (auto said generated; see borderline above), Commonwealth (auto said ban; its sentences are not a rule on entries) and Minotaur/MWA (auto said other mention; the Edgar rule is a ban under the literal reading).

## How this compares

- Become a Writer Today's AI-submission-policy list (read 2026-11-02) mixes magazines and contests and found 81 of 179 markets with an outright ban and 87 with no stated policy. Here, among contests only, from listings not chosen for AI, 24 of 51 readable contests (47%) ban AI and 25 (49%) say nothing on the pages read: a similar split.
- Lumethic found 57% of 87 photo contests ban AI images; Stingrai found that none of 53 bug-bounty programmes ban AI-assisted reports.
- What this census adds: a frame taken from deadline listings, every AI sentence published word for word with the page it came from, the saved text of every page, and a pre-registered rubric and predictions committed before any page was read.

## Limits

- One slice: 54 contests from three English-language listings, mostly UK, US and Australian, closing October to December 2026. Not the whole market.
- Rules in PDFs, behind a login or on a submission form were not read (PJI shows this can matter). SILENT is a floor on how often a ban is stated where a writer would look first, not a count of contests without one.
- Pages change; this records them as fetched on 2026-11-02 between 04:39 and 04:46 UTC.
- The primary coding was done by AI agents, not people. Every sentence it rests on is published so anyone can check or recode it.

## Files

- `coding.csv`: the primary code, training flag, quoted sentence and page for every contest, with `census.py`'s first-pass label, whether they agree, and the scoped reading.
- `census.json`, `sentences.csv`, `listings.json`, `CENSUS_AUTO.md`: `census.py` 0.1.0's output, unchanged.
- P4 rests on the listings' AI sentences in `listings.json`; each was matched to its contest by reading the saved listing text around it. The saved text of the listings and of every contest page was kept by the run that fetched them. It is not committed here, to keep the repository small and because the pages name judges and other people, which this census leaves out. The run was `python census.py --contests census/2026-11/contests.csv --out-dir out --save-text --pause 1`; running it again saves the pages as they stand on the new date, which may differ.
