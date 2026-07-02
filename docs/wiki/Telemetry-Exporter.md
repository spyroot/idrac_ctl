# Telemetry Exporter

Author: Mus <spyroot@gmail.com>

`idrac_ctl exporter` turns BMC Redfish telemetry into Prometheus text or SignalFx datapoints. I use it
for hardware signals that in-band host software can miss: chassis power, fan speed, voltage, GPU
power, energy counters, and fabric health.

## What It Reads

- Chassis `EnvironmentMetrics`.
- Chassis `Sensors`.
- TelemetryService `MetricReports`.
- GPU and fabric resources such as NVLink ports and network adapters.
- Component integrity resources when the BMC exposes them.

The important GB300 differentiator is fabric telemetry: link state, negotiated speed, RX/TX bytes,
FEC/CRC-style counters when present, and NVLink error counters.

## Credentials

Use environment variables or a gitignored runtime file. Do not pass the BMC password on argv.

```bash
idrac_ctl exporter \
  --credential-file .internal/idrac_exporter.env \
  --vendor supermicro \
  --once \
  --output prometheus
```

## Prometheus

The default service exposes `/metrics`:

```bash
idrac_ctl exporter \
  --credential-file .internal/idrac_exporter.env \
  --vendor supermicro \
  --listen 0.0.0.0 \
  --port 9109
```

## Labels

Every series carries the join labels used by the GB300 dashboards:

- `host.name`
- `node`
- `server.address`
- `bmc.ip`
- `vendor`

For BMC `172.25.230.29`, the default slot math labels the host as `gb300-poc1-slot9` and the server
address as `172.25.230.49`.
