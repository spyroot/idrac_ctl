# idrac_ctl

`idrac_ctl` is my command-line tool for talking to Dell iDRAC over Redfish. It gives you JSON-first
read commands for inventory, BIOS, firmware inventory, storage, sensors, virtual media, jobs, and
manager state, plus control commands for boot, power, BIOS changes, virtual media, and Dell jobs.
Firmware update and flash commands are not implemented yet.

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

Set credentials once so you do not have to pass them on every command. The CLI reads these
environment variables in `idrac_main.py`:

```bash
export IDRAC_IP=10.0.0.42
export IDRAC_USERNAME=root
export IDRAC_PASSWORD='your-password'
export IDRAC_PORT=443
```

The tool skips TLS verification by default because BMCs usually ship self-signed certificates. Use
`--verify-ssl` only when the BMC has a certificate chain you trust; `--insecure` is just the explicit
form of the default.

## First Read-Only Command

Start with a safe read:

```bash
idrac_ctl system
```

Output is JSON by default. If you want plain JSON for piping:

```bash
idrac_ctl --nocolor system | jq '.data.PowerState'
```

## A Few Useful Reads

```bash
idrac_ctl manager
idrac_ctl chassis
idrac_ctl sensors
idrac_ctl firmware_inventory
idrac_ctl bios --filter ProcCStates,SysMemSize
idrac_ctl storage-list
idrac_ctl get_vm
```

`sensors`, defined in `idrac_ctl/sensors/cmd_sensors.py`, walks Chassis -> Sensors and returns
temperature, power, fan, and voltage readings with units. `discovery`, defined in
`idrac_ctl/discovery/cmd_discovery.py`, is the heavier crawl: it recursively walks Redfish resources
and records local response files plus what each resource exposes.

The current vendor work is honest about its boundaries. Dell is the main control target. Supermicro
read-only discovery/query behavior is validated against a GB300 BMC and covered by fixture overlays.
HPE is still a conservative placeholder profile. On multi-system hosts, the manager resolves the host
ComputerSystem instead of a baseboard, so a GB300-style `System_0` + `HGX_Baseboard_0` topology does
not silently route host commands to the wrong member.

Before running a mutating operation, check the command help and use a non-production iDRAC.
`boot-one-shot`, defined by the boot command module, sets a one-time boot device. `reboot`, defined
by the system reset command, power-cycles or resets the host. `bios-change`, defined by the BIOS
change command, stages BIOS attributes for an apply job.

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
