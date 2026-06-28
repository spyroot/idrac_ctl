# Vendors

The generic Redfish core stays product-neutral; anything specific to one server vendor lives in its own
package under [`idrac_ctl/vendors/<name>/`](../idrac_ctl/vendors/README.md). New vendors are added
incrementally without touching the core.

```
vendors/
  base.py        # VendorCapabilities model + registry
  dell/          # Dell iDRAC
  hpe/           # HPE iLO (placeholder)
  supermicro/    # Supermicro (placeholder)
```

## Capability profiles

Each vendor registers a `VendorCapabilities` profile declaring what its Redfish service supports, so
commands gate vendor-only behavior instead of guessing. An unknown vendor falls back to a conservative
`generic` profile.

```python
from idrac_ctl.vendors import get_vendor
caps = get_vendor("dell")            # unknown -> "generic"
if caps.job_scheduling:
    ...                              # only where supported
```

The Dell profile encodes documented iDRAC facts: all five query parameters honored but **one per
URI**; recurring JobService scheduling on a fixed set of URIs (ComputerSystem.Reset, Manager.Reset,
SEL ClearLog, Volume.CheckConsistency, …); lifecycle events over SSE.

## Adding a vendor

1. Create `vendors/<name>/` with `__init__.py`, `capabilities.py` (register a profile), `README.md`.
2. Add `cmd_*.py` modules (self-registering `IDracManager`/`RedfishManager` subclasses) for vendor
   specifics, with offline tests using the `redfish_api` fixture.
3. If an emulator exists for the vendor (e.g. HPE's iLO emulator), wire an opt-in test lane like the
   `sushy-emulator` one.

The core must never import a vendor package; vendor packages may depend on the core.

## Migration

Dell code currently also lives in `idrac_ctl/idrac_manager.py` and `idrac_ctl/delloem/`. It moves into
`vendors/dell/` incrementally, alongside the `idrac_ctl` → `redfish_ctl` rename.
