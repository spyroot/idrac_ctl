# Vendor Support

Author: Mus <spyroot@gmail.com>

The Redfish core stays vendor-neutral. Vendor support is honest capability support, not a promise that
every vendor exposes the same lifecycle controls.

## Dell iDRAC

Dell is the primary control target. Proof lives in `tests/idrac_fixtures/`, Dell OEM command tests,
and the long-running iDRAC command set. Common ids are `System.Embedded.1` and `iDRAC.Embedded.1`.

Use Dell when you need the deepest coverage for lifecycle, jobs, virtual media, storage, and OEM OS
deployment flows.

## Supermicro GB300

Supermicro GB300 support is fixture-backed from a read-only Redfish 1.17 crawl under
`tests/supermicro_fixtures/`. Important ids include `System_0`, `HGX_Baseboard_0`, `BMC_0`, and
`HGX_BMC_0`.

The strongest surface today is read/query and telemetry: sensors, environment metrics, NVLink ports,
network adapters, component integrity, metric reports, and firmware inventory.

## HPE iLO

HPE support is proven for the standard read lane. Proof lives in `tests/hpe_fixtures/`, imported from
the HPE iLO emulator corpus, plus the read-only canary in `examples/hpe_ilo_canary.sh`.

The proven surface includes standard reads, Secure Boot reads, logs, network reads, telemetry reads,
and guarded dry-run reset paths. HPE OEM write flows are not a target yet.

## Generic DMTF

Generic support uses `tests/generic_fixtures/`, a DMTF-style Redfish tree. I treat this lane as the
portable fallback: standard system, manager, chassis, sensor, log, network, and inventory reads.

## Good Cross-Vendor Reads

```bash
idrac_ctl system
idrac_ctl chassis
idrac_ctl sensors
idrac_ctl network-adapters
idrac_ctl network-ports
idrac_ctl ethernet-interfaces
idrac_ctl metric-reports
idrac_ctl component-integrity
idrac_ctl secure-boot
idrac_ctl logs
idrac_ctl oem-info
```

If a non-Dell BMC behaves differently, start by checking what links it advertises in `idrac_ctl
system`, `idrac_ctl manager`, and `idrac_ctl chassis`.
