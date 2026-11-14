# AGENTS.md — Shared rules for ResLink AI

Rules for anyone (human or AI agent) changing this repo. Product intent is in
`docs/PRD.md`, design in `docs/ARCHITECTURE.md`, approved changes in
`docs/DECISIONS.md`. Claude-specific workflow is in `CLAUDE.md`.

## Non-negotiables

- **No fabricated data.** Never invent UT resources, policies, deadlines, or URLs.
  `data/resources.json` holds only entries a team member has opened and verified.
- **Links come from the catalog.** UI links are built from validated catalog entries,
  never from model output. Model citations are mapped to retrieved resource IDs; unknown IDs are dropped.
- **Grounded or honest.** Answer only from retrieved evidence. If evidence is missing,
  return `insufficient_evidence`; don't guess.
- **Public, non-sensitive sources only.** No resident PII, incident reports, or internal staff records.
- **Secrets stay in `.env`.** Never commit keys; never print them in the UI or logs.
- **Staff bulletin is stretch-only.** Not implemented without explicit approval.

## Code layout

- `app.py` — Streamlit entry point; wiring only.
- `reslink/ui.py` — Streamlit rendering only.
- `reslink/*` (everything else) — core logic; **must not import Streamlit**.
- Test fixtures use reserved hosts (`example.org`/`.com`/`.net`) and are titled `PLACEHOLDER`.
  The catalog loader rejects those hosts by default.

## Workflow

- Python 3.14 target (3.12 side-by-side venv is the documented fallback). `pip install -r requirements-dev.txt`, then `pytest` before every commit.
- Small, focused changes; don't rewrite a teammate's module without coordinating.
- Record approved architecture/scope changes in `docs/DECISIONS.md`.
