# Reviewed reference run

`reference-run.json` is a committed benchmark over the synthetic target system,
produced by:

```bash
CHAOS_SOURCE_REVISION=reference CHAOS_SOURCE_TREE_STATE=clean-checkout \
  uv run chaos benchmark --iterations 200 --out benchmarks/reference
```

`inputs.sha256` pins the deterministic inputs. CI verifies them with
`sha256sum --check benchmarks/reference/inputs.sha256`, so any fixture change
that alters behaviour is reviewed alongside the ground truth.

## What the run establishes

- **Correctness.** All ten experiments reproduce their reviewed detection and
  verdict (`matched == experiments`, `ground_truth_verified == true`), checked
  against `fixtures/ground-truth.json` by a test.
- **Determinism.** Every pass produces a byte-identical outcome map, collapsed to
  one `report_hash` (`deterministic == true`).
- **Honest posture.** The reference stack is intentionally imperfect: detection
  rate 0.9, resilience (held) rate 0.6, with a blind spot, two alert-loss gaps,
  and one fail-open component surfaced as findings.

Latency is machine dependent and is not asserted in CI; only correctness,
determinism, and input integrity are.
