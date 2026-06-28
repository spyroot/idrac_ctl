# Fleet Management & The Redfish Proxy

The CLI manages one server at a time. The planned fleet path is an optional Redfish proxy/controller:
a service that holds desired and observed state for many servers and reconciles the two over Redfish.
This page is the design target, not a runnable component in the repository today.

When implemented, this component stays optional. The core CLI should not depend on it.

## Why A Service

Surveying the prior art — Metal3/baremetal-operator (BMC I/O isolated in Ironic), OpenStack
Ironic+sushy (stateless API + worker conductor), DMTF Redfish Aggregation, Tinkerbell Rufio — the
recurring lesson is: **isolate the privileged BMC-talking process** and model **desired vs observed**
state. The design keeps that BMC-talking process in Python so it can reuse `RedfishManager` and
`IDracManager` instead of growing a second Redfish client in a second language. A `kubectl`-native CRD
facade can come later as a thin adapter; it is not needed to start.

## Target Shape

```
clients / kubectl / CI
      │  REST (optionally Redfish-Aggregator-shaped)
      ▼
 redfish-proxy (FastAPI)            ← desired + observed state (DB)
   • server registry
   • async reconcile loop (per server)         reuses RedfishManager / IDracManager
   • the ONLY pod with a route to the BMC management network
      │  Redfish/HTTPS  (insecure ok, network-isolated)
      ▼
  iDRAC / generic Redfish / (later) iLO / Supermicro
```

## Target State Model

The internal model should be CRD-shaped even in the DB, so a Kubernetes CRD adapter is natural later.
It can borrow from BareMetalHost and the DMTF `AggregationSource` vocabulary:

```yaml
spec:                                   # desired
  bmcAddress: redfish://10.0.0.5/redfish/v1/Systems/System.Embedded.1
  vendor: dell                          # selects the manager subclass / capabilities
  credentialsRef: secret-name           # k8s Secret, keys: username / password
  desired:
    power: "On"
    bootOverride: "Pxe"
    firmware: { component: BIOS, version: "2.19.1" }
    bios: { SriovGlobalEnable: "Enabled", ProcCStates: "Disabled" }
    targetProfile: "rt-low-latency"     # a named spec (see below)
status:                                 # observed
  power: "On"
  observedBoot: "Hdd"
  health: "OK"
  firmware: { BIOS: "2.18.0" }
  hardware: { cpu, memGiB, nics[], storage[] }
  lastReconciled: <ts>
  observedGeneration: 7
  goodCredentials: true
  error: null
```

## Reconcile Rules

Standard external-system controller discipline: **level-triggered** (read current, converge to spec —
never trust an event), **idempotent**, store the device handle in `status`, **periodic resync**
(Redfish has no push, so poll on an interval), **back off** on transient errors, write
`observedGeneration` after success, use finalizers for clean teardown.

## Target Profiles

A "target spec" is a named, versioned profile (e.g. `rt-low-latency`) that expands to concrete
firmware versions + BIOS attributes + SR-IOV settings. The proxy would reconcile each server toward
its profile and report drift. Profiles are the unit users reason about; the proxy turns them into the
right ordered Redfish operations (some need a reboot/job, so ordering and job-tracking matter).

## Security Design

- BMC credentials in a Kubernetes **Secret** (`username`/`password`), referenced by name — never inline,
  never logged; record only "good-credentials" metadata in status.
- **NetworkPolicy** restricting egress to the BMC management CIDR; the proxy is the only pod with that
  route. Self-signed BMC certs ⇒ `insecure` on that hop, compensated by network isolation.
- Least-privilege RBAC scoped to the proxy's own resources and the referenced Secrets.

## Scope

- **MVP:** register server; `GET /servers/{id}` (observed); `PUT /servers/{id}/desired`
  (power + bootOverride); list; SQLite/Postgres; one reconcile loop; optional Deployment / Service /
  Secret / NetworkPolicy manifests. Concurrency for many servers and benchmarking come next — see
  [scaling-and-benchmarks.md](scaling-and-benchmarks.md).
- **Later:** firmware / BIOS / SR-IOV / target-profile desired-state; DMTF-Aggregator-shaped read API;
  optional CRD + kopf façade; multi-replica leader election; iLO / Supermicro vendor subclasses.

## Testing Target

The reconcile loop should be unit-tested with a mocked client (converges, idempotent, backs off,
redacts credentials) and integration-tested against the `sushy-emulator --fake` lane and the planned
multi-server fleet simulator. See [testing.md](testing.md) and
[scaling-and-benchmarks.md](scaling-and-benchmarks.md).
