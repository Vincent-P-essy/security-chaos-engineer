# Methodology

How the measured evidence is produced and what it does and does not cover.

## Ground truth

Each experiment declares `expect_detected` and `expect_verdict` — the outcome a
reviewer expects. That declaration is the ground truth, also exported to
`fixtures/ground-truth.json`, with a test asserting the two are identical so the
committed fixture cannot drift from the catalogue.

## Correctness

`chaos benchmark` runs every experiment and compares its measured detection and
verdict to the ground truth. `matched == experiments` and
`ground_truth_verified == true` mean every reviewed outcome reproduced. Because
the catalogue spans held, degraded, and violated verdicts across ten fault kinds,
a regression in the engine surfaces as a changed verdict.

## Determinism

The benchmark runs the catalogue `iterations` times and hashes the outcome map
each pass. `deterministic == true` means all passes produced a single identical
hash. The hash excludes timing.

## The scorecard is intentionally imperfect

The reference stack is configured so the scorecard reflects a realistic posture,
not a clean sweep:

- **detection rate 0.9** — one fault (`auth_latency`) has only a paper control;
- **resilience (held) rate 0.6** — three faults degrade: the audit store fails
  open, and both the SIEM outage and log saturation drop their detection alert;
- **alert loss rate ~0.21** — saturation costs real detections.

These are the findings a security chaos program is meant to surface. Reproduce:

```bash
uv run chaos scorecard
uv run chaos benchmark --iterations 200
```

## What this is not

The target system is a model. The engine injects nothing into a real service,
opens no connections, and runs no payloads. Detection latency is measured in
abstract ticks, not seconds. A production security chaos program additionally
needs authorization, change management, and blast-radius controls that this
prototype does not implement.
