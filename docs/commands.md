# Command Reference

When I connect to a new BMC, I run `idrac_ctl system` first. It proves the endpoint, credentials, and
basic Redfish path before I ask for deeper inventory or stage any change.

The command names below are the registered CLI subcommands from the current tree. Run
`idrac_ctl <command> --help` for the exact flags on your installed version.

## Connection Basics

`idrac_main.py` reads these environment variables when you do not pass explicit connection flags:

```bash
export IDRAC_IP=10.0.0.42
export IDRAC_USERNAME=root
export IDRAC_PASSWORD='your-password'
export IDRAC_PORT=443
```

TLS verification is off by default because lab BMCs commonly use self-signed certificates.
`--verify-ssl`, defined by the root parser in `idrac_main.py`, opts into certificate verification
when you have a trusted chain. `--insecure` is the explicit force-skip form of the default.

Useful global options:

| Option | Purpose |
|---|---|
| `--idrac_ip`, `--idrac_username`, `--idrac_password`, `--idrac_port` | Connection values; each falls back to the matching `IDRAC_*` environment variable. |
| `--verify-ssl` | Verify the BMC TLS certificate instead of skipping verification. |
| `--insecure` | Explicitly skip TLS verification, matching the default. |
| `--use_http` | Use HTTP instead of HTTPS. |
| `--nocolor` | Emit plain JSON for tools such as `jq`. |
| `-f`, `--filename` | Save command output where the command supports it. |
| `-d`, `--data_only` | Print only the result data where supported. |
| `--no_extra`, `--no_action`, `--json_only`, `--no-stdout` | Control how JSON sections are printed. |

## Read-Only Starting Points

```bash
idrac_ctl system
idrac_ctl manager
idrac_ctl chassis
idrac_ctl sensors
idrac_ctl firmware_inventory
idrac_ctl bios --filter ProcCStates,SysMemSize
idrac_ctl accounts --usernames
idrac_ctl storage-list
idrac_ctl get_vm
```

`system` returns the host ComputerSystem. `manager` returns the BMC manager. `chassis` returns
chassis services. `sensors`, defined in `idrac_ctl/sensors/cmd_sensors.py`, walks Chassis -> Sensors
and returns readings with units. `firmware_inventory` reads installed firmware inventory; it does not
update firmware. `bios --filter` reads named BIOS attributes. `accounts --usernames` lists local
account names. `storage-list` and `get_vm` read storage and virtual-media state.

`discovery`, defined in `idrac_ctl/discovery/cmd_discovery.py`, recursively walks Redfish resources
and records response files plus allowed methods. The pure vendor classifier in
`idrac_ctl/discover/classifier.py` maps ServiceRoot data to `dell`, `hpe`, `supermicro`, or
`generic`.

On multi-system hosts such as a GB300, `IDracManager` resolves the host ComputerSystem by preferring
the member with `Bios` or `Boot` links, so commands target `System_0` instead of an HGX baseboard.
Supermicro is read/query validated from a live GB300 fixture overlay. HPE remains a conservative
placeholder profile.

## Subcommands

| Command | Purpose |
|---|---|
| `account` | Read one account resource. |
| `account-svc` | Read AccountService. |
| `accounts` | Read the account collection; `--usernames` prints only usernames. |
| `attr` | Read manager attributes. |
| `attr-clear-pending` | Clear pending manager attribute values. |
| `attr-update` | Stage manager attribute changes. |
| `bios` | Read BIOS attributes; common flags include `--filter`, `--from_file`, `--attr_only`, and `--deep`. |
| `bios-change` | Stage BIOS configuration changes from `--from_spec`; apply mode is `on-reset`, `auto-boot`, or `maintenance`. |
| `bios-clear-pending` | Clear pending BIOS values. |
| `bios-pending` | Read pending BIOS values. |
| `bios-registry` | Read BIOS registry metadata, choices, and writable attributes. |
| `boot` | Read boot source data. |
| `boot-one-shot` | Set a one-time boot target and optionally reboot or power on. |
| `boot-options` | Read boot option members. |
| `boot-options-clear` | Clear pending boot option values. |
| `boot-pending` | Read pending boot source values. |
| `boot-settings` | Read current and pending boot settings. |
| `boot-source` | Read a boot source, optionally with `--dev <device>`. |
| `boot-source-enable` | Enable or disable a boot option member. |
| `boot-source-registry` | Read boot source registry data. |
| `boot-source-update` | Stage boot source settings. |
| `boot-sources` | List boot source members. |
| `change-boot-order` | Change boot order and boot options. |
| `chassis` | Read chassis services. |
| `chassis-reset` | Change chassis power state. |
| `compute-query` | Read ComputerSystem settings. |
| `current_boot` | Read current boot source details. |
| `dell-lc-svc` | Read Dell Lifecycle Controller service data. |
| `discovery` | Recursively walk and dump Redfish resources, including exposed actions and allowed methods. |
| `eject_vm` | Eject virtual media. |
| `firmware` | Read firmware view data. |
| `firmware_inventory` | Read firmware inventory. |
| `get_vm` | Read virtual media. |
| `insert_vm` | Insert virtual media from a URI. |
| `job` | Read one Dell job. |
| `job-apply` | Apply pending jobs. |
| `job-rm` | Delete one job. |
| `job-rm-all` | Delete all jobs. |
| `job-watch` | Watch a job until it reaches a terminal state. |
| `jobs` | Read the job collection. |
| `jobs-dell-service` | Read Dell JobService. |
| `jobs-service` | Read standard Redfish JobService. |
| `manager` | Read manager data. |
| `manager-reboot` | Reboot the iDRAC manager. |
| `oem-actions` | Read supported Dell OEM OS deployment actions. |
| `oem-attach` | Attach a network ISO through the Dell OEM OS deployment action. |
| `oem-attach-status` | Read Dell OEM attach status. |
| `oem-boot-netios` | Boot from a network ISO through a Dell OEM action. |
| `oem-detach` | Detach Dell OEM network ISO media. |
| `oem-disconnect` | Disconnect Dell OEM network ISO media. |
| `oem-net-ios-status` | Read Dell OEM network ISO status. |
| `oem-net-iso-task` | Read Dell OEM OS deployment task data. |
| `pci` | Read PCI device or function data. |
| `privilege-registry` | Read the privilege registry. |
| `query` | Read an arbitrary Redfish resource path. |
| `raid` | Read RAID service data. |
| `reboot` | Reset the host ComputerSystem. |
| `sensors` | Read Chassis Sensor collections across vendors. |
| `service-api-rs-status` | Read remote service API status. |
| `service-api-status` | Read service API status. |
| `storage-controllers` | Read storage controller information. |
| `storage-convert-noraid` | Convert a RAID disk under a controller to non-RAID. |
| `storage-convert-raid` | Convert a non-RAID disk under a controller to RAID. |
| `storage-drives` | Read storage drive members. |
| `storage-get` | Read one storage controller with optional `--filter Drives,Volumes`. |
| `storage-list` | List storage devices. |
| `system` | Read ComputerSystem data. |
| `system-export` | Export system configuration. |
| `system-import` | Import system configuration. |
| `task-get` | Read one Redfish Task. |
| `task-watch` | Watch task progress. |
| `tasks` | Read the task collection. |
| `volume-get` | Read one volume from a storage device. |
| `volume-init` | Initialize a volume. |
| `volumes` | Read virtual disk data. |

## Common Read Workflows

### BIOS Checks

```bash
idrac_ctl bios --filter ProcCStates,SysMemSize
idrac_ctl bios --from_file bios_query.json
```

`bios_query.json`, created by you before the command runs, is a JSON array:

```json
[
  "ProcCStates",
  "SysMemSize"
]
```

### BIOS Registry

```bash
idrac_ctl bios-registry --attr_list
idrac_ctl bios-registry --attr_name PowerCycleRequest
idrac_ctl bios-registry --noreadonly -f bios-writable.json
```

### Storage

```bash
idrac_ctl storage-list
idrac_ctl storage-get --controller RAID.Integrated.1-1
idrac_ctl storage-get --controller RAID.Integrated.1-1 --filter Drives,Volumes
```

### Firmware, Sensors, And Jobs

```bash
idrac_ctl firmware_inventory
idrac_ctl sensors
idrac_ctl jobs
idrac_ctl job --job_id JID_123456789012
```

Firmware commands here are read-only inventory views. `sensors` is a useful cross-vendor smoke read.
`jobs` and `job` show pending or completed Redfish work.

## Mutating Workflows

These commands change real server state. Use a non-production BMC, read `--help`, and capture current
state before changing anything.

### BIOS Change From A Spec

```bash
idrac_ctl bios-change --from_spec ./bios.spec.json on-reset --show
idrac_ctl bios-change --from_spec ./bios.spec.json on-reset --commit
```

Many BIOS changes remain pending until an apply job and host reset. Add `--reboot` only when you are
ready for the host reset:

```bash
idrac_ctl bios-change --from_spec ./bios.spec.json on-reset --commit --reboot
```

Example spec:

```json
{
  "Attributes": {
    "MemFrequency": "MaxPerf",
    "MemTest": "Disabled",
    "OsWatchdogTimer": "Disabled",
    "ProcCStates": "Disabled",
    "SriovGlobalEnable": "Enabled"
  }
}
```

### Virtual Media ISO Boot

```bash
idrac_ctl get_vm
idrac_ctl eject_vm --device_id 1
idrac_ctl insert_vm --uri_path http://10.0.0.10/ubuntu.iso --device_id 1
idrac_ctl boot-one-shot --device Cd --reboot
```

For a UEFI target, first inspect boot sources and pass the exact target value:

```bash
idrac_ctl boot-source
idrac_ctl boot-one-shot --device UefiTarget --uefi_target '<uefi-device-path>' --reboot
```

### Power Reset

```bash
idrac_ctl reboot --reset_type GracefulRestart
idrac_ctl reboot --reset_type PowerCycle --wait
```

Allowed reset values include `On`, `ForceOff`, `ForceRestart`, `GracefulRestart`,
`GracefulShutdown`, `PushPowerButton`, `Nmi`, and `PowerCycle`.

### System Export And Import

```bash
idrac_ctl system-export --filename system.json
idrac_ctl system-export --filename system.json --async
idrac_ctl system-import --config system.json
```

`system-import` can reboot the host depending on the import options and iDRAC behavior; check
`idrac_ctl system-import --help` before using it.

### Dell OEM Network ISO

```bash
idrac_ctl oem-attach --ip_addr 10.0.0.10 --share_name sambashare \
  --remote_image ubuntu.iso \
  --remote_username "$CIFS_USERNAME" \
  --remote_password "$CIFS_PASSWORD"
idrac_ctl oem-attach-status
idrac_ctl oem-net-ios-status
idrac_ctl oem-detach
```

`oem-attach` tells iDRAC to mount an ISO from a network share. `oem-attach-status` and
`oem-net-ios-status` read Dell's OS deployment state. `oem-detach` tears down the mount. These Dell
OEM commands assume the remote share is reachable from the iDRAC management network.
