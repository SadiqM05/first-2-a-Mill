# ResLink AI — Retrieval evaluation (Milestone 3)

Measured 2026-11-14 on the verified catalog (6 resources) and 28 indexed chunks from two public
PDFs. Question set: `tests/eval_questions.json`, 31 questions: 24 supported (8 of them phrased in
words the sources don't use), 7 unsupported. These numbers are observations on a small,
hand-written set. They are not general accuracy claims. The distance cutoffs and fusion
limits were tuned on this same set, so the scores are optimistic.

Reproduce: `python -m scripts.build_index`, then `python -m scripts.compare_retrieval --sweep`
(offline) and `python -m scripts.run_eval --live` (8 Gemini calls).

## Offline retrieval: keyword-only vs hybrid (no Gemini)

| Metric | Keyword | Hybrid |
|---|---|---|
| Recall@1 (supported, n=24) | 79% | **92%** |
| Recall@3 (supported, n=24) | 79% | **96%** |
| Recall@3, paraphrased only (n=8) | 38% | **88%** |
| Unsupported questions that reach Gemini (n=7) | 5 | 7 |
| Average evidence items per question | 1.97 | 3.03 |
| Off-target evidence items (supported questions) | 18 | 27 |
| Retrieval latency, median / max | 0.7 / 1.2 ms | 38 / 42 ms |

- **Recall@1:** the top catalog hit or the top document page is an expected target.
- **Recall@3:** an expected target is within the top 3 catalog hits or top 3 pages.
- No supported question that keyword search found in its top 3 is lost by hybrid (checked per
  question by `test_hybrid_never_loses_a_keyword_hit`).
- **Known miss:** "My resident can't get into their room". The lockout catalog entry ranks
  3rd semantically (distance 0.68) and is cut by the catalog limits.

### Why a distance cutoff can't decide "unsupported"

Best semantic distances: supported targets range 0.36–0.73. Unsupported questions range
0.41–0.66 ("best pizza near campus" 0.62, "organize a hall program" 0.41). They overlap, so
semantic similarity never decides support. The cutoffs only remove noise:

| max distance (documents) | supported targets kept | unsupported questions with hits |
|---|---|---|
| 0.55 | 12/24 | 3/7 |
| 0.65 | 19/24 | 6/7 |
| **0.75 (chosen)** | **24/24** | 7/7 |

Catalog metadata uses a tighter 0.65 and contributes only its single nearest entry. The 2nd and
3rd nearest catalog entries were almost always irrelevant. Correct top-1 matches were mostly
0.46–0.73.

### Choosing the fusion limits (same recall in every row)

| Variant | Avg items | Off-target |
|---|---|---|
| Semantic catalog top 2 (≤0.75), 4 pages | 4.23 | 44 |
| Semantic catalog top 1 (≤0.65), 4 pages | 3.77 | 35 |
| **Semantic catalog top 1 (≤0.65), 3 pages, ≤2 semantic pages (chosen)** | **3.03** | **27** |

## Live Gemini evaluation (8 calls, hybrid, `gemini-3.5-flash-lite`)

| Question | Expected | Result | Citations | Correct? |
|---|---|---|---|---|
| Can I have a pet? *(paraphrase)* | grounded | grounded | policies p1 | Yes: fish ≤10 gal, service animals, approved ESAs |
| Are candles allowed? *(paraphrase)* | grounded | grounded | policies p2 | Yes: open flame prohibited, battery candles allowed |
| What if a resident gets injured? *(paraphrase)* | grounded | grounded | job desc p3 | Partly: correct p3 facts (no transport, notify staff); missed p4 "5 P's → contact Hall Director" |
| How much do RAs get paid? *(paraphrase)* | grounded | grounded | job desc p6 | Yes: $1,200/month Aug–Apr, prorated Jul/May |
| What is the quiet hours policy? | grounded | grounded | policies p5 | Yes: 9 p.m.–9 a.m., 24 h during finals |
| Where can I park overnight? | insufficient | insufficient | — | Yes |
| Best pizza place near campus? | insufficient | insufficient | — | Yes |
| Where do I submit my weekly RA report? | insufficient | **grounded** | job desc p1 | **Regression**: says weekly reports are an RA task (true, cited) but doesn't say where to submit |

Status matched 7/8. Citations correct 7/8. Median end-to-end latency 1.06 s. Every fact in
the grounded answers was checked against the PDF text. None were fabricated, and every link
came from the catalog.

**The regression:** with keyword retrieval (Milestone 2) this question was correctly declined.
Hybrid adds the incident-report catalog entry and p2 as extra context. The model then answered
a related question, "are weekly reports a task?", instead of the one asked. It's a single
sample, so model randomness can't be ruled out. A proposed fix (a stricter rule for when
`sufficient` may be set) is pending approval.

### Follow-up: stricter `sufficient` rule (approved, 3 live calls)

Added to the Gemini instructions: *"Set sufficient to true only when the retrieved evidence
directly answers the user's specific question. Merely mentioning the topic is not
sufficient."* Retrieval is unchanged.

| Question | Before | After | Answer |
|---|---|---|---|
| Where do I submit my weekly RA report? | grounded (regression) | **insufficient_evidence** | "...RAs must complete weekly reports (page 1), but it does not state where or how to submit them." |
| Can I have a pet? *(supported)* | grounded, p1 | **grounded, p1** | Same correct facts (fish ≤10 gal, service animals, approved ESAs) |
| When is the next staff meeting? *(tangential trap)* | not run live | **insufficient_evidence** | "I could not verify when the next staff meeting is..." |

The weekly-report regression is resolved for this sample. With 3 calls this is a spot check, not a
measured rate. Rerun `python -m scripts.run_eval --live` before the demo to confirm the full set.

## Behavior notes

- Unsupported questions now always reach Gemini (7/7, vs 5/7 with keywords), so they use
  quota. The insufficient-evidence check and citation validation stay the safeguard.
- If ChromaDB, the index or the model is missing, stale or erroring, retrieval falls back to
  keyword-only. The sidebar shows "Retrieval: keyword only" and the reason.

# Milestone 4: procedures from the Front Desk Manual transcription

Measured 2026-11-14 with 18 procedure units added (16 procedures, 1 group overview, 1 reference
table). Question set: 47 questions. 31 are carried over from Milestone 3. 16 are about procedures:
14 can be answered from the sources, 1 asks for missing steps, 1 is unsupported, and 1 contains
personal information.

## Offline retrieval (no Gemini)

| Group | Keyword R@1 → hybrid | Keyword R@3 → hybrid |
|---|---|---|
| Earlier PDF/catalog questions (n=24) | 75% → 92% | 79% → **96%** (unchanged from Milestone 3) |
| Procedure questions (n=14) | 57% → **50%** | 79% → **93%** |
| All supported (n=38) | 68% → 76% | 79% → **95%** |

- **Regression found and fixed:** adding the procedures pushed "When do I hold open door hours?"
  out of hybrid's top 3. Words like "door" and "hours" became more common across the index, so
  they count for less. Semantic search now contributes 1 candidate page instead of 2. That fixed it
  and gave the best top-3 recall (95% vs 92%), with less off-target evidence (68 vs 75 items).
- **Tried and rejected:** counting words in a procedure's heading twice. It fixed one keyword-only
  miss but broke "A resident lost their room key, what happens?".
- **Top-1 drop on procedures (57% → 50%):** semantic search sometimes ranks a neighbouring procedure
  first. All top-3 evidence reaches Gemini, so answers rely on top-3 recall (93%).
- **Known misses:** "What is SC Logic?" (the overview loses to procedures with "SC Logic" in their
  headings). "How do I return a letter to sender?" is missed by keyword search only; hybrid finds it.
- **Accepted extra match:** keyword search now also returns the Front Desk Manual for "How many
  front desk hours…" because of its title. This is recorded as `acceptable_catalog`.

## Live Gemini (8 API calls + 1 privacy-blocked question, `gemini-3.5-flash-lite`)

| Question | Expected | Result | Checked against the transcription |
|---|---|---|---|
| How do I check in a package? *(walkthrough)* | grounded | grounded | All 12 steps verbatim and in order, with RAW-package branching and sub-bullets. The model returned them on one line; see below. |
| Walk me through a recore for a lost key *(walkthrough)* | grounded | grounded | 11/11 steps. $45 template kept with placeholders. School Dude portal linked. |
| What craft do I select in School Dude when charging for a lost access card? *(specific)* | grounded | grounded | "Operational services" (§ Steps for Lost Card). One sentence, no full walkthrough. |
| How long can a resident keep a lockout access card? *(specific)* | grounded | grounded | Up to 72 h; 72 h lost/broken phone, 2 h phone in room. |
| How do I return a letter to sender? *(incomplete)* | grounded + incomplete notice | grounded | 3 steps. The model said the source is incomplete, and the code-added notice was shown. |
| What are steps 1 to 3 of the School Dude procedure on page 18? | insufficient | insufficient | Declined: "steps 1 through 3 ... were not supplied". Nothing invented. |
| How do I process a refund for a resident? | insufficient | insufficient | Declined. |
| Charge John Smith, UT ID 123456789, room 214 … *(privacy)* | blocked | blocked | 0 API calls. The ID was redacted in chat history. |
| Can I have a pet? *(PDF regression)* | grounded | grounded | Unchanged and correct (policies p1). |

Status matched 9/9. Every grounded answer cited the right section, every procedure answer carried
the "not verified as current" notice, and related links came only from catalog IDs. Median latency
was 1.5 s.

**Formatting fix:** the model sometimes writes a numbered procedure inline. The check-in walkthrough
had all 12 steps on one line, which renders as one paragraph in Larry. The code now puts an inline
`1. … 2. … 3.` run on separate lines without changing any words. That is checked on the recorded
live answer (word sequence identical) and by unit tests. Not re-run live, to stay within budget.

## Privacy check (limitations)

It blocks only obvious patterns before retrieval or Gemini: 9-digit ID numbers, SSN-like numbers,
emails and phone numbers. **Names, room numbers, NetIDs and birthdays written in words are not
detected.** Larry's input placeholder asks users not to enter resident names or IDs. Chat history
is kept in memory for the browser session only and never written to disk. Detected patterns are
redacted before they're stored or shown again.
