# Fleet Management And The Redfish Proxy

> Status: DESIGN / NOT IMPLEMENTED. The CLI works without this service.

If I have one server in front of me, I use `idrac_ctl` directly. If I need to drive a fleet, I want a
small Redfish proxy/controller that stores desired state, reads observed state, and reconciles the
two without giving every client a route to the BMC network.

## Why A Service

The design lesson from tools such as Ironic and baremetal-operator is to isolate the process that can
reach BMCs. This proxy would keep that process in Python so it can reuse `RedfishManager`,
`IDracManager`, `sensors`, `discovery`, firmware inventory reads, and the same vendor capability
profiles documented in [vendors.md](vendors.md).

Multi-vendor discovery/read already exists in the CLI. What is deferred here is vendor-aware desired
state reconciliation: deciding what to change, ordering the writes, tracking jobs, and reporting
drift across many servers.

## Target Shape

```text
clients / kubectl / CI
  -> redfish-proxy service
  -> desired + observed state store
  -> async reconcile workers using the current Redfish managers
  -> BMC management network
```

The proxy would be the only deployed component with BMC egress. A Kubernetes CRD adapter could come
later, but the first useful version can just be an API and a database.

## Target State Model

I would model the stored state close to a CRD because it keeps desired and observed fields explicit:

```yaml
spec:
  bmcAddress: redfish://10.0.0.5/redfish/v1/Systems/System.Embedded.1
  vendor: dell
  credentialsRef: secret-name
  desired:
    power: "On"
    bootOverride: "Pxe"
    bios: { SriovGlobalEnable: "Enabled" }
status:
  power: "On"
  health: "OK"
  lastReconciled: <timestamp>
  goodCredentials: true
  error: null
```

`credentialsRef` is the name of a Kubernetes Secret created by the operator or installer; the Secret
would hold `username` and `password` keys. The proxy would log only metadata such as whether
credentials worked.

The Dell-shaped `bmcAddress` above is only an example. A real proxy needs the same host-system
selection now in `IDracManager`: on a GB300, route host actions to `System_0`, not the HGX baseboard.

## Reconcile Rules

Redfish has no push stream for all state, so the controller would poll, compare observed state to the
desired spec, apply only the missing changes, and back off on transient errors. Successful writes
would update observed state after the BMC or job confirms the change.

## Target Profiles

A target profile such as `rt-low-latency` would expand to concrete BIOS attributes, boot settings,
and later firmware expectations. Profiles are easier for operators to reason about than one-off
attribute lists, but the proxy still has to turn them into ordered Redfish operations.

Firmware update remains future work in this repository. Current firmware support is inventory/read
only.

## Security Design

- BMC credentials live in a Kubernetes Secret referenced by name, never inline in the spec and never
  printed.
- NetworkPolicy would restrict egress to the BMC management CIDR; the proxy would be the only pod
  with that route.
- TLS verification can stay off on the BMC hop when the network is isolated, or be enabled with a
  trusted certificate chain.
- RBAC would be scoped to the proxy resources and the referenced Secrets only.

## Scope

- MVP: register a server, read observed state, set desired power and boot override, list servers, and
  reconcile one server at a time with SQLite or Postgres.
- Next: bounded concurrency, benchmark gates, and a simulator; see
  [scaling-and-benchmarks.md](scaling-and-benchmarks.md).
- Later: BIOS profile reconcile, firmware update flows, optional CRD facade, leader election, and
  deeper vendor-specific desired state.

Supermicro read/query behavior is already validated against a live GB300 fixture overlay. HPE is only
a classifier/profile placeholder until tested. The proxy would treat those as different maturity
levels.

## Testing Target

I would unit-test the reconcile loop with a mocked Redfish client for convergence, idempotence,
backoff, and secret redaction. The current opt-in emulator test in `tests/test_emulator_smoke.py`
covers a single generic Redfish server. A future fleet simulator would cover many synthetic servers,
latency, and transient failures.
