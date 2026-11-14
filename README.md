# ResLink AI — Your Intelligent RA Resource Navigator

VolHacks 2026 project by team First2aMill. A local Streamlit dashboard and grounded
assistant that helps UT FDB Hall RAs find verified public university resources.
See `docs/PRD.md` and `docs/ARCHITECTURE.md`.

**Status:** Milestone 3. Verified resource dashboard, Larry (floating chat assistant),
hybrid retrieval (keyword + local ChromaDB semantic search) over catalog metadata and public
PDFs, and grounded Gemini answers with page-level citations. See `docs/EVALUATION.md`.

## Setup (Python 3.14, tested; 3.12 is the fallback)

**Windows (PowerShell)**

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env   # then fill in GEMINI_API_KEY and GEMINI_MODEL
```

**macOS / Linux**

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # then fill in GEMINI_API_KEY and GEMINI_MODEL
```

## Run

```bash
python -m scripts.build_index   # PDFs -> chunks.json -> ChromaDB index (rerun after catalog changes; stop the app first)
streamlit run app.py
pytest                          # offline; no Gemini calls
python -m scripts.compare_retrieval --sweep   # offline: keyword vs hybrid retrieval metrics
python -m scripts.run_eval --live              # live: 8 Gemini calls (uses quota)
```

The first `build_index` downloads the embedding model (~79 MB) to `~/.cache/chroma`; do it
before the demo. Afterwards everything except Gemini runs offline.

Without the indexes the app still works: no chunks means catalog-metadata answers only, and no
semantic index means keyword-only retrieval (the sidebar shows which mode is active).

## Fallback: a side-by-side Python 3.12 venv

If `pip install -r requirements.txt` fails on 3.14 (e.g. missing chromadb/onnxruntime wheels on your OS):

1. Install Python 3.12 (Windows: `winget install Python.Python.3.12` or python.org).
2. Create a side-by-side env first: `py -3.12 -m venv .venv312`, then install requirements into it and run `pytest`.
3. Once it passes, delete the old `.venv` and rename `.venv312` to `.venv` (or keep using `.venv312`; both are git-ignored).

## Adding resources

Add entries to `data/resources.json` only after opening and verifying the source.
Required fields: `id`, `title`, `category` (`maintenance`, `reporting`, `programming`, `policies`, `ra_portals`), and `url` (https).
Optional fields: `content_type` (`webpage`, `pdf`, `form`, `portal` for sign-in-only systems), `description`, `keywords`.
After adding a PDF, run `python -m scripts.build_index`.
The app refuses to load the catalog if any entry is invalid and shows every problem it found.
