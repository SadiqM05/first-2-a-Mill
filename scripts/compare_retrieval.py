"""Offline comparison of keyword-only vs hybrid retrieval (no Gemini calls).

Usage:  python -m scripts.compare_retrieval [--sweep] [--json out.json]

For every question in tests/eval_questions.json:
- Supported questions (with expected_catalog / expected_evidence targets):
  Recall@1 = the top catalog hit or the top document page is a target;
  Recall@3 = a target is within the top 3 catalog hits or top 3 document pages.
- Unsupported questions: whether any evidence is returned. Evidence means a Gemini call
  will be made; the answer then depends on Gemini's insufficient-evidence check.
- Latency: retrieval time only.

--sweep prints, per question, the distance of the best semantic hit that is a target
(supported) or the best hit overall (unsupported), and how candidate max-distance
thresholds would affect recall vs. noise. Used to choose DEFAULT_MAX_DISTANCE.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from reslink.catalog import load_catalog
from reslink.config import PROJECT_ROOT, load_settings
from reslink.ingest import load_chunks
from reslink.retrieval import HybridRetriever, KeywordRetriever
from reslink.semantic import CATALOG_MAX_DISTANCE, DEFAULT_MAX_DISTANCE, SemanticIndex

QUESTIONS = Path(__file__).resolve().parent.parent / "tests" / "eval_questions.json"


def targets(case: dict) -> set[str]:
    out = set(case.get("expected_evidence", []))
    if case.get("expected_catalog"):
        out.add(case["expected_catalog"])
    return out


def split(evidence) -> tuple[list[str], list[str]]:
    catalog = [e.evidence_id for e in evidence if e.source == "catalog"]
    docs = [e.evidence_id for e in evidence if e.source == "document"]
    return catalog, docs


def evaluate(retriever, cases: list[dict]) -> dict:
    rows, latencies = [], []
    for case in cases:
        start = time.perf_counter()
        evidence = retriever.retrieve(case["question"])
        ms = (time.perf_counter() - start) * 1000
        latencies.append(ms)
        catalog, docs = split(evidence)
        want = targets(case)
        row = {"question": case["question"], "ms": round(ms, 1), "catalog": catalog, "documents": docs,
               "paraphrase": bool(case.get("paraphrase")), "supported": bool(want)}
        if want:
            row["r1"] = bool({*catalog[:1], *docs[:1]} & want)
            row["r3"] = bool({*catalog[:3], *docs[:3]} & want)
            # citation candidates that are not targets (irrelevant evidence sent to the model)
            row["off_target"] = [e for e in catalog + docs if e not in want and e.split("@")[0] not in
                                 {t.split("@")[0] for t in want}]
        else:
            row["evidence_returned"] = bool(evidence)
        rows.append(row)
    sup = [r for r in rows if r["supported"]]
    para = [r for r in sup if r["paraphrase"]]
    uns = [r for r in rows if not r["supported"]]
    return {
        "rows": rows,
        "recall@1": sum(r["r1"] for r in sup) / len(sup),
        "recall@3": sum(r["r3"] for r in sup) / len(sup),
        "paraphrase_recall@3": sum(r["r3"] for r in para) / len(para) if para else None,
        "unsupported_with_evidence": sum(r["evidence_returned"] for r in uns),
        "avg_evidence_items": round(statistics.mean(len(r["catalog"]) + len(r["documents"]) for r in rows), 2),
        "off_target_items_supported": sum(len(r["off_target"]) for r in sup),
        "unsupported_total": len(uns),
        "latency_ms_median": round(statistics.median(latencies), 1),
        "latency_ms_max": round(max(latencies), 1),
        "n_supported": len(sup),
        "n_paraphrase": len(para),
    }


def sweep(index: SemanticIndex, cases: list[dict]) -> None:
    print("\nBest semantic distance per question (no threshold applied):")
    supported, unsupported = [], []
    for case in cases:
        hits = sorted(index.search(case["question"], n=6, max_distance=2.0, kind="catalog")
                      + index.search(case["question"], n=12, max_distance=2.0, kind="document"),
                      key=lambda h: h.distance)
        want = targets(case)
        if want:
            ids = [f"{h.resource_id}@p{h.page}" if h.kind == "document" else h.resource_id for h in hits]
            best = next((h.distance for h, i in zip(hits, ids) if i in want), None)
            supported.append(best)
            print(f"  supported   {best if best is None else round(best, 3)!s:>6}  {case['question']}")
        else:
            best = hits[0].distance if hits else None
            unsupported.append(best)
            print(f"  unsupported {round(best, 3)!s:>6}  {case['question']}")
    print("\nThreshold sweep (supported targets kept / unsupported questions still getting semantic hits):")
    for t in [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]:
        kept = sum(1 for d in supported if d is not None and d <= t)
        noisy = sum(1 for d in unsupported if d is not None and d <= t)
        print(f"  max_distance={t:.2f}: targets kept {kept}/{len(supported)}  unsupported with hits {noisy}/{len(unsupported)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sweep", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)

    settings = load_settings()
    resources = load_catalog(settings.catalog_path)
    chunks, _ = load_chunks(settings.index_path, resources, PROJECT_ROOT)
    keyword = KeywordRetriever(resources, chunks)
    index, status = SemanticIndex.open(settings.chroma_path, resources, chunks)
    if index is None:
        print(f"semantic index unavailable: {status}")
        return 1
    # Follow-up questions need their conversation; standalone retrieval metrics exclude them.
    cases = [c for c in json.loads(QUESTIONS.read_text(encoding="utf-8")) if not c.get("follow_up_of")]
    index.search("warm up", n=1)  # load the model before timing

    results = {
        "keyword": evaluate(HybridRetriever(keyword, None), cases),
        "hybrid": evaluate(HybridRetriever(keyword, index, max_distance=DEFAULT_MAX_DISTANCE,
                                          catalog_max_distance=CATALOG_MAX_DISTANCE), cases),
    }
    print(f"{'metric':32} {'keyword':>10} {'hybrid':>10}")
    for key in ["recall@1", "recall@3", "paraphrase_recall@3", "unsupported_with_evidence",
                "avg_evidence_items", "off_target_items_supported", "latency_ms_median", "latency_ms_max"]:
        k, h = results["keyword"][key], results["hybrid"][key]
        fmt = (lambda v: f"{v:.0%}") if "recall" in key else (lambda v: str(v))
        print(f"{key:32} {fmt(k):>10} {fmt(h):>10}")
    print(f"(supported={results['hybrid']['n_supported']}, paraphrased={results['hybrid']['n_paraphrase']}, "
          f"unsupported={results['hybrid']['unsupported_total']}, max_distance docs={DEFAULT_MAX_DISTANCE} "
          f"catalog={CATALOG_MAX_DISTANCE})")

    print("\nPer question (K=keyword, H=hybrid; R3 = target in top 3):")
    for k, h in zip(results["keyword"]["rows"], results["hybrid"]["rows"]):
        if k["supported"]:
            flag = "REGRESSION" if k["r3"] and not h["r3"] else ""
            print(f"  K:{'Y' if k['r3'] else '-'} H:{'Y' if h['r3'] else '-'} {flag:10} {k['question']}"
                  + (f"   off-target: {h['off_target']}" if h["off_target"] else ""))
        else:
            print(f"  K:{'ev' if k['evidence_returned'] else '--'} H:{'ev' if h['evidence_returned'] else '--'} "
                  f"(unsupported) {k['question']}   hybrid evidence: {h['catalog'] + h['documents']}")
    if args.sweep:
        sweep(index, cases)
    if args.json:
        args.json.write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
