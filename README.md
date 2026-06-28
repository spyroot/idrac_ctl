# idrac_ctl

`idrac_ctl` is my command-line tool for talking to Dell iDRAC over Redfish. It gives you JSON-first
read and control commands for inventory, BIOS, boot, firmware, storage, virtual media, jobs, and
manager state.

If you have one server in front of you, start here. The deeper architecture, test, vendor, and command
reference material lives in [`docs/`](docs/).

## Install

From PyPI:

```bash
pip install idrac_ctl
```

For local development, use the checked-in conda environment:

```bash
git clone https://github.com/spyroot/idrac_ctl.git
cd idrac_ctl
conda env create -f environment.yml
conda activate idrac_ctl
```

## Connect To iDRAC

Set credentials once so you do not have to pass them on every command:

```bash
export IDRAC_IP=10.0.0.42
export IDRAC_USERNAME=root
export IDRAC_PASSWORD='your-password'
export IDRAC_PORT=443
```

If your lab uses the usual iDRAC self-signed certificate, add `--insecure` to commands.

## First Read-Only Command

Start with a safe read:

```bash
idrac_ctl --insecure system
```

Output is JSON by default. If you want plain JSON for piping:

```bash
idrac_ctl --insecure --nocolor system | jq '.data.PowerState'
```

## A Few Useful Reads

```bash
idrac_ctl --insecure manager
idrac_ctl --insecure chassis
idrac_ctl --insecure firmware_inventory
idrac_ctl --insecure bios --filter ProcCStates,SysMemSize
idrac_ctl --insecure storage-list
idrac_ctl --insecure get_vm
```

Before running a mutating operation, check the command help and use a non-production iDRAC:

```bash
idrac_ctl boot-one-shot --help
idrac_ctl reboot --help
idrac_ctl bios-change --help
```

## More Docs

- [Command reference](docs/commands.md) - all current subcommands and common workflows.
- [Testing](docs/testing.md) - offline mock tests, dual-mode tests, emulator tests, and live-test safety.
- [Architecture](docs/architecture.md) - Redfish core, iDRAC layer, command registration, and known debt.
- [Vendors](docs/vendors.md) - vendor capability profiles and how new vendors fit.
- [Fleet proxy design](docs/redfish-proxy.md) - planned service/controller shape for fleet management.
- [Scaling and benchmarks](docs/scaling-and-benchmarks.md) - planned concurrency engine and benchmark goals.
