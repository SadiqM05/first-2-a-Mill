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

## 2026-11-13 — First resources + Milestone 2

11. **First verified resources** (supplied by team, inspected 2026-11-13): maintenance request portal (Asset Essentials), lockout card access (Housing RA login), roster (StarRez). All three are **sign-in-only portals**; only their login pages are publicly visible. Descriptions combine what the login page shows with the purpose the team gave for each link. Keywords are search terms for retrieval, not claims about the systems.
12. **New category `ra_portals`** ("RA Portals") for lockout and roster systems, which fit none of the original four. **New content type `portal`** = sign-in-only system: linkable, not ingestible; UI marks it "sign-in required".
13. **Keyword retrieval runs over catalog metadata** (title, category, description, keywords). Portals have no public text to ingest, so document ingestion waits for public pages/PDFs.
14. **Gemini output contract:** JSON (`sufficient`, `answer`, `cited_ids`) via `response_json_schema`. Code keeps only cited IDs that were retrieved, withholds answers with no valid citation, strips model-written URLs, and never sends URLs to the model. Temperature is left at the model default (no model name assumed).
15. **Failure behavior:** no retrieval match → no model call, honest insufficient-evidence reply. Gemini not configured / failing / malformed output → `error` status with matching verified resources shown ("sources only"). Only the exception type is displayed.
16. **Retrieval tuning:** "resident" treated as a stopword (it appears in most RA questions and caused false matches).

## 2026-11-13 — Documents, page citations, live Gemini

17. **New resources:** Incident Report Form (Maxient; `reporting`, `portal`, redirects to UT CAS sign-in), RA Job Description PDF (`policies`, 6 pages, Residence Life Manual pp. 44-49), University Housing Policies PDF (`policies`, 8 pages, file dated 7.21.2023). Maintenance portal gained keyword "schooldude" because the job description says "Submit SchoolDude work orders" (Dude Solutions, the portal's domain, was formerly SchoolDude).
18. **Ingestion:** `python -m scripts.build_index` downloads catalog PDFs to `data/documents/`, extracts text per page (PyMuPDF), chunks into 250-word windows with 50-word overlap per page, and writes `data/index/chunks.json` (git-ignored, rebuildable). Chunks whose resource or URL no longer matches the catalog are ignored at load time.
19. **Document retrieval:** BM25-style IDF over chunk tokens; a chunk needs at least 2 distinct query words (or all words of a 1-word query). Matching chunks are merged per page, giving one evidence block per page. Catalog and document hits are ranked separately and both sent (up to 3 each).
20. **Page-level citations:** document evidence IDs are `resource-id@pN` (PDF page index, not the printed manual page). PDF links get `#page=N`, built from the catalog URL by code.
21. **Gemini resilience:** one retry with backoff on 429/5xx; failures show exception type + numeric status only. `scripts/run_eval.py` runs the eval set live (1.5 s between calls).
22. **Catalog scoring fix:** each query word counts once at its strongest field (title > category > description) so "report" no longer double-counts via title + "Reporting" category.
