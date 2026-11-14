"""Run tests/eval_questions.json through the full pipeline with the real Gemini API.

Usage:  python -m scripts.run_eval [--live] [--keyword-only] [--out data/index/eval_results.json]

--live          only the questions marked "live" (the ~8-call budget); otherwise all questions.
--keyword-only  use keyword retrieval (for comparison); default is hybrid when the index is ready.

Makes one Gemini call per question that has retrieved evidence. For each question it checks:
- status matches expected_status (grounded / insufficient_evidence);
- citation correctness: grounded answers cite at least one expected target and list any
  citations outside the targets; unsupported questions must end with no citations.
Results are observations, not claims: read the answers and verify facts/links by hand.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from reslink.assistant import GeminiGenerator, answer_question
from reslink.catalog import load_catalog
from reslink.config import PROJECT_ROOT, load_env_file, load_settings
from reslink.ingest import load_chunks
from reslink.models import slugify
from reslink.retrieval import HybridRetriever, KeywordRetriever
from reslink.semantic import CATALOG_MAX_DISTANCE, DEFAULT_MAX_DISTANCE, SemanticIndex

QUESTIONS = PROJECT_ROOT / "tests" / "eval_questions.json"


def targets(case: dict) -> set[str]:
    out = set(case.get("expected_evidence", []))
    if case.get("expected_catalog"):
        out.add(case["expected_catalog"])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", action="store_true", help="only questions marked with --tag (quota budget)")
    parser.add_argument("--tag", default="live", help="which live set to run with --live (e.g. live, live_m6)")
    parser.add_argument("--keyword-only", action="store_true")
    parser.add_argument("--delay", type=float, default=1.5, help="seconds between questions (rate limits)")
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "data" / "index" / "eval_results.json")
    args = parser.parse_args(argv)

    load_env_file()
    settings = load_settings()
    if not settings.gemini_configured:
        print("GEMINI_API_KEY and GEMINI_MODEL must be set in .env", file=sys.stderr)
        return 1

    resources = load_catalog(settings.catalog_path)
    chunks, warnings = load_chunks(settings.index_path, resources, PROJECT_ROOT)
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    keyword = KeywordRetriever(resources, chunks)
    index, status = (None, "disabled (--keyword-only)") if args.keyword_only else SemanticIndex.open(
        settings.chroma_path, resources, chunks)
    retriever = HybridRetriever(keyword, index, max_distance=DEFAULT_MAX_DISTANCE,
                                catalog_max_distance=CATALOG_MAX_DISTANCE)
    generator = GeminiGenerator(settings.gemini_api_key, settings.gemini_model)

    cases = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    if args.live:
        cases = [c for c in cases if c.get(args.tag)]
    mode = "hybrid" if index is not None else f"keyword only ({status})"
    print(f"model={settings.gemini_model} retrieval={mode} questions={len(cases)}\n")

    results, status_ok, cite_ok = [], 0, 0
    answered: dict[str, str | None] = {}  # question -> answer, for multi-turn "follow_up_of" cases
    for n, case in enumerate(cases):
        if n:
            time.sleep(args.delay)
        history = []
        if case.get("follow_up_of"):
            prev = case["follow_up_of"]
            if prev not in answered:
                print(f"SKIP  follow-up needs '{prev}' earlier in this run: {case['question']}\n")
                continue
            history = [(prev, answered[prev])]
        start = time.time()
        response = answer_question(case["question"], retriever, generator, history=history)
        answered[case["question"]] = response.answer
        elapsed = time.time() - start
        cites = [
            f"{c.resource.id}#{slugify(c.section)}" if c.section
            else f"{c.resource.id}" + (f"@p{c.page}" if c.page else "")
            for c in response.citations
        ]
        want = targets(case)
        if response.status.value in ("grounded", "partial"):
            on_target = bool(set(cites) & want)
            off_target = [c for c in cites if c not in want]
            citation_ok = on_target if want else False  # grounded on an unsupported question = bad
        else:
            on_target, off_target = False, []
            citation_ok = not cites
        checks = []
        if case.get("walkthrough_steps") and response.answer:
            # Completeness: every documented top-level step number must appear in the answer.
            steps = {int(n) for n in re.findall(r"^\s*(\d+)\.", response.answer, flags=re.M)}
            complete = set(range(1, case["walkthrough_steps"] + 1)) <= steps
            checks.append(f"walkthrough steps {len(steps)}/{case['walkthrough_steps']} "
                          f"{'OK' if complete else 'INCOMPLETE'}")
            citation_ok = citation_ok and complete
        for key in ("expected_caveat", "expected_caveat_any"):
            if case.get(key) and response.status.value in ("grounded", "partial"):
                has = any(case[key] in c.text for c in response.caveats)
                checks.append(f"caveat '{case[key]}' {'present' if has else 'MISSING'}")
                citation_ok = citation_ok and has
        text = (response.answer or "").lower()
        if case.get("must_include_any") and response.answer:
            has = any(s.lower() in text for s in case["must_include_any"])
            checks.append(f"includes one of {case['must_include_any']}: {'OK' if has else 'MISSING'}")
            citation_ok = citation_ok and has
        if case.get("must_include_all") and response.answer:
            lacking = [s for s in case["must_include_all"] if s.lower() not in text]
            checks.append(f"includes all of {case['must_include_all']}: {'OK' if not lacking else f'MISSING {lacking}'}")
            citation_ok = citation_ok and not lacking
        if case.get("must_not_include") and response.answer:
            found = [s for s in case["must_not_include"] if s.lower() in text]
            checks.append(f"must not include {case['must_not_include']}: {'OK' if not found else f'FOUND {found}'}")
            citation_ok = citation_ok and not found
        expected = case.get("expected_status_any") or [case["expected_status"]]
        s_ok = response.status.value in expected
        status_ok += s_ok
        cite_ok += citation_ok
        print(f"{'PASS' if s_ok else 'FAIL'}  {response.status.value:22} {elapsed:4.1f}s  {case['question']}")
        print(f"      cites: {cites or '-'}  citation_ok={citation_ok}"
              + (f"  off-target: {off_target}" if off_target else ""))
        for check in checks:
            print(f"      check: {check}")
        for caveat in response.caveats:
            print(f"      note[{caveat.kind}]: {caveat.text}")
        print(f"      resources: {[r.id for r in response.resources]}")
        print(f"      answer: {response.answer or response.notice}\n")
        results.append({
            "question": case["question"], "expected_status": case["expected_status"],
            "status": response.status.value, "answer": response.answer, "notice": response.notice,
            "citations": cites, "targets": sorted(want), "citation_ok": citation_ok,
            "off_target_citations": off_target, "links": [c.link for c in response.citations],
            "seconds": round(elapsed, 2), "retrieval": retriever.last_mode,
            "caveats": [{"kind": c.kind, "text": c.text} for c in response.caveats], "checks": checks,
            "history": history,
            "resources": [r.id for r in response.resources],
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"status matched: {status_ok}/{len(cases)}   citations correct: {cite_ok}/{len(cases)}   "
          f"median latency: {sorted(r['seconds'] for r in results)[len(results) // 2]}s\nResults: {args.out}")
    return 0 if status_ok == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
