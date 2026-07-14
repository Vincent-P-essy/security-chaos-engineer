# Security policy

Report vulnerabilities through GitHub private vulnerability reporting. Include
the affected commit, the system fixture, the experiment, the expected verdict,
the observed verdict, and a minimal reproduction.

This project runs a simulated target system. It injects no faults into any real
service, opens no network connections to third parties, and executes no attacker
payloads. The experiment engine is pure and deterministic, and its verdicts fail
safe: an experiment with no reliable detecting control is reported as a
`violated` blind spot rather than a silent pass.

The local API is unauthenticated and must be bound to loopback. It exposes the
target-system topology and runs experiments against the in-memory simulation
only; it cannot reach production infrastructure.

The committed system model, controls, and experiments are synthetic. Never point
this tool at a production environment or feed it real asset inventories in a
public fork; a real security chaos program requires change management,
authorization, and blast-radius controls this prototype does not implement.
