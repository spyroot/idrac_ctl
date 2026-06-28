# Scaling & Benchmarks

The target is to drive **~1,000 servers concurrently** to a spec and know — with numbers — that it is
fast, correct, and stable. This page is the design and acceptance target for the concurrency engine,
fleet simulator, and benchmark gates; those runnable artifacts are not in the repository yet.

## Concurrency Engine

A fleet operation (e.g. "apply profile `rt-low-latency` to these 1,000 servers") should fan out to
per-server async pipelines over a shared, bounded executor:

- **Async I/O** (`api_async_*` on the manager) so thousands of in-flight Redfish requests don't need
  thousands of threads.
- **Bounded concurrency** — a configurable cap on simultaneous servers / in-flight requests, with a
  queue, so we never overwhelm a BMC subnet or ourselves.
- **Per-server pipeline** — each server runs its own ordered steps (some need a reboot/job and must be
  awaited) independently; a slow or failing server never blocks the rest.
- **Rate limiting + backoff** — iDRAC gets sluggish under load (Dell's own docs warn about this), so
  we respect `Retry-After`, back off on transient 5xx/timeouts, and cap retries.
- **Idempotent + resumable** — re-running a fleet op converges only what's still off-spec; partial
  failures are reported per server, not as one opaque failure.

## Planned Fleet Simulator

We cannot test concurrency against real BMCs, and one `sushy-emulator` is a single server. The planned
answer is a **fleet simulator**: a local async Redfish service that presents **N synthetic servers**
with:

- realistic resource trees (reuse the captured fixtures + per-server identity),
- **injectable latency** (fixed / jittered / tail) to model a slow subnet,
- **injectable failures** (timeouts, 5xx, auth errors, BMC "busy") at a configurable rate,
- mutating Actions that change state (power, boot, BIOS apply, job creation) so reconcile is exercised
  end to end.

That would let CI run a 1,000-server fan-out deterministically on a laptop and let us benchmark
honestly. Where `sushy-emulator --fake` validates one generic server, the fleet simulator validates
scale and behavior under stress.

## What To Measure

For each fleet operation, benchmark against the simulator:

- **Throughput** — servers brought to spec per minute.
- **Latency** — p50 / p95 / p99 per-server completion and per-request.
- **Concurrency** — max in-flight, queue depth over time.
- **Error rate** — transient vs terminal; retries per server.
- **Correctness** — % converged to spec, drift detected, zero spurious mutations.
- **Resource use** — CPU / memory of the proxy at the target concurrency.

When implemented, results should land under `reports/` (for example,
`reports/bench-fleet-1000.json`) so regressions are visible. A benchmark is part of the definition of
done for the concurrency engine — not an afterthought.

## Acceptance Targets

- 1,000 simulated servers, read-and-report: completes well under a few minutes at a sane concurrency
  cap, p99 per-server within a small multiple of p50.
- Under 10% injected transient failures: ≥99% converge after bounded retries, no unbounded retry
  storms, no crash.
- Numbers reproducible in the Ubuntu container so Mac/Linux agree.
