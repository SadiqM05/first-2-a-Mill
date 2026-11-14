# Claude Code Handoff — ResLink AI

You are assisting a two-person team building **ResLink AI — Your Intelligent RA Resource Navigator** for an **18-hour AI Product hackathon**. Read `docs/PRD.md` and `docs/ARCHITECTURE.md` before planning or editing. These files are the source of truth for product intent and proposed architecture. Do not treat unimplemented proposals as completed features.

## Mission

Help University of Tennessee FDB Hall Resident Assistants quickly locate verified public university forms/resources and understand documented procedures. Deliver a Streamlit dashboard and grounded conversational assistant that links to authoritative sources. RAs remain responsible for completing tasks themselves.

## Confirmed constraints

- **Stack:** Python + Streamlit; Gemini API for answer generation; proposed ChromaDB + Sentence Transformers for local semantic retrieval; PyMuPDF, requests/BeautifulSoup for curated public-source ingestion; JSON catalog.
- **Local-first:** No deployment, AWS, FastAPI, React, TypeScript, login, or protected university integrations required.
- **Sources:** Only publicly accessible or explicitly authorized non-sensitive materials. Never invent UT resources, policies, links, deadlines, or demo results.
- **MVP:** Category dashboard; natural-language resource lookup; grounded procedural answers; verified actionable links; citations; evaluation.
- **Stretch only:** Staff bulletin (announcements, deadlines, meeting summaries). Do **not** implement it until the user explicitly authorizes it and the MVP is stable. Sample announcements must be clearly labeled as fictional demonstration content.
- **Privacy:** Never ingest resident PII, confidential reports, or sensitive staff records. Never commit credentials.

## Working rules

1. **Start with a plan:** Inspect repository, summarize current state, propose the smallest next vertical slice, and request approval before major architectural changes or scope additions.
2. **Prioritize functioning software:** Implement one source → one retrieved answer → one verified link before adding styling, extra features, or more dependencies.
3. **No fabricated data:** `data/resources.json` starts empty until the team supplies verified entries. Use explicitly marked placeholders in tests only; never surface placeholders as real university sources.
4. **Guard against hallucinations:** Answer only from retrieved evidence. Build clickable links from validated catalog/source metadata, never free-form model output. Show uncertainty and retrieval failure explicitly.
5. **Keep code approachable:** Prefer readable Python modules, type hints, small functions, docstrings where useful, minimal abstractions, and simple error handling.
6. **Validate changes:** Run available tests or a smoke test after each meaningful change. Explain what was tested and what could not be tested.
7. **Respect collaboration:** Do not overwrite teammate changes, force-push, delete files, or modify unrelated modules. Use small focused commits if asked.
8. **Protect secrets:** Use `.env` for API keys, `.env.example` for names only, and `.gitignore` for `.env`, `.venv`, `__pycache__`, local indexes, and caches.
9. **Timebox:** If sophisticated RAG becomes a blocker, propose a simple verified catalog/keyword retrieval fallback. Do not silently replace the agreed architecture; explain the tradeoff.
10. **Document decisions:** Record meaningful approved changes in `docs/DECISIONS.md` and keep PRD/architecture synchronized.

## Suggested first tasks (after user approval)

1. Initialize repository skeleton, `.gitignore`, `.env.example`, `requirements.txt`, and README with Windows/macOS setup instructions as appropriate.
2. Create a Streamlit page showing the product title, resource category sections, and chat input, with honest empty-state messaging.
3. Implement resource schema validation and loading from `data/resources.json`.
4. Implement ingestion and retrieval for one verified public document supplied by the team.
5. Connect Gemini through a small assistant service; return answer, citations, verified resource links, and error states.
6. Add representative test questions and evaluate grounding/link correctness.
7. Polish UI and demo. Consider bulletin only if user explicitly approves.

## Questions to ask rather than guess

- Which exact UT resource URLs/PDFs are verified and authorized for indexing?
- Which Gemini model and API access are available?
- Which operating systems are the two developers using?
- What is the deadline for freezing the MVP and preparing the demo?

## First response expected from Claude

Read the two docs, inspect the repository, then provide: (a) a brief architecture recap; (b) any gaps or contradictions; (c) a small implementation plan for the first working vertical slice; (d) the minimum information needed from the team. **Do not implement the optional staff bulletin or invent resources.**
