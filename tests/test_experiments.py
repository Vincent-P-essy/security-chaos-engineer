from __future__ import annotations

import json

from security_chaos_engineer.experiments import EXPERIMENTS, ground_truth
from security_chaos_engineer.models import TargetSystem
from security_chaos_engineer.resources import packaged_path
from security_chaos_engineer.runner import build_scorecard, run_all


def test_all_experiments_reproduce_ground_truth(system: TargetSystem) -> None:
    results = run_all(system, EXPERIMENTS)
    declared = ground_truth()
    for result in results:
        expected = declared[result.experiment_id]
        assert result.detected is expected["detected"]
        assert result.verdict.value == expected["verdict"]


def test_ground_truth_matches_committed_fixture() -> None:
    committed = json.loads(packaged_path("ground-truth.json").read_text(encoding="utf-8"))
    assert committed == ground_truth()


def test_reference_scorecard_shape(system: TargetSystem) -> None:
    results = run_all(system, EXPERIMENTS)
    scorecard = build_scorecard(EXPERIMENTS, results)
    assert scorecard.experiments == 10
    assert scorecard.detected == 9
    assert scorecard.held == 6
    assert scorecard.degraded == 3
    assert scorecard.violated == 1
    assert len(scorecard.findings) == 4
    assert scorecard.alert_loss_rate > 0
