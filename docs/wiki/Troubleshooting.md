# Troubleshooting

Author: Mus <spyroot@gmail.com>

When a command fails, I start with the smallest safe read and work outward.

## Cannot Connect

Check the connection variables first:

```bash
env | grep '^IDRAC_'
idrac_ctl system
```

If TLS fails on a lab BMC, remember that certificate verification is off by default. Use `--verify-ssl`
only when the BMC has a trusted certificate chain.

## Command Works On Dell But Not Another Vendor

Start with standard Redfish reads:

```bash
idrac_ctl system
idrac_ctl manager
idrac_ctl chassis
idrac_ctl oem-info
```

Then check the vendor page. Dell has the deepest lifecycle control today; Supermicro GB300, HPE iLO,
and generic Redfish targets are strongest on read/query paths.

## BIOS Attribute Not Found

Read the registry before applying the profile:

```bash
idrac_ctl bios-registry --attr_name ProcCStates
```

If the attribute is missing, do not force the profile. Find the vendor-specific equivalent or leave
that setting out.

## Exporter Has No Fabric Metrics

Confirm the BMC exposes modern telemetry resources:

```bash
idrac_ctl metric-reports
idrac_ctl network-adapters
idrac_ctl nvlink-ports
idrac_ctl component-integrity
```

Some BMCs expose chassis sensors but not NVLink or IB counters. That is a platform capability gap,
not a Prometheus formatter problem.

## Tests Should Stay Offline

Default tests should not need live BMCs, real credentials, or network access:

```bash
pytest -q
```

Set `IDRAC_IP`, `IDRAC_USERNAME`, and `IDRAC_PASSWORD` only for approved live tests.
