"""Serialize experiment results and the resilience scorecard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ExperimentResult, Scorecard


def result_to_dict(result: ExperimentResult) -> dict[str, Any]:
    return {
        "experiment": result.experiment_id,
        "fault": result.fault.value,
        "detected": result.detected,
        "time_to_detect_ticks": result.time_to_detect_ticks,
        "verdict": result.verdict.value,
        "hypothesis_held": result.hypothesis_held,
        "alerts_emitted": result.alerts_emitted,
        "alerts_delivered": result.alerts_delivered,
        "alerts_lost": result.alerts_lost,
        "blast_radius": list(result.blast_radius),
        "reasons": list(result.reasons),
        "detections": [
            {
                "control": d.control_id,
                "kind": d.kind.value,
                "at_tick": d.at_tick,
                "alerted": d.alerted,
                "alert_delivered": d.alert_delivered,
            }
            for d in result.detections
        ],
    }


def scorecard_to_dict(scorecard: Scorecard) -> dict[str, Any]:
    return {
        "experiments": scorecard.experiments,
        "detected": scorecard.detected,
        "held": scorecard.held,
        "degraded": scorecard.degraded,
        "violated": scorecard.violated,
        "detection_rate": scorecard.detection_rate,
        "resilience_rate": scorecard.resilience_rate,
        "mean_time_to_detect_ticks": scorecard.mean_time_to_detect_ticks,
        "alerts_emitted": scorecard.alerts_emitted,
        "alerts_lost": scorecard.alerts_lost,
        "alert_loss_rate": scorecard.alert_loss_rate,
        "findings": [
            {"experiment": f.experiment_id, "severity": f.severity.value, "summary": f.summary}
            for f in scorecard.findings
        ],
    }


def build_report(results: list[ExperimentResult], scorecard: Scorecard) -> dict[str, Any]:
    return {
        "scorecard": scorecard_to_dict(scorecard),
        "results": [result_to_dict(r) for r in results],
    }


def render_markdown(report: dict[str, Any]) -> str:
    card = report["scorecard"]
    lines = [
        "# Security chaos resilience scorecard",
        "",
        f"- Experiments: **{card['experiments']}**",
        f"- Detection rate: **{card['detection_rate'] * 100:.0f}%** "
        f"({card['detected']}/{card['experiments']})",
        f"- Resilience (held) rate: **{card['resilience_rate'] * 100:.0f}%** "
        f"({card['held']}/{card['experiments']})",
        f"- Mean time to detect: **{card['mean_time_to_detect_ticks']} ticks**",
        f"- Alert loss rate: **{card['alert_loss_rate'] * 100:.0f}%**",
        "",
        "| Experiment | Fault | Verdict | Detect (ticks) | Alerts lost |",
        "|---|---|---|---:|---:|",
    ]
    for result in report["results"]:
        ttd = result["time_to_detect_ticks"]
        lines.append(
            f"| {result['experiment']} | {result['fault']} | {result['verdict']} | "
            f"{ttd if ttd is not None else '-'} | {result['alerts_lost']} |"
        )
    if card["findings"]:
        lines += ["", "## Findings", ""]
        for finding in card["findings"]:
            lines.append(
                f"- **{finding['severity']}** {finding['experiment']}: {finding['summary']}"
            )
    return "\n".join(lines) + "\n"


def write_report(out_dir: Path, report: dict[str, Any]) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "scorecard.json"
    md_path = out_dir / "scorecard.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
