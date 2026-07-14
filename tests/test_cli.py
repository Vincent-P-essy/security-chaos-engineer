from __future__ import annotations

import json
from pathlib import Path

import pytest

from security_chaos_engineer.cli import main


def _capture(capsys: pytest.CaptureFixture[str]) -> object:
    return json.loads(capsys.readouterr().out)


def test_run_all(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "all"]) == 0
    assert len(_capture(capsys)) == 10


def test_run_named(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "exp-log-saturation"]) == 0
    assert _capture(capsys)["verdict"] == "degraded"


def test_run_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "nope"]) == 2


def test_scorecard(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scorecard"]) == 0
    card = _capture(capsys)
    assert card["violated"] == 1


def test_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["report", "--out", str(tmp_path)]) == 0
    assert Path(_capture(capsys)["json"]).exists()


def test_benchmark(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["benchmark", "--iterations", "2", "--out", str(tmp_path)]) == 0
    assert _capture(capsys)["deterministic"] is True
