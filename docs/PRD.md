# ResLink AI — Product Requirements Document

**Status:** Hackathon MVP specification (proposed; subject to team approval)  
**Audience:** University of Tennessee, FDB Hall Resident Assistants (RAs); head staff are secondary stakeholders  
**Development window:** 18-hour, two-person AI Product hackathon  
**Product name:** ResLink AI — Your Intelligent RA Resource Navigator

## 1. Problem

RAs must navigate fragmented university webpages, forms, documents, and procedures to complete recurring responsibilities such as reports, maintenance requests, and hall programming. They may know what needs to be done but not where to find the authoritative instructions or correct form. Information is also fragmented across head staff communications: some updates and deadlines are shared at staff meetings, so RAs who miss meetings may not receive information promptly and others may struggle to find it afterward.

**Problem to solve in the MVP:** Make publicly available RA resources and procedures easy to discover and act on, using natural-language questions and verified links. **Related problem reserved for a stretch goal:** Make staff announcements and deadlines searchable outside meetings.

## 2. Users and jobs to be done

- **Primary:** FDB Hall RAs seeking the correct resource or procedure quickly.
- **Secondary:** Head staff who need RAs to access accurate, consistent information. Head staff publishing tools are *not* required in the MVP.
- **Job:** “When I need to complete an RA responsibility, help me find the right official resource and understand the next steps without searching multiple places.”

## 3. Product proposition

A local-first, Streamlit-based resource dashboard and conversational AI assistant. Users browse categories or describe a task in ordinary language. The application retrieves relevant information from a curated collection of publicly accessible university resources, gives a concise grounded explanation, and links to the original source or form. It guides users; it does **not** complete, submit, or approve administrative work.

## 4. MVP scope (required)

| ID | Capability | Expected behavior | Acceptance criteria |
|---|---|---|---|
| M1 | Resource dashboard | Browse curated resources by category (e.g., reporting, maintenance, programming, policies) | Resources show human-readable title, category, and verified original URL |
| M2 | Natural-language search | Ask where to find a form or how to complete an RA task | Question returns relevant retrieved material or a clear insufficient-evidence message |
| M3 | Grounded procedural answers | Summarize steps from retrieved material | Instructions are traceable to source content; no fabricated policy or procedural requirements |
| M4 | Actionable source cards | Show relevant resource and direct link | Links originate from the verified catalog or ingested source metadata, not model-generated URLs |
| M5 | Citation / provenance | Show the origin of claims | Answers identify supporting document/page or URL when available |
| M6 | Demo evaluation | Test realistic RA scenarios | Record questions, expected source, actual result, and observed failures; verify links manually |

**Suggested initial resource categories:** Maintenance, Reporting, Programming, Policies. Categories and specific resources require validation against the actual materials collected.

**Illustrative demo questions (not assertions about existing forms):**
1. “Where do I submit my weekly RA report?”
2. “What steps do I follow to organize a hall program?”
3. “A resident needs something repaired. Where do I start?”

## 5. Stretch goal — staff bulletin (only after MVP is stable)

Display searchable head staff announcements, meeting summaries, and deadlines, optionally including them in AI retrieval. A small, locally maintained JSON file with clearly labeled **sample** announcements is sufficient for demonstration. Do not implement authentication, push notifications, staff publishing workflows, or a production communications system during the hackathon. Sample content must never be presented as an actual UT directive.

## 6. Explicitly out of scope

- Completing/submitting forms, making maintenance requests, or taking actions in university systems.
- University account integration, protected portals, SSO, authentication, and authorization.
- Storing resident personal data, private incident reports, or confidential staff records.
- Continuous website crawling or automatic monitoring of university updates.
- Cloud deployment, AWS infrastructure, multi-hall rollout, production availability guarantees.
- Full staff announcement management, notifications, persistent user profiles.

## 7. Experience principles

- **Task-first:** Make “find the right thing” faster than navigating a document hierarchy.
- **Actionable:** Put source links and next steps adjacent to answers.
- **Transparent:** Distinguish retrieved facts from uncertainty; surface source references.
- **Low-friction:** No login required for the local demo.
- **Trustworthy:** Prefer a clear “I couldn't verify that” over an invented answer.

## 8. Success criteria and validation

**Minimum demo readiness:** All three illustrative scenarios can be demonstrated using *actual collected and verified* resources, or are replaced with scenarios that the collected evidence supports. Resource links open the intended destination. The system refuses to invent an answer when evidence is absent. At least one insufficient-evidence query is tested.

**Proposed evaluation approach:** Build a set of approximately 15–20 representative questions, with expected source URLs, and track retrieval relevance, answer grounding, link correctness, and failures. This is a target for testing, **not** a claimed measured result. No invented time-savings or accuracy claims.

## 9. Risks and mitigations

- **No suitable public documents:** Curate a smaller verified catalog; prioritize direct resource navigation and honest limitations.
- **Hallucinated instructions/URLs:** Restrict links to catalog metadata; ground generation in retrieved excerpts; decline unsupported questions.
- **PDF/web extraction errors:** Inspect extracted text and maintain original-source metadata.
- **API quota or connectivity failure:** Keep a usable browsable dashboard and local retrieval fallback.
- **Time pressure:** Freeze scope once core question-to-source flow works; prioritize testing and demo over stretch features.
- **Privacy:** Only ingest public or explicitly authorized non-sensitive content; do not send confidential records to external LLM services.

## 10. Decisions and open questions

**Confirmed:** Streamlit + Python; local-first MVP; Gemini API planned for generation; RAG with ChromaDB and Sentence Transformers proposed; publicly accessible UT resources; FDB Hall RAs first; staff bulletin stretch only; no deployment requirement.

**To confirm during resource collection:** Exact source URLs and documents; which official procedures are publicly documented; whether three illustrative demo scenarios are supported; which sample announcements, if any, are acceptable for a clearly marked stretch demonstration.
