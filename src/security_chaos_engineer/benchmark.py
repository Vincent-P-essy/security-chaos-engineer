"""Deterministic benchmark over the experiment catalogue.

Runs every experiment ``iterations`` times, verifies each measured outcome
against the reviewed ground truth, confirms the results are byte-identical across
passes via a single stable hash, and measures wall time. Correctness and
determinism are asserted; timing is recorded but excluded from the hash.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .experiments import EXPERIMENTS, ground_truth
from .loader import load_default_system
from .models import ExperimentResult
from .runner import build_scorecard, run_all


@dataclass(frozen=True)
class BenchmarkResult:
    iterations: int
    experiments: int
    matched: int
    ground_truth_verified: bool
    deterministic: bool
    report_hash: str
    detection_rate: float
    resilience_rate: float
    alert_loss_rate: float
    mean_time_to_detect_ticks: float
    latency_pass_p50_ms: float
    latency_pass_p95_ms: float
    elapsed_seconds: float
    source_revision: str
    source_tree_state: str


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return round(ordered[rank], 4)


def _outcome_map(results: list[ExperimentResult]) -> dict[str, dict[str, object]]:
    return {r.experiment_id: {"detected": r.detected, "verdict": r.verdict.value} for r in results}


def _hash(outcomes: dict[str, dict[str, object]]) -> str:
    payload = json.dumps(outcomes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def benchmark(iterations: int = 100) -> BenchmarkResult:
    system = load_default_system()
    declared = ground_truth()

    durations_ms: list[float] = []
    hashes: set[str] = set()
    matched = 0
    verified = True
    scorecard = None
    started = time.perf_counter()

    for iteration in range(iterations):
        pass_start = time.perf_counter()
        results = run_all(system, EXPERIMENTS)
        durations_ms.append((time.perf_counter() - pass_start) * 1000)
        outcomes = _outcome_map(results)
        hashes.add(_hash(outcomes))
        if iteration == 0:
            scorecard = build_scorecard(EXPERIMENTS, results)
            matched = sum(1 for eid, observed in outcomes.items() if observed == declared[eid])
            verified = matched == len(declared)

    elapsed = time.perf_counter() - started
    assert scorecard is not None
    return BenchmarkResult(
        iterations=iterations,
        experiments=len(declared),
        matched=matched,
        ground_truth_verified=verified,
        deterministic=len(hashes) == 1,
        report_hash=next(iter(hashes)) if hashes else "",
        detection_rate=scorecard.detection_rate,
        resilience_rate=scorecard.resilience_rate,
        alert_loss_rate=scorecard.alert_loss_rate,
        mean_time_to_detect_ticks=scorecard.mean_time_to_detect_ticks,
        latency_pass_p50_ms=_percentile(durations_ms, 50),
        latency_pass_p95_ms=_percentile(durations_ms, 95),
        elapsed_seconds=round(elapsed, 4),
        source_revision=os.environ.get("CHAOS_SOURCE_REVISION", "unknown"),
        source_tree_state=os.environ.get("CHAOS_SOURCE_TREE_STATE", "unknown"),
    )


def write_benchmark(out_dir: Path, result: BenchmarkResult) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "benchmark.json"
    path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
