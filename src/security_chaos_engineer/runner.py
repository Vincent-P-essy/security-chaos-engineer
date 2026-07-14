"""The chaos experiment engine.

``run_experiment`` executes the security chaos lifecycle for a single
experiment: it establishes the steady state, injects the fault, ticks a virtual
clock while the system's controls react, accounts for alert delivery through a
bounded pipeline, forms a verdict, and rolls the fault back. The simulation is
pure and deterministic: identical inputs always produce the same result, so a
run can serve as reproducible evidence.

The verdict answers the steady-state hypothesis "the system detects this fault
and degrades safely without losing the alert":

* ``held`` - a reliable control detected the fault, its alert was delivered, and
  the affected component failed closed;
* ``degraded`` - detected, but the component failed open or the alert was lost
  to a saturated pipeline;
* ``violated`` - no reliable control detected the fault within the horizon.
"""

from __future__ import annotations

from .models import (
    Detection,
    Experiment,
    ExperimentResult,
    Finding,
    Scorecard,
    Severity,
    TargetSystem,
    Verdict,
)

_SEVERITY_RANK: dict[Severity, int] = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


def run_experiment(system: TargetSystem, experiment: Experiment) -> ExperimentResult:
    """Run one experiment against ``system`` and return its measured result."""

    fault = experiment.fault
    component = next((c for c in system.components if c.id == fault.component), None)
    graceful = component.fails_closed if component is not None else False

    capacity = system.pipeline.capacity
    emitted = 0
    delivered = 0
    lost = 0

    # The fault produces a burst of competing alert volume that occupies the
    # pipeline first; this is how log saturation can drown real detections.
    emitted += fault.alert_pressure
    noise_delivered = min(fault.alert_pressure, capacity)
    delivered += noise_delivered
    lost += fault.alert_pressure - noise_delivered
    remaining = capacity - noise_delivered

    firing = sorted(
        (
            control
            for control in system.controls_for(fault.kind)
            if control.reliable and control.detection_latency_ticks <= experiment.horizon_ticks
        ),
        key=lambda control: control.detection_latency_ticks,
    )

    detections: list[Detection] = []
    first_detect: int | None = None
    detecting_alert_ok = False
    for control in firing:
        alert_delivered = False
        if control.emits_alert:
            emitted += 1
            if remaining > 0:
                remaining -= 1
                delivered += 1
                alert_delivered = True
            else:
                lost += 1
        detections.append(
            Detection(
                control_id=control.id,
                kind=control.kind,
                at_tick=control.detection_latency_ticks,
                alerted=control.emits_alert,
                alert_delivered=alert_delivered,
            )
        )
        if first_detect is None:
            first_detect = control.detection_latency_ticks
            detecting_alert_ok = alert_delivered or not control.emits_alert

    detected = first_detect is not None
    verdict, reasons = _verdict(detected, graceful, detecting_alert_ok, first_detect)

    return ExperimentResult(
        experiment_id=experiment.id,
        fault=fault.kind,
        detected=detected,
        time_to_detect_ticks=first_detect,
        verdict=verdict,
        alerts_emitted=emitted,
        alerts_delivered=delivered,
        alerts_lost=lost,
        blast_radius=experiment.blast_radius,
        detections=tuple(detections),
        hypothesis_held=verdict is Verdict.HELD,
        reasons=reasons,
    )


def _verdict(
    detected: bool, graceful: bool, alert_ok: bool, first_detect: int | None
) -> tuple[Verdict, tuple[str, ...]]:
    if not detected:
        return Verdict.VIOLATED, ("no reliable control detected this fault within the horizon",)
    if graceful and alert_ok:
        return Verdict.HELD, (
            f"detected in {first_detect} tick(s); alert delivered; component failed closed",
        )
    reasons: list[str] = []
    if not graceful:
        reasons.append("component did not fail closed under the fault")
    if not alert_ok:
        reasons.append("detection alert was dropped by a saturated pipeline")
    return Verdict.DEGRADED, tuple(reasons)


def run_all(system: TargetSystem, experiments: tuple[Experiment, ...]) -> list[ExperimentResult]:
    return [run_experiment(system, experiment) for experiment in experiments]


def _finding(experiment: Experiment, result: ExperimentResult) -> Finding:
    base = _SEVERITY_RANK[experiment.fault.severity]
    if result.verdict is Verdict.VIOLATED:
        severity = list(_SEVERITY_RANK)[min(3, base + 1)]
        summary = f"blind spot: no control detected {result.fault.value}"
    else:  # degraded
        severity = experiment.fault.severity
        summary = "; ".join(result.reasons) or "degraded under fault"
    return Finding(experiment_id=experiment.id, severity=severity, summary=summary)


def build_scorecard(
    experiments: tuple[Experiment, ...], results: list[ExperimentResult]
) -> Scorecard:
    """Aggregate experiment results into a resilience scorecard with findings."""

    by_id = {experiment.id: experiment for experiment in experiments}
    detected = sum(1 for r in results if r.detected)
    held = sum(1 for r in results if r.verdict is Verdict.HELD)
    degraded = sum(1 for r in results if r.verdict is Verdict.DEGRADED)
    violated = sum(1 for r in results if r.verdict is Verdict.VIOLATED)
    detect_times = [r.time_to_detect_ticks for r in results if r.time_to_detect_ticks is not None]
    mttd = round(sum(detect_times) / len(detect_times), 4) if detect_times else 0.0
    findings = tuple(
        _finding(by_id[r.experiment_id], r)
        for r in results
        if r.verdict is not Verdict.HELD and r.experiment_id in by_id
    )
    return Scorecard(
        experiments=len(results),
        detected=detected,
        held=held,
        degraded=degraded,
        violated=violated,
        mean_time_to_detect_ticks=mttd,
        alerts_emitted=sum(r.alerts_emitted for r in results),
        alerts_lost=sum(r.alerts_lost for r in results),
        findings=findings,
    )
