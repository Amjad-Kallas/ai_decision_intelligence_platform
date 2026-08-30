from __future__ import annotations

import time
from pathlib import Path

import yaml

from decisionos.agent.orchestrator import answer_question

QUESTIONS_PATH = Path(__file__).parent / "questions.yaml"

NEGATION_MARKERS = [
    "not present",
    "does not",
    "doesn't",
    "no evidence",
    "cannot determine",
    "no direct",
    "not appear",
    "not handle",
    "no mention",
]


def _evidence_matches(expected: list[str], evidence: list[dict]) -> bool:
    haystacks = [f"{c['node_id']} {c['file_path']}".lower() for c in evidence]
    return any(exp.lower() in h for exp in expected for h in haystacks)


def _keywords_match(expected: list[str], answer: str) -> bool:
    answer_lower = answer.lower()
    return all(kw.lower() in answer_lower for kw in expected)


def _no_answer_match(answer: str) -> bool:
    answer_lower = answer.lower()
    return any(marker in answer_lower for marker in NEGATION_MARKERS)


def run() -> None:
    questions = yaml.safe_load(QUESTIONS_PATH.read_text(encoding="utf-8"))

    results = []
    for q in questions:
        start = time.perf_counter()
        result = answer_question(q["question"])
        latency = time.perf_counter() - start

        checks: dict[str, bool] = {}
        if "expected_evidence" in q:
            checks["evidence"] = _evidence_matches(q["expected_evidence"], result["evidence"])
        if "expected_keywords" in q:
            checks["keywords"] = _keywords_match(q["expected_keywords"], result["answer"])
        if q.get("type") == "no_answer":
            checks["no_answer"] = _no_answer_match(result["answer"])

        passed = all(checks.values()) if checks else True
        results.append({"id": q["id"], "passed": passed, "checks": checks, "latency": latency, "answer": result["answer"]})

    print(f"{'ID':<24}{'RESULT':<8}{'LATENCY':<10}CHECKS")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"{r['id']:<24}{status:<8}{r['latency']:.1f}s     {r['checks']}")
        if not r["passed"]:
            print(f"    answer: {r['answer'][:200]}")

    passed_count = sum(1 for r in results if r["passed"])
    print(f"\n{passed_count}/{len(results)} passed")


if __name__ == "__main__":
    run()
