# Architecture

`idrac_ctl` is built in layers so the generic Redfish work stays reusable and vendor specifics never
leak into the core. The direction is a generic `redfish_ctl` with vendors as plug-ins.

```
CLI (idrac_main.py, argparse)
   │  dispatch by ApiRequestType + name
   ▼
Command modules  (cmd_*.py, <domain>/cmd_*.py)      self-register via __init_subclass__
   │  inherit
   ▼
IDracManager          Dell/iDRAC OEM behavior  (idrac_manager.py, delloem/)
   │  inherit
   ▼
RedfishManager        product-neutral Redfish client  (redfish_manager.py)
   │
   ▼
requests  → Redfish / iDRAC over HTTPS
```

## Core seams

- **`RedfishManager`** — the generic client: connection (`ip`/`user`/`password`/`port`/`insecure`/
  `x_auth`), the HTTP verbs, response/message parsing (`redfish_respond.py`), and the
  `CommandResult(data, discovered, extra, error)` return contract. It must never import Dell code.
- **`IDracManager(RedfishManager)`** — Dell OEM specialization: task/job polling, Dell paths
  (`System.Embedded.1`, `iDRAC.Embedded.1`), `delloem/` actions.
- **Commands** — each is an `IDracManager` subclass declared with `scm_type=ApiRequestType.<X>`,
  `name=`, `metaclass=Singleton`. It implements `execute(**kwargs) -> CommandResult` and
  `register_subcommand()` for its CLI args. Registration is automatic, so adding a capability is
  adding a module — never editing a central switch.

## Vendors

Vendor specifics live under [`idrac_ctl/vendors/<name>/`](../idrac_ctl/vendors/README.md). Each vendor
package registers a `VendorCapabilities` profile (which query parameters the service honors, recurring
jobs, lifecycle events, OEM prefix) so commands can gate vendor-only behavior. The generic core picks
a conservative profile for unknown targets. See [vendors.md](vendors.md).

## Sync and async

Commands can run a request synchronously or against an asyncio loop (`api_async_*`). The async paths
matter most for the fleet proxy, where thousands of requests run concurrently — see
[scaling-and-benchmarks.md](scaling-and-benchmarks.md).

## Known structural debt (tracked)

- The repo root ships a re-export shim (`./__init__.py`) that complicates imports; it goes away with
  the `redfish_ctl` rename.
- `IDracManager` is large; transport/retry should move down into `RedfishManager`.
- Power/boot/BIOS/firmware should be callable as **library methods**, not only through the CLI
  arg-parser path, so the proxy and other callers reuse them directly.
