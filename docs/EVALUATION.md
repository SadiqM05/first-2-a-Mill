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
