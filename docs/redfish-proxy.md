# Fleet management & the Redfish proxy

The CLI manages one server at a time. To manage a fleet — bring 1,000 servers to a target spec,
concurrently — there is an **optional** Kubernetes-deployable service: the Redfish proxy/controller.
It holds the desired and observed state of every server and reconciles the two over Redfish.

This component is optional. The core CLI never depends on it.

## Why a service (and why Python, not a Go operator)

Surveying the prior art — Metal3/baremetal-operator (BMC I/O isolated in Ironic), OpenStack
Ironic+sushy (stateless API + worker conductor), DMTF Redfish Aggregation, Tinkerbell Rufio — the
recurring lesson is: **isolate the privileged BMC-talking process** and model **desired vs observed**
state. We get both from a single Python service that **reuses `RedfishManager`/`IDracManager`**, so we
don't maintain a second Redfish client in a second language. A `kubectl`-native CRD façade can come
later as a thin adapter; it is not needed to start.

## Shape

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

## State model

CRD-shaped even in the DB, so a Kubernetes CRD adapter is free later. Borrowed from BareMetalHost +
the DMTF `AggregationSource` vocabulary:

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

## Reconcile rules

Standard external-system controller discipline: **level-triggered** (read current, converge to spec —
never trust an event), **idempotent**, store the device handle in `status`, **periodic resync**
(Redfish has no push, so poll on an interval), **back off** on transient errors, write
`observedGeneration` after success, use finalizers for clean teardown.

## Target profiles

A "target spec" is a named, versioned profile (e.g. `rt-low-latency`) that expands to concrete
firmware versions + BIOS attributes + SR-IOV settings. The proxy reconciles each server toward its
profile and reports drift. Profiles are the unit users reason about; the proxy turns them into the
right ordered Redfish operations (some need a reboot/job, so ordering and job-tracking matter).

## Security

- BMC credentials in a k8s **Secret** (`username`/`password`), referenced by name — never inline,
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

## Testing

The reconcile loop is unit-tested with a mocked client (converges, idempotent, backs off, redacts
credentials) and integration-tested against the `sushy-emulator --fake` lane and the multi-server
fleet simulator. See [testing.md](testing.md) and [scaling-and-benchmarks.md](scaling-and-benchmarks.md).
