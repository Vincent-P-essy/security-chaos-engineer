# Limitations

This is a portfolio-grade prototype. It demonstrates the *method* of security
chaos engineering — a reproducible experiment lifecycle that surfaces resilience
gaps — over a simulated system, not a production chaos platform.

- **Simulated target.** Components, controls, and the alert pipeline are a model.
  The engine injects no faults into real infrastructure and executes no
  attacker behaviour.
- **Abstract time.** Detection latency and horizons are counted in ticks, not
  seconds. The numbers order controls relative to one another; they are not SLAs.
- **Declared control behaviour.** Whether a control is `reliable` and whether a
  component `fails_closed` are inputs. The tool reveals the consequences of a
  posture you describe; it does not discover that posture from a live system.
- **Single-fault experiments.** Each experiment injects one fault. Compound or
  cascading failures across multiple components are not modelled.
- **No safety controls.** A real security chaos program needs authorization,
  change windows, blast-radius limits, and automated rollback of *real* faults.
  None of that applies here because nothing real is touched, but none of it is
  implemented either.
- **Alert model is a proxy.** Pipeline saturation is modelled as a capacity that
  a fault's alert pressure consumes. It captures the phenomenon of lost
  detections under load without modelling a specific queue or backend.
- **Local API.** Unauthenticated and for loopback only.

See the [methodology](METHODOLOGY.md) and [architecture](ARCHITECTURE.md) before
interpreting a scorecard.
