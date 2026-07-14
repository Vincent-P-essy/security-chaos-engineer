"""The reviewed experiment catalogue.

Each experiment injects one security fault and declares the outcome a human
reviewer expects: whether a control should detect it and what the steady-state
verdict should be. The engine's job is to reproduce these outcomes
deterministically; the benchmark fails if it does not. The catalogue is
deliberately mixed so the scorecard shows real gaps — a blind spot, an ungraceful
failure, and alert loss — rather than a clean sweep.
"""

from __future__ import annotations

from .models import Experiment, Fault, FaultKind, Severity, Verdict

EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment(
        id="exp-cert-revocation",
        title="Sudden TLS certificate revocation",
        hypothesis="The gateway detects revocation fast and refuses to serve on a dead cert.",
        fault=Fault(
            kind=FaultKind.CERT_REVOCATION, component="tls_gateway", severity=Severity.HIGH
        ),
        expect_detected=True,
        expect_verdict=Verdict.HELD,
        blast_radius=("tls_gateway",),
    ),
    Experiment(
        id="exp-token-expiry",
        title="Mass JWT expiry mid-session",
        hypothesis="Auth detects invalidated tokens and forces re-authentication.",
        fault=Fault(
            kind=FaultKind.TOKEN_EXPIRY, component="auth_service", severity=Severity.MEDIUM
        ),
        expect_detected=True,
        expect_verdict=Verdict.HELD,
        blast_radius=("auth_service",),
    ),
    Experiment(
        id="exp-response-corruption",
        title="Partial API response corruption",
        hypothesis="Integrity checks catch corrupted responses before they are trusted.",
        fault=Fault(
            kind=FaultKind.RESPONSE_CORRUPTION, component="api_backend", severity=Severity.HIGH
        ),
        expect_detected=True,
        expect_verdict=Verdict.HELD,
        blast_radius=("api_backend",),
    ),
    Experiment(
        id="exp-auth-latency",
        title="Latency injected into the auth service",
        hypothesis="The latency SLO alarm pages on slow authentication.",
        fault=Fault(
            kind=FaultKind.AUTH_LATENCY, component="auth_service", severity=Severity.MEDIUM
        ),
        expect_detected=False,
        expect_verdict=Verdict.VIOLATED,
        blast_radius=("auth_service", "api_backend"),
    ),
    Experiment(
        id="exp-siem-outage",
        title="SIEM unavailable for several minutes",
        hypothesis="A heartbeat detects SIEM loss and its alert still reaches an operator.",
        fault=Fault(
            kind=FaultKind.SIEM_OUTAGE, component="siem", severity=Severity.HIGH, alert_pressure=10
        ),
        expect_detected=True,
        expect_verdict=Verdict.DEGRADED,
        blast_radius=("siem",),
    ),
    Experiment(
        id="exp-key-rotation",
        title="Forced encryption key rotation",
        hypothesis="KMS monitoring detects unexpected rotation and services re-key cleanly.",
        fault=Fault(kind=FaultKind.KEY_ROTATION, component="kms", severity=Severity.MEDIUM),
        expect_detected=True,
        expect_verdict=Verdict.HELD,
        blast_radius=("kms",),
    ),
    Experiment(
        id="exp-audit-db-loss",
        title="Audit database connection lost",
        hypothesis="Losing the audit store detects and stops writes rather than failing open.",
        fault=Fault(kind=FaultKind.AUDIT_DB_LOSS, component="audit_db", severity=Severity.HIGH),
        expect_detected=True,
        expect_verdict=Verdict.DEGRADED,
        blast_radius=("audit_db",),
    ),
    Experiment(
        id="exp-log-saturation",
        title="Log pipeline saturation",
        hypothesis="A flood of logs is detected without losing the detections that matter.",
        fault=Fault(
            kind=FaultKind.LOG_SATURATION,
            component="log_pipeline",
            severity=Severity.MEDIUM,
            alert_pressure=12,
        ),
        expect_detected=True,
        expect_verdict=Verdict.DEGRADED,
        blast_radius=("log_pipeline", "siem"),
    ),
    Experiment(
        id="exp-waf-disabled",
        title="WAF rule silently disabled",
        hypothesis="Config drift detection catches a removed WAF rule.",
        fault=Fault(kind=FaultKind.WAF_RULE_DISABLED, component="waf", severity=Severity.HIGH),
        expect_detected=True,
        expect_verdict=Verdict.HELD,
        blast_radius=("waf",),
    ),
    Experiment(
        id="exp-iam-escalation",
        title="Unexpected IAM privilege escalation",
        hypothesis="The access analyzer flags an unexpected privilege grant quickly.",
        fault=Fault(
            kind=FaultKind.IAM_PRIVILEGE_ESCALATION, component="iam", severity=Severity.CRITICAL
        ),
        expect_detected=True,
        expect_verdict=Verdict.HELD,
        blast_radius=("iam",),
    ),
)


def ground_truth() -> dict[str, dict[str, object]]:
    """Return the declared expected outcome for every experiment."""

    return {
        experiment.id: {
            "detected": experiment.expect_detected,
            "verdict": experiment.expect_verdict.value,
        }
        for experiment in EXPERIMENTS
    }
