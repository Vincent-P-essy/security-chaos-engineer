from __future__ import annotations

from security_chaos_engineer.models import (
    AlertPipeline,
    Component,
    ControlKind,
    Experiment,
    Fault,
    FaultKind,
    SecurityControl,
    TargetSystem,
    Verdict,
)
from security_chaos_engineer.runner import build_scorecard, run_experiment


def make_system(
    *,
    fails_closed: bool = True,
    reliable: bool = True,
    emits_alert: bool = True,
    capacity: int = 8,
    with_control: bool = True,
) -> TargetSystem:
    controls: tuple[SecurityControl, ...] = ()
    if with_control:
        controls = (
            SecurityControl(
                id="probe",
                kind=ControlKind.DETECT,
                covers=(FaultKind.CERT_REVOCATION,),
                detection_latency_ticks=2,
                reliable=reliable,
                emits_alert=emits_alert,
            ),
        )
    return TargetSystem(
        name="unit",
        components=(Component(id="edge", fails_closed=fails_closed),),
        controls=controls,
        pipeline=AlertPipeline(capacity=capacity),
    )


def cert_fault(pressure: int = 1) -> Fault:
    return Fault(kind=FaultKind.CERT_REVOCATION, component="edge", alert_pressure=pressure)


def experiment(fault_pressure: int = 1, horizon: int = 30, **expect: object) -> Experiment:
    return Experiment(
        id="exp-unit",
        title="unit",
        hypothesis="unit",
        fault=cert_fault(fault_pressure),
        horizon_ticks=horizon,
        expect_detected=bool(expect.get("detected", True)),
        expect_verdict=expect.get("verdict", Verdict.HELD),  # type: ignore[arg-type]
    )


def test_held_when_detected_graceful_and_delivered() -> None:
    result = run_experiment(make_system(), experiment())
    assert result.verdict is Verdict.HELD
    assert result.detected is True
    assert result.time_to_detect_ticks == 2
    assert result.alerts_lost == 0
    assert result.hypothesis_held is True


def test_degraded_when_component_fails_open() -> None:
    result = run_experiment(make_system(fails_closed=False), experiment())
    assert result.verdict is Verdict.DEGRADED
    assert "fail closed" in " ".join(result.reasons)


def test_degraded_when_alert_lost_to_saturation() -> None:
    result = run_experiment(make_system(capacity=1), experiment(fault_pressure=5))
    assert result.verdict is Verdict.DEGRADED
    assert result.alerts_lost >= 1
    assert "saturated" in " ".join(result.reasons)


def test_violated_when_control_unreliable() -> None:
    result = run_experiment(
        make_system(reliable=False), experiment(detected=False, verdict=Verdict.VIOLATED)
    )
    assert result.verdict is Verdict.VIOLATED
    assert result.detected is False
    assert result.time_to_detect_ticks is None


def test_violated_when_no_control_covers_fault() -> None:
    result = run_experiment(make_system(with_control=False), experiment())
    assert result.verdict is Verdict.VIOLATED


def test_horizon_shorter_than_latency_misses_detection() -> None:
    result = run_experiment(make_system(), experiment(horizon=1))
    assert result.detected is False
    assert result.verdict is Verdict.VIOLATED


def test_silent_prevention_control_still_holds() -> None:
    result = run_experiment(make_system(emits_alert=False), experiment())
    # A control that prevents silently detects without needing a delivered alert.
    assert result.verdict is Verdict.HELD
    assert result.alerts_emitted == 1  # only the fault noise


def test_missing_component_is_not_graceful() -> None:
    exp = Experiment(
        id="exp-missing",
        title="missing",
        hypothesis="h",
        fault=cert_fault().model_copy(update={"component": "ghost"}),
    )
    result = run_experiment(make_system(), exp)
    assert result.verdict is Verdict.DEGRADED


def test_scorecard_aggregates_and_finds_gaps() -> None:
    system = make_system(fails_closed=False)
    exp = experiment(verdict=Verdict.DEGRADED)
    results = [run_experiment(system, exp)]
    scorecard = build_scorecard((exp,), results)
    assert scorecard.experiments == 1
    assert scorecard.degraded == 1
    assert scorecard.resilience_rate == 0.0
    assert len(scorecard.findings) == 1


def test_scorecard_severity_bumps_blind_spots() -> None:
    system = make_system(with_control=False)
    exp = experiment()
    scorecard = build_scorecard((exp,), [run_experiment(system, exp)])
    assert scorecard.violated == 1
    assert scorecard.findings[0].summary.startswith("blind spot")


def test_fault_kinds_are_exhaustive() -> None:
    # Every declared fault kind is a valid enum member (guards typos in fixtures).
    assert FaultKind.LOG_SATURATION in set(FaultKind)
