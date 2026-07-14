from __future__ import annotations

import json
from pathlib import Path

import pytest

from security_chaos_engineer.benchmark import _percentile, benchmark, write_benchmark
from security_chaos_engineer.experiments import EXPERIMENTS
from security_chaos_engineer.loader import load_default_system, load_system
from security_chaos_engineer.models import TargetSystem
from security_chaos_engineer.reporting import (
    build_report,
    render_markdown,
    result_to_dict,
    write_report,
)
from security_chaos_engineer.runner import build_scorecard, run_all


def test_percentile_helper() -> None:
    assert _percentile([], 50) == 0.0
    assert _percentile([1.0, 2.0, 3.0], 50) == 2.0
    assert _percentile([5.0], 95) == 5.0


def test_benchmark_is_deterministic() -> None:
    result = benchmark(iterations=5)
    assert result.deterministic is True
    assert result.ground_truth_verified is True
    assert result.matched == result.experiments == 10
    assert result.detection_rate == 0.9
    assert result.resilience_rate == 0.6
    assert result.report_hash


def test_write_benchmark(tmp_path: Path) -> None:
    path = write_benchmark(tmp_path, benchmark(iterations=2))
    assert json.loads(path.read_text(encoding="utf-8"))["iterations"] == 2


def test_report_render(system: TargetSystem, tmp_path: Path) -> None:
    results = run_all(system, EXPERIMENTS)
    report = build_report(results, build_scorecard(EXPERIMENTS, results))
    markdown = render_markdown(report)
    assert "resilience scorecard" in markdown.lower()
    assert "Findings" in markdown

    paths = write_report(tmp_path, report)
    assert paths["json"].exists()
    assert paths["markdown"].exists()


def test_result_to_dict_shape(system: TargetSystem) -> None:
    results = run_all(system, EXPERIMENTS)
    payload = result_to_dict(results[0])
    assert set(payload) >= {"experiment", "verdict", "detected", "detections"}


def test_loader_from_file(tmp_path: Path) -> None:
    assert isinstance(load_default_system(), TargetSystem)
    path = tmp_path / "s.yaml"
    path.write_text("name: tiny\n", encoding="utf-8")
    assert load_system(path).name == "tiny"


def test_loader_rejects_non_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_system(bad)


def test_loader_rejects_oversize(tmp_path: Path) -> None:
    big = tmp_path / "big.yaml"
    big.write_text("name: " + "x" * 2_000_000, encoding="utf-8")
    with pytest.raises(ValueError, match="exceeds"):
        load_system(big)
