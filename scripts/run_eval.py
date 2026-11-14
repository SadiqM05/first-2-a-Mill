"""Run tests/eval_questions.json through the full pipeline with the real Gemini API.

Usage:  python -m scripts.run_eval [--out data/index/eval_results.json]

Makes one Gemini call per question that has retrieved evidence. Prints a table and
writes raw results (question, status, answer, citations) for manual review in
docs/EVALUATION.md. Results are observations, not claims: verify links by hand.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from reslink.assistant import GeminiGenerator, answer_question
from reslink.catalog import load_catalog
from reslink.config import PROJECT_ROOT, load_env_file, load_settings
from reslink.ingest import load_index
from reslink.retrieval import KeywordRetriever

QUESTIONS = PROJECT_ROOT / "tests" / "eval_questions.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--delay", type=float, default=1.5, help="seconds between questions (rate limits)")
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "data" / "index" / "eval_results.json")
    args = parser.parse_args(argv)

    load_env_file()
    settings = load_settings()
    if not settings.gemini_configured:
        print("GEMINI_API_KEY and GEMINI_MODEL must be set in .env", file=sys.stderr)
        return 1

    resources = load_catalog(settings.catalog_path)
    chunks, warnings = load_index(settings.index_path, resources)
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    retriever = KeywordRetriever(resources, chunks)
    generator = GeminiGenerator(settings.gemini_api_key, settings.gemini_model)

    cases = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    results, passed = [], 0
    print(f"model={settings.gemini_model} resources={len(resources)} chunks={len(chunks)}\n")
    for n, case in enumerate(cases):
        if n:
            time.sleep(args.delay)
        start = time.time()
        response = answer_question(case["question"], retriever, generator)
        elapsed = time.time() - start
        ok = response.status.value == case["expected_status"]
        passed += ok
        cites = [f"{c.resource.id}" + (f"@p{c.page}" if c.page else "") for c in response.citations]
        print(f"{'PASS' if ok else 'FAIL'}  {response.status.value:22} {elapsed:4.1f}s  {case['question']}")
        print(f"      cites: {cites or '-'}")
        print(f"      answer: {response.answer or response.notice}\n")
        results.append({
            "question": case["question"],
            "expected_status": case["expected_status"],
            "status": response.status.value,
            "answer": response.answer,
            "notice": response.notice,
            "citations": cites,
            "links": [c.link for c in response.citations],
            "seconds": round(elapsed, 2),
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{passed}/{len(cases)} matched expected status. Results: {args.out}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
