from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from security_chaos_engineer.api import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json()["status"] == "ok"


def test_system_topology(client: TestClient) -> None:
    system = client.get("/system").json()
    assert len(system["components"]) == 9
    assert len(system["controls"]) == 10


def test_experiments_listing(client: TestClient) -> None:
    assert len(client.get("/experiments").json()["experiments"]) == 10


def test_run_experiment(client: TestClient) -> None:
    result = client.post("/experiments/exp-cert-revocation/run").json()
    assert result["verdict"] == "held"

    degraded = client.post("/experiments/exp-audit-db-loss/run").json()
    assert degraded["verdict"] == "degraded"

    assert client.post("/experiments/does-not-exist/run").status_code == 404


def test_scorecard(client: TestClient) -> None:
    report = client.get("/scorecard").json()
    assert report["scorecard"]["experiments"] == 10
    assert report["scorecard"]["detection_rate"] == 0.9


def test_report_endpoint(client: TestClient) -> None:
    assert client.get("/report").json()["scorecard"]["held"] == 6


def test_dashboard(client: TestClient) -> None:
    assert client.get("/").status_code == 200
