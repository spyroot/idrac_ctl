# idrac_ctl Wiki

Author: Mus <spyroot@gmail.com>

`idrac_ctl` is my Redfish command-line toolkit for BMC operations. I use it when I want JSON-first
inventory, safe BIOS changes, boot control, storage views, virtual media, logs, sensors, and BMC
telemetry without opening the vendor web UI.

Start here:

- [Quick Start](Quick-Start.md) gets a new shell connected and runs the first safe read.
- [Vendor Support](Vendor-Support.md) explains what is proven for Dell, Supermicro, HPE, and generic
  Redfish targets.
- [Safe Operations](Safe-Operations.md) shows the read, preview, apply, verify rhythm I use before
  changing hardware.
- [BIOS Profiles](BIOS-Profiles.md) ties the low-latency, Dell System Profile, custom, Intel, and AMD
  examples together.
- [Telemetry Exporter](Telemetry-Exporter.md) covers the Prometheus and SignalFx BMC telemetry path.
- [Examples](Examples.md) maps the shell recipes under `examples/`.
- [Troubleshooting](Troubleshooting.md) lists the first checks when a BMC, command, or test run fails.

The README stays short on purpose. This wiki is the operator handbook.
