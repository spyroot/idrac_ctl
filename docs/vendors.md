# Vendors

When I talk to an iDRAC, one detail matters immediately: Dell accepts the common Redfish query
parameters, but only one query parameter per URI. That is why vendor facts live in capability
profiles instead of scattered conditionals.

Vendor packages live under [`idrac_ctl/vendors/<name>/`](../idrac_ctl/vendors/README.md). The generic
Redfish core never imports them; command and manager code can consult their profiles.

## Current Profiles

| Vendor | Status |
|---|---|
| Dell iDRAC | Primary target. The Dell profile enables query flags, records the one-query-parameter-per-URI rule, and marks recurring JobService scheduling and lifecycle SSE as supported. |
| Supermicro | Query-only profile validated read-only against a live GB300 BMC with Redfish 1.17.0. It uses standard Redfish paths such as `System_0`; query-parameter support and job scheduling stay false until verified. |
| HPE | Conservative placeholder profile until tested against iLO hardware or the HPE emulator. |
| Generic | Fallback for unknown vendors; keeps capability flags conservative. |

```python
from idrac_ctl.vendors import get_vendor

caps = get_vendor("dell")
if caps.one_query_param_per_uri:
    ...
```

`get_vendor()`, defined in `idrac_ctl/vendors/__init__.py`, returns the named profile or the generic
fallback.

## Runtime Discovery

`classify_vendor()`, defined in `idrac_ctl/discover/classifier.py`, detects `dell`, `hpe`,
`supermicro`, or `generic` from a ServiceRoot dict. It checks OEM keys first, then an OEM-prefixed
`@odata.type`, then manufacturer/vendor text.

`discovery`, the CLI command in `idrac_ctl/discovery/cmd_discovery.py`, is the runtime crawler. It
walks Redfish resources, writes response files, and records allowed methods. Use it carefully against
approved hardware; the default unit tests stay offline.

## Cross-Vendor Reads

`sensors`, defined in `idrac_ctl/sensors/cmd_sensors.py`, is the cleanest vendor-neutral command. It
walks Chassis -> Sensors by links and returns readings with units. `tests/test_sensors.py` proves it
against the Supermicro overlay, not a Dell-only path.

On multi-system hosts, `IDracManager` discovers all Systems and Managers and picks the host system by
looking for `Bios` or `Boot` links. That is what keeps a GB300 host (`System_0`) distinct from the
NVIDIA HGX baseboard member.

## Adding A Vendor

Start small:

1. Add `idrac_ctl/vendors/<name>/capabilities.py` with the conservative facts you have actually
   verified.
2. Add a fixture overlay under `tests/<vendor>_fixtures/` and use `redfish_mock_factory("<vendor>")`
   so tests exercise the same request path as the CLI.
3. Add generic-read tests first: ServiceRoot classification, system/manager discovery, sensors or
   inventory reads.
4. Add vendor-specific `cmd_*.py` modules only when a real command needs behavior the generic core
   cannot express.
5. If an emulator exists, wire an opt-in lane like `tests/test_emulator_smoke.py` does for
   `sushy-emulator --fake`.

The first useful vendor does not need command parity with Dell. It needs honest capabilities,
fixtures, and read-only proof.

## Migration

Dell command code still lives in `idrac_ctl/idrac_manager.py` and `idrac_ctl/delloem/`. Moving it
under `vendors/dell/` is planned as commands are split out.
