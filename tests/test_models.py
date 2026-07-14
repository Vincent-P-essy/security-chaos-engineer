from __future__ import annotations

import pytest
from pydantic import ValidationError

from security_chaos_engineer.models import (
    Component,
    ControlKind,
    FaultKind,
    Finding,
    SecurityControl,
    Severity,
    TargetSystem,
)


def test_duplicate_component_ids_rejected() -> None:
    with pytest.raises(ValidationError):
        TargetSystem(components=(Component(id="a"), Component(id="a")))


def test_duplicate_control_ids_rejected() -> None:
    control = SecurityControl(id="c", covers=(FaultKind.CERT_REVOCATION,))
    with pytest.raises(ValidationError):
        TargetSystem(controls=(control, control))


def test_controls_for_filters_by_fault() -> None:
    system = TargetSystem(
        controls=(
            SecurityControl(id="a", covers=(FaultKind.CERT_REVOCATION,)),
            SecurityControl(id="b", covers=(FaultKind.SIEM_OUTAGE,)),
        )
    )
    matched = system.controls_for(FaultKind.CERT_REVOCATION)
    assert [c.id for c in matched] == ["a"]


def test_control_requires_coverage() -> None:
    with pytest.raises(ValidationError):
        SecurityControl(id="x", covers=())


def test_control_kind_enum() -> None:
    control = SecurityControl(
        id="p", kind=ControlKind.PREVENT, covers=(FaultKind.WAF_RULE_DISABLED,)
    )
    assert control.kind is ControlKind.PREVENT


def test_finding_severity() -> None:
    finding = Finding(experiment_id="e", severity=Severity.CRITICAL, summary="x")
    assert finding.severity is Severity.CRITICAL
