# ai-writing-prize-rules

Which writing prizes accept work made with generative AI, and exactly what each one asks you to disclose. One row per prize in [`prizes.csv`](prizes.csv), with the rule quoted word for word in its original language, a link to the page it came from and the date it was checked.

Made by MV2 of Munim, Inc., with AI agents working in his name. Data and text: CC BY 4.0. Code (`check_prizes.py` and its tests): Apache-2.0.

**Not legal advice.** Rules change between editions. Read the organiser's own page before you enter.

## The prizes (checked 2026-10-31)

| Prize | Language | Deadline | AI policy | Mostly-AI text | Where you disclose |
|---|---|---|---|---|---|
| AI Philosophy Competition 2026 | en | 2026-10-31 | AI required | must be primarily AI generated | methodology report, published online (judging is blind to it) |
| Prix Pascal 2026 | fr | 2026-11-30 | AI required | yes | entry form (LLM, agents or prompt) + technical dossier |
| Sogen SF Short Story Prize (18th) | ja | 2027-01-12 | allowed, disclosed | at most 1 such work per entrant | after the synopsis + web-form checkbox |
| Kakuyomu Contest 12 (short story) | ja | 2027-02-01 | allowed, disclosed | yes, tagged AI本文利用 (about 50%+) | platform tag; a wrong tag excludes the work |
| Hayakawa SF Contest (15th) | ja | 2027-03-31 | allowed, disclosed | no limit stated | end of the synopsis |
| Bungei Prize (64th) | ja | 2027-03-31 | allowed, disclosed | no limit stated | author's biography (略歴) |
| Nikkei Hoshi Shinichi Award (14th) | ja | closed 2026-10-06 | allowed, disclosed | only after a human revises it | entry form, 500 characters |
| Writers of the Future (Q1 2027) | en | 2026-12-31 | banned | no | none |
| Nebula Awards | en | nominations | banned | no | none |

## What the rules show

- **Disclosure goes in five different places**: an entry form (Prix Pascal, Hoshi, plus Sogen's checkbox), the end of the synopsis (Sogen, Hayakawa), the author's biography (Bungei), a tag on the work (Kakuyomu) and a separate methodology report (AI Philosophy Competition). A writer who reuses one disclosure for every prize will put it in the wrong place for most of them.
- **"Accepts AI" covers very different rules.** The AI Philosophy Competition requires the work to be primarily AI generated. Hoshi accepts non-human entrants if a contactable guardian or agent is named, yet says AI-generated text must not be used as is and must be revised by a person. Sogen accepts mostly-AI stories but only one per entrant.
- **Three of the seven can ask for your records** (Sogen, Hayakawa, Hoshi): prompts and outputs may be requested during judging. Keep them from the first draft.
- **Most open doors are in Japan.** Five of the seven prizes here that accept AI-made fiction or essays take entries in Japanese. The two English-language fiction prizes checked both ban it. This is a small, hand-picked list, not a survey, so it shows where to look rather than how common each policy is.

## Fields

| Field | Meaning |
|---|---|
| `id` | lower-case slug, unique |
| `prize`, `organiser`, `edition` | as the organiser names them (Japanese names keep an English gloss) |
| `entry_language` | two-letter code of the language entries must be written in |
| `deadline`, `deadline_note` | YYYY-MM-DD (empty if there is none) and the organiser's wording (time zone, postmark or arrival) |
| `top_prize` | the largest prize, as stated |
| `ai_policy` | `ai_required`, `allowed_with_disclosure` or `banned` |
| `mostly_ai_text` | `required`, `yes`, `one_per_entrant`, `human_revised_only`, `no_limit_stated` or `no` |
| `human_revision_required` | `yes`, `no`, `not_stated` or `not_applicable` (banned rows) |
| `disclosure_where` | where the disclosure goes and what it must say |
| `records_on_request` | whether prompts or production records may be requested |
| `entrant_rule` | who may enter, where the source says |
| `quote` | the rule, verbatim; several sentences are joined with " / " |
| `quote_language`, `source_url`, `source_type`, `checked` | language of the quote, the page it was taken from (`official` or `secondary`), and the check date |

## How it was checked

Every quote was compared with the live page on 2026-10-31 by fetching the page and testing whether it contains the exact string. Eight sources are the organiser's own page. Sogen's comes from kobonabi.com, a contest listing that reprints the rules, because the publisher's site (tsogen.co.jp) refused automated requests. Its official page is https://www.tsogen.co.jp/award/sfss/18th/.

`python check_prizes.py` checks the file: header, required fields, allowed values, dates, https sources, unique ids, and that banned rows say so consistently. `python -m unittest` runs the tests.

## Related lists

- [becomeawritertoday.com: AI submission policies](https://becomeawritertoday.com/ai-submission-policies/): magazines and contests that ban or restrict AI, quoted and dated. The best source for the "banned" side, which this file only samples.
- [aiteller.jp: AI小説コンテスト・公募一覧](https://aiteller.jp/blog/ai-novel-contest): Japanese contests and their AI rules, updated monthly.
- [koubo.jp: 主要32賞のスタンスまとめ](https://koubo.jp/article/85604): the stance of 32 Japanese literary prizes.
- [jamesyu.org: Award-Winning AI Literature](https://jamesyu.org/award-winning-ai-literature/): prize winners with confirmed or alleged AI use.

This file adds an open, machine-readable table across languages that records *where* each prize wants the disclosure and what it limits, with the exact rule text.

Corrections are welcome as issues.
