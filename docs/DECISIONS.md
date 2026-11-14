# Decisions log

## 2026-11-13 — Phase 0 / Milestone 1 (approved by team)

1. **Docs tracked in Git.** Removed `docs/` and `claude.md` from `.gitignore`; renamed `claude.md` → `CLAUDE.md` to match references (case-sensitive on macOS/Linux).
2. **Requirements.** `requirements.txt` is a UTF-8 list of direct dependencies with minimum versions; `requirements-dev.txt` adds pytest. Replaces the previous UTF-16 `pip freeze` dump.
3. **Python 3.12** is the target (`.python-version`). Existing 3.14 venv is kept until the team migrates; see README.
4. **Embeddings:** ChromaDB's built-in ONNX embedding function first, instead of Sentence Transformers (avoids the torch download). Revisit only if retrieval quality is inadequate.
5. **Gemini** via `google-genai`; `GEMINI_API_KEY` and `GEMINI_MODEL` from env. No model name hardcoded in application code.
6. **Package layout:** core logic in `reslink/` (instead of `services/` from the architecture sketch) so tests import cleanly; Streamlit confined to `app.py` and `reslink/ui.py`.
7. **Retrieval order:** keyword retrieval over the catalog first, ChromaDB semantic retrieval second, behind one interface. Keyword stays as fallback.
8. **Catalog guard:** loader rejects reserved placeholder hosts (`example.org/.com/.net`) unless a test explicitly allows them; validation is all-or-nothing and reports every error.
9. **Initial categories:** maintenance, reporting, programming, policies (from PRD; revisit once real resources are collected).
10. **Staff bulletin:** remains stretch-only; not implemented.
