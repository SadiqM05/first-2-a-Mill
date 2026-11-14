# Claude Code Guide — ResLink AI

You are assisting a two-person team building **ResLink AI — Your Intelligent RA Resource Navigator** for an **18-hour AI Product hackathon** (VolHacks 2026). Milestones 1–4 are implemented. The focus now is demo reliability.

**Start every session with `docs/SESSION_HANDOFF.md`**: current status, verified test results, remaining work and a resume checklist. Then use:
- `docs/PRD.md`: product intent;
- `docs/ARCHITECTURE.md`: the system as built;
- `docs/DECISIONS.md`: why each choice was made (approved changes only);
- `docs/EVALUATION.md`: measured results;
- `docs/SOURCE_REVIEW.md`: transcription passages awaiting verification.

## Mission

Help University of Tennessee FDB Hall Resident Assistants quickly locate verified public university forms/resources and understand documented procedures. The deliverable is a Streamlit dashboard plus a grounded assistant (Larry) that links to authoritative sources. RAs remain responsible for completing tasks themselves.

## Confirmed constraints

- **Stack:** Python 3.14 + Streamlit; Gemini via `google-genai` (model from `GEMINI_MODEL`, never hardcoded); ChromaDB with its built-in ONNX embeddings plus keyword retrieval (hybrid, RRF); PyMuPDF for PDFs; JSON catalog; Markdown procedure transcriptions. Don't add dependencies or infrastructure without approval.
- **Local-first:** no deployment, AWS, FastAPI, React, TypeScript, login/RBAC, or protected university integrations.
- **Sources:** only publicly accessible or explicitly authorized non-sensitive materials. Never invent UT resources, policies, links, procedures, steps, fees, deadlines, form fields, citations, or demo results.
- **UI:** keep Larry's floating chatbot and Streamlit's built-in Light/Dark/System theme toggle. Never pin `[theme] base` in `.streamlit/config.toml`.
- **Staff Bulletin (Milestone 5, approved and implemented):** a read-only top-level section next to Resources (`reslink/bulletin.py`, `data/bulletins.json`). It must stay **independent of Larry and the AI pipeline**: never index bulletins, send them to Gemini, or import `reslink.bulletin` from retrieval/semantic/assistant/ingest/procedures (tests enforce this). No creation/editing UI, notifications, database, or auth. The current announcements are fictional demonstration data and must stay labeled as such (`"demo_data": true`, `[Demo]` titles); never add real private staff communications.
- **Privacy:** never ingest, request, log, or store resident personal information, confidential reports, or sensitive staff records. Never commit or print credentials.

## Working rules

1. **Plan first:** inspect the repository, summarize current state, propose the smallest next step, and wait for approval before substantial changes, architectural changes, or scope additions.
2. **Demo reliability over features:** keep the keyword-only and "sources only" fallbacks working. Prefer small, verifiable changes.
3. **No fabricated data:** add catalog entries to `data/resources.json` only after the team has verified the source. Tests use explicitly marked placeholders (reserved `example.*` hosts) only; never show placeholders as real university sources. Never "correct" the procedure transcription; flag issues in its sidecar `.meta.json` and `docs/SOURCE_REVIEW.md`.
4. **Guard against hallucinations:** answer only from retrieved evidence. Build links only from validated catalog metadata, never from model output. Show uncertainty, incomplete sources, and retrieval failure explicitly.
5. **Keep code approachable:** readable Python modules, type hints, small functions, docstrings where useful, minimal abstractions, simple error handling. Only `app.py`, `reslink/ui.py`, and `reslink/larry.py` import Streamlit.
6. **Validate changes:** run `pytest` (offline) after each meaningful change, plus `scripts/compare_retrieval.py` for retrieval changes. Live Gemini checks use a small, stated budget (`scripts/check_gemini.py` = 1 call; `scripts/run_eval.py --live` = 8 calls). Report what was and wasn't tested.
7. **Respect collaboration:** never commit or push. The user commits through GitHub Desktop. Don't overwrite teammate changes, delete files without approval, or modify unrelated modules.
8. **Protect secrets:** `.env` holds the key (git-ignored); `.env.example` holds names only. Check configuration with `reslink.config.load_settings()`, and don't read `.env` directly.
9. **Document decisions:** record approved changes in `docs/DECISIONS.md`, measured results in `docs/EVALUATION.md`, and keep `docs/ARCHITECTURE.md` and `docs/SESSION_HANDOFF.md` in sync.
10. **Tooling note (Windows / Git Bash):** use the Edit tool instead of bash heredocs for Python source edits; heredocs have turned `\n` inside Python strings into real line breaks.
