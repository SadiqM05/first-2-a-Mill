# ResLink AI — Session Handoff

**Written:** 2026-11-14, at the end of the Milestone 4 session. **Refreshed:** 2026-11-14,
after Milestone 4 was committed (`8dff352`) and after the approved repository cleanup.
**Purpose:** let a fresh Claude Code session pick up without the previous conversation.
**Sources:** facts below were checked against the repository, `git`, and a test run at the time
of writing. Each item is marked as **done**, **uncommitted**, or **proposed**. No secrets are in
this file.

---

## 1. Project overview

**What it does.** ResLink AI is a local Streamlit app for University of Tennessee Resident
Assistants (FDB / Brown Hall). It has a dashboard of **verified** resources and **Larry**, a
floating chat assistant. Larry answers only from retrieved evidence: catalog metadata, two public
UT PDFs, and a transcribed Front Desk Manual. Its answers cite their sources and link only to
verified catalog URLs. If the evidence doesn't support an answer, it says so instead of guessing.

**Hackathon scope and constraints** (from `CLAUDE.md`, `docs/PRD.md`, and the user's instructions):
- 18-hour, two-person hackathon (VolHacks 2026, team First2aMill). The goal is a reliable demo.
- Local-first. No deployment, auth/RBAC, FastAPI/React, cloud infrastructure, or extra frameworks.
- Only public or explicitly approved non-sensitive sources. Never fabricate resources, URLs,
  policies, procedures, fees, deadlines or citations.
- No resident personal information is requested, logged or stored.
- The staff bulletin is a **stretch goal only**. It is not implemented and not approved.

**Stack.** Python 3.14.3 (`.venv`), Streamlit 1.67, `google-genai` 3.3.0 (Gemini, model from
`GEMINI_MODEL`), ChromaDB 1.5.9 with its built-in ONNX all-MiniLM-L6-v2 embeddings (no torch),
PyMuPDF, pytest 9.2.

**Request flow:**
```
question -> privacy check (obvious IDs/emails/phones -> blocked, no API call)
         -> HybridRetriever: keyword (catalog + document units) + Chroma semantic, fused by RRF
         -> Gemini (JSON: sufficient / answer / cited_ids), prompt = evidence only
         -> code validates citations against retrieved evidence, strips model URLs,
            adds source caveats and related catalog links, formats inline step lists
         -> Larry renders answer + caveats + verified cards
```

**Key files.**

| File | Responsibility |
|---|---|
| `app.py` | Streamlit entry point. Loads catalog and chunks, builds a cached retriever, renders the dashboard and Larry. |
| `reslink/models.py` | Dataclasses: `Resource`, `Chunk`, `Evidence`, `Citation`, `AssistantResponse`, `Status`; categories and content types. |
| `reslink/config.py` | Settings from env/.env: `GEMINI_API_KEY`, `GEMINI_MODEL`, and the optional `RESLINK_CATALOG_PATH` / `RESLINK_INDEX_PATH` / `RESLINK_CHROMA_PATH`. |
| `reslink/catalog.py` | Strict validation of `data/resources.json`. Rejects placeholder hosts; a `transcription` has no URL. |
| `reslink/ingest.py` | PDF text extraction, chunking, `chunks.json` I/O, and `load_chunks()` (PDF chunks + procedures). |
| `reslink/procedures.py` | Markdown procedures parser (`##` group with page range, `###` procedure) plus the sidecar `.meta.json`. |
| `reslink/retrieval.py` | `KeywordRetriever` (catalog scoring + BM25-style units), `HybridRetriever` (RRF fusion), evidence text builders. |
| `reslink/semantic.py` | ChromaDB index: build/open, fingerprint stale detection, kind-filtered search, telemetry off. |
| `reslink/assistant.py` | Gemini prompt (rules 1–11), output parsing, citation validation, caveats, `format_steps`, notices. |
| `reslink/privacy.py` | Pattern check and redaction for obvious personal information. **Not comprehensive.** |
| `reslink/ui.py` | Streamlit rendering: header, sidebar status, dashboard tabs, resource cards, responses. |
| `reslink/larry.py`, `reslink/static/larry.css` | Floating chat widget (launcher/panel, fragment, session history). CSS uses only `.st-key-larry-*` classes and theme-aware colors. |
| `scripts/build_index.py` | Downloads catalog PDFs, writes `data/index/chunks.json`, builds the Chroma index (with procedures). |
| `scripts/compare_retrieval.py` | Offline keyword vs hybrid metrics (`--sweep` for thresholds). |
| `scripts/run_eval.py` | Live Gemini evaluation (`--live` = budgeted subset). |
| `scripts/check_gemini.py` | Pre-demo Gemini connectivity check through the app's own settings and wrapper (1 request, key never printed). |
| `data/resources.json` | Verified catalog (7 entries). |
| `data/procedures/residence_hall_front_desk_knowledge_base.md` (+ `.meta.json`) | Front Desk Manual transcription and its sidecar (related links, review flags). |
| `docs/PRD.md` | Original product spec. |
| `docs/ARCHITECTURE.md` | The system as built (updated in the cleanup). |
| `docs/DECISIONS.md` | Decision log, items 1–36. **Read this first** for any "why". |
| `docs/EVALUATION.md` | Measured retrieval and live results for Milestones 3 and 4. |
| `docs/SOURCE_REVIEW.md` | Transcription passages that need manual verification. |
| `AGENTS.md`, `CLAUDE.md` | Shared rules and Claude workflow. |

---

## 2. Development progress

| Milestone | Status | Commit |
|---|---|---|
| Phase 0 + M1: repo fixes, catalog validation, dashboard | **Done, committed** | `aa0f909` |
| M2: keyword retrieval, Gemini integration, PDF ingestion, page citations | **Done, committed** | `1b823c5` |
| UI: Larry floating chatbot, theme toggle restored | **Done, committed** | `a015a71` |
| M3: hybrid retrieval (ChromaDB + RRF), stricter `sufficient` rule | **Done, committed** | `92c425e` |
| M4: procedures knowledge base, privacy check, section citations | **Done, committed** | `8dff352` |
| Repository cleanup (approved audit) | **Done, NOT committed** | (working tree; see §3) |
| Staff bulletin (stretch) | Not started, not approved | — |

**Features implemented (all done):**
- **Catalog:** 7 verified resources. Five are portals or PDFs with checked URLs (maintenance/Asset
  Essentials, lockout card access, StarRez roster, Maxient incident form), two are public PDFs (RA
  Job Description, Housing Policies), plus the Front Desk Manual transcription (no URL). Categories:
  maintenance, reporting, programming, policies, ra_portals, procedures.
- **Retrieval:** keyword (catalog fields + IDF over document units) and semantic (Chroma, catalog
  metadata and documents searched separately), fused by RRF. Falls back to keyword-only if the
  index or model is missing, stale or erroring; the sidebar shows the mode.
- **Grounding safeguards:**
  - citations must match retrieved evidence IDs, and invented IDs are dropped;
  - an answer with no valid citation is withheld;
  - URLs written by the model are stripped, and links come only from the catalog;
  - `sufficient` only when the evidence directly answers the question;
  - an explicit insufficient-evidence reply when it doesn't.
- **Citations:** PDF pages (`resource@pN`, link `#page=N`). Procedures (`front-desk-manual#<slug>`),
  rendered as "Front Desk Residence Hall Manual, § Section, pp. X–Y" with no link.
- **Larry:** a floating launcher and panel (bottom-right, responsive). History survives
  closing/reopening; the input is disabled while answering; spinner. Follows the built-in
  System/Light/Dark theme menu, with no config pinning the theme.

**Major decisions** (full list in `docs/DECISIONS.md`):
- Python **3.14** (3.12 is the documented fallback).
- Chroma's ONNX embeddings, not sentence-transformers.
- No hardcoded model name.
- Semantic similarity **never** decides whether a question is supported; Gemini plus citation
  validation does.
- Portals are never ingested, only their catalog metadata.

**Milestone 4 changes (committed in `8dff352`):**
- New `procedures` category and `transcription` content type (no URL, requires `source_path`).
- New `reslink/procedures.py`: 18 units from the manual (16 procedures, the Mail overview, the
  School Dude reference). Stored verbatim, one whole chunk each.
- Retrieval groups by citation unit (PDF page or procedure section). Semantic page candidates
  2 → 1, which fixed a PDF regression.
- Code-added caveats: "not independently verified as current", "Incomplete source", "Flagged for
  review".
- Related links come from sidecar catalog IDs only. The unverified housing.utk.edu URL is replaced
  in evidence and never linked.
- Prompt rules 8–11: walkthrough vs specific-step answers, no invented steps/fees, keep template
  placeholders, never request personal details.
- `format_steps()` puts inline numbered answers on separate lines (formatting only).
- Privacy check and redaction of chat history; Larry's placeholder says "no resident names or IDs".

---

## 3. Current repository state (refreshed after cleanup)

- **Branch:** `main`. **Latest commit:** `8dff352 feat: integrate procedural knowledge into Larry`.
  All Milestone 4 work, including `data/procedures/` and this file, is committed.
- **Uncommitted: the approved repository cleanup** (no behavior change; tests unchanged):
  - `reslink/assistant.py`: removed the unused `resolve_citations()`;
  - `requirements.txt`: dropped the unused `beautifulsoup4`, Python version comment now 3.14;
  - `.env.example`: **restored**, variable names only;
  - `data/documents/.gitkeep`: deleted (the folder holds tracked PDFs);
  - `.gitignore`: removed the obsolete `chroma_db/` rule, added `.claude/settings.local.json`;
  - `AGENTS.md`: Python 3.14 target;
  - `scripts/check_gemini.py`: refactored to use the app's settings and Gemini wrapper (1 request,
    no hardcoded model, key never printed);
  - `docs/ARCHITECTURE.md`: rewritten to describe the system as built;
  - `CLAUDE.md`: first-hour sections removed, points to this file;
  - `docs/SESSION_HANDOFF.md`: this refresh.
- **Ignored, do NOT commit:** `.env` (contains `GEMINI_API_KEY`, `GEMINI_MODEL`), `.venv/`,
  `.pytest_cache/`, and `data/index/`. `data/index/` holds `chunks.json`, `chroma/`, and the eval
  result JSONs; all of it can be rebuilt.
- **Committed data:** `data/documents/housing-policies.pdf` and `ra-job-description.pdf` (public UT
  PDFs) are tracked, so the index can be built offline.
- **Outside the repo:** the ONNX model cache `~/.cache/chroma/onnx_models/all-MiniLM-L6-v2` (~167 MB
  extracted). It's needed for semantic search without network access.
- The user commits manually with GitHub Desktop. **Never commit or push from Claude.**

---

## 4. Testing and evaluation (measured 2026-11-14)

**Automated:** `pytest` → **313 passed, 4 xfailed** (about 25 s, offline, no Gemini calls). The
4 xfails are documented known misses:
- keyword-only: "How do I return a letter to sender?" (hybrid finds it), "What is SC Logic?";
- hybrid: "My resident can't get into their room" (lockout portal not surfaced), "What is SC Logic?".

**Offline retrieval** (`python -m scripts.compare_retrieval`, 47 questions, 38 supported):

| | Keyword | Hybrid |
|---|---|---|
| Recall@1 / Recall@3 (all supported) | 68% / 79% | 76% / **95%** |
| PDF/catalog questions, R@3 (n=24) | 79% | **96%** |
| Procedure questions, R@1 / R@3 (n=14) | 57% / 79% | **50%** / 93% |
| Paraphrased, R@3 (n=10) | 40% | 90% |
| Retrieval latency, median | <1 ms | ~38 ms |

Tuning was done on the same question set it's scored on, so these numbers are optimistic.

**Live Gemini** (`gemini-3.5-flash-lite`, M4 run: 8 API calls + 1 blocked): status matched **9/9**.
- Walkthroughs complete (check-in 12/12 steps, recore 11/11).
- Specific-step answers were direct.
- Incomplete source flagged (Return to Sender).
- Missing steps declined (School Dude steps 1–3); refund declined.
- Privacy bait blocked with 0 calls.
- PDF regression check (pet) correct.

Every fact was checked by hand against the sources. The check-in answer came back on one line;
`format_steps` was added afterwards and verified only offline. Details are in `docs/EVALUATION.md`.

**Known limitations:**
- Unsupported questions usually still reach Gemini, which uses quota. The free-tier rate limit
  (HTTP 429) has been hit before when running evals back to back.
- Procedure top-1 ranking is weaker than top-3 (another procedure sometimes ranks first).
- Procedure page ranges are per group, so citations aren't page-precise.
- The privacy check misses names, room numbers, NetIDs and birthdays written out in words.
- The dark-mode panel background (`Canvas`) is close to, but not exactly, Streamlit's dark
  background.

**Manual checks still required:**
- Run `python -m scripts.run_eval --live` once (8 calls) to confirm `format_steps` on live output.
  Don't run it right before the demo.
- Real-browser pass: Procedures tab, Larry walkthrough, privacy block, theme toggle, phone layout.
  The previous session used a scratch Playwright venv that won't exist in a new session.
- The source-review items in §5.
- The teammate's install on their own OS (Python 3.14 wheels for chromadb/onnxruntime).

---

## 5. Remaining work

**Source review** (user action; see `docs/SOURCE_REVIEW.md`):
1. Excessive Lockouts — Access Cards: the manual note says "lost lockout charges" (possibly copied
   in transcription).
2. Excessive Lockouts — Keys: one step fewer than the Access Cards version.
3. Giving Recored Keys: the recore-charging note may belong under Steps for Recore.
4. `https://housing.utk.edu/information-technology/` is **unverified**. Automated requests get HTTP
   403 from Cloudflare. If the user verifies it, add it to `resources.json` and to the sidecar's
   `related` lists.

**Gaps found at the first handoff: resolved by the approved cleanup (uncommitted):**
- ~~`.env.example` missing~~: restored, names only.
- ~~`requirements.txt` says Python 3.12~~: now 3.14; unused `beautifulsoup4` removed.
- ~~`scripts/check_gemini.py` hardcoded model / separate API~~: now uses the app's integration.
- ~~`docs/ARCHITECTURE.md` out of date~~: rewritten to match the code.

**Still open:**
- PRD demo scenarios 1 (weekly report) and 2 (hall program) have **no supporting source**, and Larry
  correctly declines them. Per the PRD, replace them with supported scenarios for the demo.

**Demo preparation priorities (proposed):**
1. The user commits the cleanup.
2. Run `python -m scripts.check_gemini` (1 call) to confirm the key, model and quota.
3. Run `build_index` on the demo machine ahead of time (model download, ~79 MB).
4. One live eval run to confirm, then freeze features.
5. Write a demo script using **supported** scenarios, for example:
   - a lockout card walkthrough with a related portal link;
   - "Can I have a pet?" (a paraphrase that hits PDF p1);
   - "How do I check in a package?" (full walkthrough);
   - an unsupported question that's declined honestly;
   - the privacy block;
   - toggling the theme.
6. Take backup screenshots in case of quota or network failure. Keyword-only and "sources only"
   modes still work without Gemini.

**Recommended next milestone (proposed, not approved): "M5: demo hardening and freeze".** The
repo fixes are done; what remains:
- a final live eval (confirms `format_steps` on live output);
- a real-browser pass;
- a demo script in `docs/DEMO.md` using supported scenarios;
- backup screenshots;
- a rehearsal on the demo machine.

Only consider the staff bulletin if the user explicitly approves it after M5.

---

## 6. Development instructions

```powershell
# Install (Windows; macOS/Linux: python3.14 -m venv .venv && source .venv/bin/activate)
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

**Environment.** Copy `.env.example` to `.env` and fill in `GEMINI_API_KEY` (your key) and
`GEMINI_MODEL` (a model your account can use); the three `RESLINK_*_PATH` overrides are optional.
Check connectivity with `python -m scripts.check_gemini` (1 request). `.env` is git-ignored. **Never print, log or commit
the key.** Claude should check configuration with `load_settings().gemini_configured` and never read
`.env` directly. To run without Gemini, set `GEMINI_MODEL` to empty; the app then shows
"sources only" answers.

```powershell
python -m scripts.build_index        # PDFs -> chunks.json -> Chroma (+ procedures). Stop the app first.
streamlit run app.py                 # sidebar should show: 7 resources, 46 passages, Retrieval: hybrid
pytest                               # offline, ~25 s, expect 313 passed / 4 xfailed
python -m scripts.compare_retrieval --sweep   # offline retrieval metrics
python -m scripts.run_eval --live    # LIVE: 8 Gemini calls (quota). --keyword-only to compare.
```

Rebuild the index after editing `data/resources.json`, a PDF, or the procedures Markdown/sidecar.
Until then the sidebar shows the semantic index as **stale** and retrieval falls back to keyword-only.

---

## 7. Decisions and constraints (keep these)

- **Keep the stack:** Streamlit + Gemini (`google-genai`) + ChromaDB with ONNX embeddings, Python 3.14.
- **Keep the UI:** Larry's floating chatbot and the built-in Light/Dark/System toggle. Never add
  `[theme] base` to `.streamlit/config.toml`; a test guards this.
- **No unnecessary infrastructure or dependencies.** No auth, deployment or new frameworks.
- **Demo reliability over new features.** Keep the keyword-only and sources-only fallbacks working.
- **Never fabricate** citations, URLs, procedures, fees, deadlines or form fields. Links come only
  from `data/resources.json`. Don't edit the transcription; flag problems in the sidecar or in
  `SOURCE_REVIEW.md`.
- **No resident personal information** requested, logged or stored.
- **Never commit or push.** The user handles commits in GitHub Desktop.
- Propose a plan and wait for approval before substantial changes (the user's standing workflow).
- Prefer the Edit tool over bash heredocs for Python edits. Heredocs in this Windows/Git Bash
  setup kept turning `\n` inside Python strings into real line breaks.

---

## 8. Resume checklist for the next Claude Code session

1. Read `CLAUDE.md`, `AGENTS.md`, this file, then `docs/DECISIONS.md` (items 1–36).
2. Run `git status` and `git log --oneline -5`. Milestone 4 is `8dff352`. Check whether the user
   committed the repository cleanup (expected new commit after `8dff352`). If not, **don't
   commit**; just note it.
3. Check the environment **without exposing secrets**:
   `python -c "from reslink.config import load_env_file, load_settings; load_env_file(); s=load_settings(); print(s.gemini_model, s.gemini_configured)"`.
4. Run `pytest`. Expect **313 passed, 4 xfailed**; investigate any difference before doing anything
   else.
5. If `data/index/` is missing or the sidebar says stale, run `python -m scripts.build_index`.
6. Ask the user:
   - Did you verify the housing.utk.edu URL?
   - Did you check the 3 flagged transcription passages?
   - Is the M5 "demo hardening" plan approved?
7. Before writing any code, propose the M5 steps (§5) and wait for approval.
