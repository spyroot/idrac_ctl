# Quick Start

Author: Mus <spyroot@gmail.com>

I start with one safe read. It proves the BMC address, credentials, TLS behavior, and the main
ComputerSystem path before I touch BIOS, boot order, power, storage, or firmware.

## Install

```bash
python -m pip install idrac_ctl
idrac_ctl --version
```

For development from a checkout:

```bash
conda env create -f environment.yml
conda activate idrac_ctl
```

## Connect

`idrac_main.py`, the CLI entrypoint, reads these variables when command-line connection flags are not
provided:

```bash
export IDRAC_IP=10.0.0.42
export IDRAC_USERNAME=root
export IDRAC_PASSWORD='your-password'
export IDRAC_PORT=443
```

Do not paste real BMC passwords into examples, tickets, shell history, screenshots, or git-tracked
files.

## First Safe Read

```bash
idrac_ctl system
```

A good response has a host id, name, and power state. If `jq` is installed, I usually check only the
fields I need:

```bash
idrac_ctl --nocolor system | jq '.data | {Id, Name, PowerState}'
```

## Next Reads

```bash
idrac_ctl manager
idrac_ctl chassis
idrac_ctl sensors
idrac_ctl firmware_inventory
idrac_ctl bios --filter ProcCStates,SysMemSize
idrac_ctl storage-list
idrac_ctl get_vm
idrac_ctl logs
```

After those work, use [Safe Operations](Safe-Operations.md) before running anything that changes the
host or BMC.
