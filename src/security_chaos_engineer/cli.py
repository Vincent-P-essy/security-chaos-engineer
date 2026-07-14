"""Command-line interface for the security chaos engineer."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import uvicorn

from .benchmark import benchmark, write_benchmark
from .experiments import EXPERIMENTS
from .loader import load_default_system, load_system
from .models import TargetSystem
from .reporting import build_report, result_to_dict, write_report
from .runner import build_scorecard, run_all, run_experiment


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="chaos", description="Security chaos engineering")
    root.add_argument("--system", type=Path, help="path to a target-system YAML file")
    commands = root.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="run one experiment or all of them")
    run.add_argument("experiment", nargs="?", default="all")

    commands.add_parser("scorecard", help="run all experiments and print the scorecard")

    report = commands.add_parser("report", help="run all experiments and write a report")
    report.add_argument("--out", type=Path, default=Path("reports"))

    run_benchmark = commands.add_parser("benchmark", help="measure the experiment catalogue")
    run_benchmark.add_argument("--iterations", type=int, default=100)
    run_benchmark.add_argument("--out", type=Path, default=Path("reports"))

    serve = commands.add_parser("serve", help="start the local API and dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)

    return root


def _system(args: argparse.Namespace) -> TargetSystem:
    return load_system(args.system) if args.system else load_default_system()


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)

    if args.command == "run":
        system = _system(args)
        if args.experiment == "all":
            results = run_all(system, EXPERIMENTS)
            _print([result_to_dict(r) for r in results])
            return 0
        experiment = next((e for e in EXPERIMENTS if e.id == args.experiment), None)
        if experiment is None:
            print(f"unknown experiment: {args.experiment}")
            return 2
        _print(result_to_dict(run_experiment(system, experiment)))
        return 0

    if args.command == "scorecard":
        system = _system(args)
        results = run_all(system, EXPERIMENTS)
        card = build_scorecard(EXPERIMENTS, results)
        _print(build_report(results, card)["scorecard"])
        return 0

    if args.command == "report":
        system = _system(args)
        results = run_all(system, EXPERIMENTS)
        card = build_scorecard(EXPERIMENTS, results)
        paths = write_report(args.out, build_report(results, card))
        _print({key: str(path) for key, path in paths.items()})
        return 0

    if args.command == "benchmark":
        measured = benchmark(iterations=args.iterations)
        path = write_benchmark(args.out, measured)
        _print({"benchmark": str(path), **asdict(measured)})
        return 0

    if args.command == "serve":
        uvicorn.run(
            "security_chaos_engineer.api:create_app",
            host=args.host,
            port=args.port,
            factory=True,
            log_level="info",
        )
        return 0

    return 2  # pragma: no cover - argparse requires a subcommand


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
