"""Local HTTP surface for running experiments and reading the scorecard.

The API is unauthenticated and meant for loopback and the dashboard. It exposes
the target system topology, the experiment catalogue, single-experiment runs, and
the aggregate resilience scorecard.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .experiments import EXPERIMENTS
from .loader import load_default_system
from .models import TargetSystem
from .reporting import build_report, result_to_dict, scorecard_to_dict
from .resources import web_dir
from .runner import build_scorecard, run_all, run_experiment


def create_app(system: TargetSystem | None = None) -> FastAPI:
    app = FastAPI(
        title="Security Chaos Engineer",
        version="0.2.0",
        description="Inject security faults and measure detection, response, and degradation.",
    )
    app.state.system = system or load_default_system()

    def target() -> TargetSystem:
        return app.state.system  # type: ignore[no-any-return]

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "system": target().name}

    @app.get("/system")
    def system_topology() -> dict[str, Any]:
        current = target()
        return {
            "name": current.name,
            "pipeline": current.pipeline.model_dump(),
            "components": [c.model_dump() for c in current.components],
            "controls": [c.model_dump() for c in current.controls],
        }

    @app.get("/experiments")
    def experiments() -> dict[str, Any]:
        return {
            "experiments": [
                {
                    "id": e.id,
                    "title": e.title,
                    "hypothesis": e.hypothesis,
                    "fault": e.fault.kind.value,
                    "component": e.fault.component,
                }
                for e in EXPERIMENTS
            ]
        }

    @app.post("/experiments/{experiment_id}/run")
    def run_named(experiment_id: str) -> dict[str, Any]:
        experiment = next((e for e in EXPERIMENTS if e.id == experiment_id), None)
        if experiment is None:
            raise HTTPException(status_code=404, detail="unknown experiment")
        result = run_experiment(target(), experiment)
        return result_to_dict(result)

    @app.get("/scorecard")
    def scorecard() -> dict[str, Any]:
        results = run_all(target(), EXPERIMENTS)
        card = build_scorecard(EXPERIMENTS, results)
        return build_report(results, card)

    @app.get("/report")
    def report() -> dict[str, Any]:
        results = run_all(target(), EXPERIMENTS)
        return {"scorecard": scorecard_to_dict(build_scorecard(EXPERIMENTS, results))}

    directory = web_dir()
    if directory.exists():
        app.mount("/", StaticFiles(directory=str(directory), html=True), name="web")

    return app
