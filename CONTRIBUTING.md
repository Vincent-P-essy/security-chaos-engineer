# Contributing

Every change to the experiment engine needs:

1. a positive test for a fault that is detected and absorbed (`held`);
2. a negative test for each failure mode you can produce (`degraded` via an
   ungraceful component or a saturated pipeline, `violated` via a missing or
   unreliable control);
3. a ground-truth review when any experiment's expected outcome changes, kept in
   sync with `fixtures/ground-truth.json` (a test enforces this).

The simulation must stay pure and deterministic: identical inputs must yield an
identical verdict and a single stable benchmark hash. Do not add randomness, a
language model, or wall-clock dependence.

Verdicts must fail safe. A fault with no reliable detecting control is a blind
spot and must report `violated`, never a silent `held`.

Run before submitting:

```bash
uv sync --frozen --all-extras
make lint
make test
make benchmark
sha256sum --check benchmarks/reference/inputs.sha256
docker compose config --quiet
docker build -t security-chaos-engineer:test .
```

Do not commit real asset inventories, credentials, or generated co-author
trailers. Keep resilience claims tied to reproducible experiment evidence.
