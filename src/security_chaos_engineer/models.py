"""Typed domain model for security chaos experiments.

The vocabulary follows security chaos engineering: a *steady-state hypothesis*
is a measurable security property expected to hold, a *fault* is an adverse
condition injected on purpose, and an *experiment* verifies that the system's
security controls detect and absorb the fault before rolling it back. Every
model is frozen and rejects unknown fields.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

IDENTIFIER = r"^[a-z0-9][a-z0-9_.:-]{0,63}$"
MAX_COMPONENTS = 256
MAX_CONTROLS = 256
MAX_EXPERIMENTS = 512


class FaultKind(StrEnum):
    """A security fault an experiment can inject."""

    CERT_REVOCATION = "cert_revocation"
    TOKEN_EXPIRY = "token_expiry"  # noqa: S105 - fault kind name, not a secret
    RESPONSE_CORRUPTION = "response_corruption"
    AUTH_LATENCY = "auth_latency"
    SIEM_OUTAGE = "siem_outage"
    KEY_ROTATION = "key_rotation"
    AUDIT_DB_LOSS = "audit_db_loss"
    LOG_SATURATION = "log_saturation"
    WAF_RULE_DISABLED = "waf_rule_disabled"
    IAM_PRIVILEGE_ESCALATION = "iam_privilege_escalation"


class ControlKind(StrEnum):
    """What a security control does when it fires."""

    DETECT = "detect"
    PREVENT = "prevent"
    RESPOND = "respond"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Verdict(StrEnum):
    """Outcome of an experiment's steady-state hypothesis."""

    HELD = "held"
    DEGRADED = "degraded"
    VIOLATED = "violated"


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Component(Frozen):
    """A part of the target system that a fault can affect."""

    id: str = Field(pattern=IDENTIFIER)
    description: str = Field(default="", max_length=200)
    # Whether this component fails closed (safe) when its fault hits.
    fails_closed: bool = True


class SecurityControl(Frozen):
    """A detection, prevention, or response control installed in the system.

    ``detection_latency_ticks`` is how long the control takes to fire after a
    covered fault is injected. ``reliable`` set to ``False`` models a control
    that is present but does not actually fire (a paper control), which chaos is
    meant to expose.
    """

    id: str = Field(pattern=IDENTIFIER)
    kind: ControlKind = ControlKind.DETECT
    covers: tuple[FaultKind, ...] = Field(min_length=1, max_length=32)
    detection_latency_ticks: int = Field(default=1, ge=0, le=1000)
    reliable: bool = True
    emits_alert: bool = True
    description: str = Field(default="", max_length=200)


class AlertPipeline(Frozen):
    """Bounded alerting path. Saturation drops alerts (they are lost)."""

    capacity: int = Field(default=8, ge=0, le=100_000)
    description: str = Field(default="", max_length=200)


class TargetSystem(Frozen):
    """The system under experiment: components, controls, and alerting."""

    name: str = Field(default="reference-stack", max_length=80)
    components: tuple[Component, ...] = Field(default=(), max_length=MAX_COMPONENTS)
    controls: tuple[SecurityControl, ...] = Field(default=(), max_length=MAX_CONTROLS)
    pipeline: AlertPipeline = AlertPipeline()

    @model_validator(mode="after")
    def _unique_ids(self) -> TargetSystem:
        for label, ids in (
            ("component", [c.id for c in self.components]),
            ("control", [c.id for c in self.controls]),
        ):
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate {label} id")
        return self

    def controls_for(self, fault: FaultKind) -> tuple[SecurityControl, ...]:
        return tuple(control for control in self.controls if fault in control.covers)


class Fault(Frozen):
    """A concrete fault injection targeting a component."""

    kind: FaultKind
    component: str = Field(pattern=IDENTIFIER)
    severity: Severity = Severity.HIGH
    # Extra alert volume this fault generates while active (drives saturation).
    alert_pressure: int = Field(default=1, ge=0, le=100_000)


class Experiment(Frozen):
    """A steady-state hypothesis plus the fault that challenges it."""

    id: str = Field(pattern=IDENTIFIER)
    title: str = Field(max_length=120)
    hypothesis: str = Field(max_length=300)
    fault: Fault
    horizon_ticks: int = Field(default=30, ge=1, le=10_000)
    # Expected outcomes reviewed by hand; the benchmark verifies these.
    expect_detected: bool = True
    expect_verdict: Verdict = Verdict.HELD
    blast_radius: tuple[str, ...] = Field(default=(), max_length=MAX_COMPONENTS)


class Detection(Frozen):
    """A control firing at a given tick."""

    control_id: str
    kind: ControlKind
    at_tick: int = Field(ge=0)
    alerted: bool
    alert_delivered: bool


class ExperimentResult(Frozen):
    """The measured outcome of one experiment."""

    experiment_id: str
    fault: FaultKind
    detected: bool
    time_to_detect_ticks: int | None
    verdict: Verdict
    alerts_emitted: int
    alerts_delivered: int
    alerts_lost: int
    blast_radius: tuple[str, ...]
    detections: tuple[Detection, ...]
    hypothesis_held: bool
    reasons: tuple[str, ...] = ()


class Finding(Frozen):
    """A resilience gap surfaced by an experiment."""

    experiment_id: str
    severity: Severity
    summary: str = Field(max_length=200)


class Scorecard(Frozen):
    """Aggregate resilience posture across a set of experiments."""

    experiments: int
    detected: int
    held: int
    degraded: int
    violated: int
    mean_time_to_detect_ticks: float
    alerts_emitted: int
    alerts_lost: int
    findings: tuple[Finding, ...]

    @property
    def detection_rate(self) -> float:
        return round(self.detected / self.experiments, 4) if self.experiments else 0.0

    @property
    def resilience_rate(self) -> float:
        return round(self.held / self.experiments, 4) if self.experiments else 0.0

    @property
    def alert_loss_rate(self) -> float:
        return round(self.alerts_lost / self.alerts_emitted, 4) if self.alerts_emitted else 0.0
