# ResLink AI — Your Intelligent RA Resource Navigator

VolHacks 2026 project by team First2aMill. A local Streamlit dashboard and grounded
assistant that helps UT FDB Hall RAs find verified public university resources.
See `docs/PRD.md` and `docs/ARCHITECTURE.md`.

**Status:** Milestone 1. Catalog validation and resource dashboard work. The AI assistant
is not connected yet. The catalog is empty until verified resources are added.

## Setup (Python 3.12)

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env   # then fill in GEMINI_API_KEY and GEMINI_MODEL
```

**macOS / Linux**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # then fill in GEMINI_API_KEY and GEMINI_MODEL
```

## Run

```bash
streamlit run app.py
pytest
```

## Migrating an existing venv to 3.12

If your `.venv` was created with another Python version (check `.venv/pyvenv.cfg`):

1. Install Python 3.12 (Windows: `winget install Python.Python.3.12` or python.org).
2. Create a side-by-side env first: `py -3.12 -m venv .venv312`, then install requirements into it and run `pytest`.
3. Once it passes, delete the old `.venv` and rename `.venv312` to `.venv` (or keep using `.venv312`; both are git-ignored).

## Adding resources

Add entries to `data/resources.json` only after opening and verifying the source.
Required fields: `id`, `title`, `category` (`maintenance`, `reporting`, `programming`, `policies`), and `url` (https).
Optional fields: `content_type` (`webpage`, `pdf`, `form`), `description`, `keywords`.
The app refuses to load the catalog if any entry is invalid and shows every problem it found.
