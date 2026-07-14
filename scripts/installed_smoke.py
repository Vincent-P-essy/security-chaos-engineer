"""Smoke-test the installed wheel from outside the source checkout."""

from __future__ import annotations

from security_chaos_engineer.experiments import EXPERIMENTS, ground_truth
from security_chaos_engineer.loader import load_default_system
from security_chaos_engineer.runner import build_scorecard, run_all


def main() -> int:
    system = load_default_system()
    results = run_all(system, EXPERIMENTS)
    declared = ground_truth()
    for result in results:
        expected = declared[result.experiment_id]
        if (
            result.detected is not expected["detected"]
            or result.verdict.value != expected["verdict"]
        ):
            print(f"mismatch on {result.experiment_id}")
            return 1
    scorecard = build_scorecard(EXPERIMENTS, results)
    print(
        f"ok: {scorecard.experiments} experiments, "
        f"{scorecard.held} held, {len(scorecard.findings)} findings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
