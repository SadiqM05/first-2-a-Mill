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

## 2026-11-14 — Milestone 3: hybrid semantic retrieval (approved)

23. **ChromaDB + built-in ONNX all-MiniLM-L6-v2**, no torch. Stays on Python 3.14 (chromadb 1.5.9 / onnxruntime 1.32 wheels verified); installed into the existing `.venv`. Model (79 MB) cached in `~/.cache/chroma` on first `build_index`; the app never triggers the download. Anonymized telemetry disabled.
24. **What is embedded:** catalog metadata (title, category, description, keywords; no URLs) for every verified resource, plus public PDF chunks. Portal contents are never indexed. Index at `data/index/chroma` (git-ignored), rebuilt from scratch by `python -m scripts.build_index`; a content fingerprint on the collection detects stale indexes.
25. **Hybrid = reciprocal rank fusion (k=60)**, separately for catalog evidence and document pages. Keyword retrieval unchanged and always included. Semantic contributes its nearest catalog entry (distance ≤ 0.65) and up to 2 pages from its 8 nearest chunks (≤ 0.75). Output: up to 3 catalog + 3 pages. Cutoffs/limits tuned with `scripts/compare_retrieval.py` (docs/EVALUATION.md).
26. **Semantic similarity never decides support.** Supported/unsupported distances overlap; Gemini's sufficient flag + citation validation remain the gate. Semantic hits only map to existing catalog IDs / indexed chunks; anything else is dropped.
27. **Fallback:** missing/stale/erroring semantic index → keyword-only (sidebar says why). Retriever cached per process (`st.cache_resource`) keyed on content fingerprint + index file time.
28. **Stricter insufficient-evidence rule (approved 2026-11-14):** the Gemini instructions now say `sufficient` may be true only when the evidence directly answers the specific question; merely mentioning the topic is not enough. Fixes the weekly-report regression introduced by broader hybrid evidence (verified with 3 live calls; docs/EVALUATION.md).

## 2026-11-14 — Milestone 4: procedures knowledge base (approved)

29. **Front Desk Manual transcription** indexed from `data/procedures/residence_hall_front_desk_knowledge_base.md`: `##` = group with required page range, `###` = one procedure (one whole chunk, never split), group intro = "… — Overview" unit, group without `###` = one unit. Bodies stored verbatim; parsed live on app start (edits apply immediately; semantic index flagged stale until rebuilt).
30. **Catalog extension:** category `procedures`; content type `transcription` = the only type with no URL (must have none) and a required `source_path`. All other types keep the https URL rule. Dashboard card shows no link.
31. **Citations:** procedure evidence IDs `front-desk-manual#<section-slug>`; citations render "Front Desk Residence Hall Manual, § Section, pp. X–Y" with no link. Retrieval groups by citation unit (PDF page or procedure section); PDF behavior unchanged.
32. **Trust signals by code, not model:** every cited transcription adds "not independently verified as current"; "Source limitation" text → "Incomplete source" notice; questionable passages flagged in the sidecar `.meta.json` → "Flagged for review". The Markdown is never corrected (docs/SOURCE_REVIEW.md).
33. **Links:** related verified resources attached per procedure via sidecar catalog IDs only. The transcription's housing.utk.edu URL is unverified (403 to automated checks) → replaced in evidence, never linked; lockout procedures link the verified Lockout Card Access portal.
34. **Prompt rules:** full walkthrough → all steps in order with sub-steps/notes; specific question → answer only that; never invent steps/fees/deadlines/fields; keep template placeholders; never request or repeat personal details. Inline numbered answers are re-lined by code (formatting only, words unchanged).
35. **Privacy check:** obvious IDs/SSNs/emails/phones block retrieval and Gemini and are redacted from session history. Explicitly not comprehensive.
36. **Hybrid tuning:** semantic page candidates 2 → 1 (fixed a PDF regression caused by procedure units; best R@3). A heading-weight boost was tried and rejected.
