# Command Reference

This page mirrors the current `idrac_ctl --help` command names. Use it as the stable reference and run
`idrac_ctl <command> --help` for the exact flags on your installed version.

Most examples assume you already exported:

```bash
export IDRAC_IP=10.0.0.42
export IDRAC_USERNAME=root
export IDRAC_PASSWORD='your-password'
```

Add `--insecure` when your iDRAC uses a self-signed certificate.

## Global Options

| Option | Purpose |
|---|---|
| `--idrac_ip`, `--idrac_username`, `--idrac_password`, `--idrac_port` | Connection values. Defaults come from `IDRAC_IP`, `IDRAC_USERNAME`, `IDRAC_PASSWORD`, and `IDRAC_PORT`. |
| `--insecure` | Disable TLS certificate verification for self-signed iDRAC certificates. |
| `--use_http` | Use HTTP instead of HTTPS. |
| `--nocolor` | Emit plain JSON for tools such as `jq`. |
| `-f`, `--filename` | Save command output where the command supports it. |
| `-d`, `--data_only` | Print only the command result data where supported. |
| `--no_extra`, `--no_action`, `--json_only`, `--no-stdout` | Control how JSON sections are printed. |

## Read-Only Starting Points

```bash
idrac_ctl --insecure system
idrac_ctl --insecure manager
idrac_ctl --insecure chassis
idrac_ctl --insecure firmware_inventory
idrac_ctl --insecure bios --filter ProcCStates,SysMemSize
idrac_ctl --insecure accounts --usernames
idrac_ctl --insecure storage-list
idrac_ctl --insecure get_vm
```

## Subcommands

| Command | Purpose |
|---|---|
| `account` | Query one account resource. |
| `account-svc` | Query AccountService. |
| `accounts` | Query account collection; use `--usernames` for just usernames. |
| `attr` | Query manager attributes. |
| `attr-clear-pending` | Clear pending attribute values. |
| `attr-update` | Update manager attributes. |
| `bios` | Query BIOS attributes; supports `--filter`, `--from_file`, `--attr_only`, and `--deep`. |
| `bios-change` | Stage BIOS configuration changes from `--from_spec`; apply mode is `on-reset`, `auto-boot`, or `maintenance`. |
| `bios-clear-pending` | Clear pending BIOS values. |
| `bios-pending` | Query pending BIOS values. |
| `bios-registry` | Query BIOS registry attributes, value choices, and writable attributes. |
| `boot` | Query boot source data. |
| `boot-one-shot` | Set one-time boot target; can optionally reboot or power on. |
| `boot-options` | Query boot options. |
| `boot-options-clear` | Clear pending boot option values. |
| `boot-pending` | Query pending boot source values. |
| `boot-settings` | Query boot settings and pending boot settings. |
| `boot-source` | Query a boot source, optionally with `--dev <device>`. |
| `boot-source-enable` | Enable or disable a boot source. |
| `boot-source-registry` | Query boot source registry data. |
| `boot-source-update` | Update boot source settings. |
| `boot-sources` | List boot source members. |
| `change-boot-order` | Change boot order and boot options. |
| `chassis` | Query chassis services. |
| `chassis-reset` | Change chassis power state. |
| `compute-query` | Query compute settings. |
| `current_boot` | Query current boot source details. |
| `dell-lc-svc` | Query Dell Lifecycle Controller service data. |
| `discovery` | Discover actions under Redfish resources. |
| `eject_vm` | Eject virtual media. |
| `firmware` | Query firmware view. |
| `firmware_inventory` | Query firmware inventory. |
| `get_vm` | Query virtual media. |
| `insert_vm` | Insert virtual media from a URI. |
| `job` | Query one job. |
| `job-apply` | Apply pending jobs. |
| `job-rm` | Delete one job. |
| `job-rm-all` | Delete all jobs. |
| `job-watch` | Watch a job. |
| `jobs` | Query job collection. |
| `jobs-dell-service` | Query Dell job service. |
| `jobs-service` | Query job service. |
| `manager` | Query manager view. |
| `manager-reboot` | Reboot the iDRAC manager. |
| `oem-actions` | Query supported Dell OEM OS deployment actions. |
| `oem-attach` | Attach network ISO with Dell OEM action. |
| `oem-attach-status` | Query Dell OEM attach status. |
| `oem-boot-netios` | Boot from network ISO with Dell OEM action. |
| `oem-detach` | Detach Dell OEM network ISO. |
| `oem-disconnect` | Disconnect Dell OEM network ISO. |
| `oem-net-ios-status` | Query network ISO status. |
| `oem-net-iso-task` | Query Dell OEM OS deployment task data. |
| `pci` | Query PCI device or function. |
| `privilege-registry` | Query privilege registry service. |
| `query` | Query an arbitrary Redfish resource path. |
| `raid` | Query RAID service data. |
| `reboot` | Reset the computer system. |
| `service-api-rs-status` | Query remote service API status. |
| `service-api-status` | Query service API status. |
| `storage-controllers` | Query storage controller information. |
| `storage-convert-noraid` | Convert RAID disk under a controller to non-RAID. |
| `storage-convert-raid` | Convert non-RAID disk under a controller to RAID. |
| `storage-drives` | Query storage drives. |
| `storage-get` | Query one storage controller with optional `--filter Drives,Volumes`. |
| `storage-list` | List storage devices. |
| `system` | Query ComputerSystem view. |
| `system-export` | Export system configuration. |
| `system-import` | Import system configuration. |
| `task-get` | Query one task. |
| `task-watch` | Watch task progress. |
| `tasks` | Query task collection. |
| `volume-get` | Query one volume from a storage device. |
| `volume-init` | Initialize a volume. |
| `volumes` | Query virtual disk data. |

## Common Read Workflows

### BIOS Checks

```bash
idrac_ctl --insecure bios --filter ProcCStates,SysMemSize
idrac_ctl --insecure bios --from_file bios_query.json
```

`bios_query.json` is a JSON array:

```json
[
  "ProcCStates",
  "SysMemSize"
]
```

### BIOS Registry

```bash
idrac_ctl --insecure bios-registry --attr_list
idrac_ctl --insecure bios-registry --attr_name PowerCycleRequest
idrac_ctl --insecure bios-registry --noreadonly -f bios-writable.json
```

### Storage

```bash
idrac_ctl --insecure storage-list
idrac_ctl --insecure storage-get --controller RAID.Integrated.1-1
idrac_ctl --insecure storage-get --controller RAID.Integrated.1-1 --filter Drives,Volumes
```

### Firmware And Jobs

```bash
idrac_ctl --insecure firmware_inventory
idrac_ctl --insecure jobs
idrac_ctl --insecure job --job_id JID_123456789012
```

## Mutating Workflows

These commands change real server state. Use a non-production iDRAC, read `--help`, and capture the
current state before changing anything.

### BIOS Change From A Spec

```bash
idrac_ctl --insecure bios-change --from_spec ./bios.spec.json on-reset --show
idrac_ctl --insecure bios-change --from_spec ./bios.spec.json on-reset --commit
```

Many BIOS changes remain pending until an apply job and host reset. Add `--reboot` only when you are
ready for the host reset:

```bash
idrac_ctl --insecure bios-change --from_spec ./bios.spec.json on-reset --commit --reboot
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
idrac_ctl --insecure get_vm
idrac_ctl --insecure eject_vm --device_id 1
idrac_ctl --insecure insert_vm --uri_path http://10.0.0.10/ubuntu.iso --device_id 1
idrac_ctl --insecure boot-one-shot --device Cd --reboot
```

For a UEFI target, first inspect boot sources and pass the exact target value:

```bash
idrac_ctl --insecure boot-source
idrac_ctl --insecure boot-one-shot --device UefiTarget --uefi_target '<uefi-device-path>' --reboot
```

### Power Reset

```bash
idrac_ctl --insecure reboot --reset_type GracefulRestart
idrac_ctl --insecure reboot --reset_type PowerCycle --wait
```

Allowed reset values include `On`, `ForceOff`, `ForceRestart`, `GracefulRestart`,
`GracefulShutdown`, `PushPowerButton`, `Nmi`, and `PowerCycle`.

### System Export And Import

```bash
idrac_ctl --insecure system-export --filename system.json
idrac_ctl --insecure system-export --filename system.json --async
idrac_ctl --insecure system-import --config system.json
```

`system-import` can reboot the host depending on the import options and iDRAC behavior; check
`idrac_ctl system-import --help` before using it.

### Dell OEM Network ISO

```bash
idrac_ctl --insecure oem-attach --ip_addr 10.0.0.10 --share_name sambashare \
  --remote_image ubuntu.iso \
  --remote_username "$CIFS_USERNAME" \
  --remote_password "$CIFS_PASSWORD"
idrac_ctl --insecure oem-attach-status
idrac_ctl --insecure oem-net-ios-status
idrac_ctl --insecure oem-detach
```

The OEM commands are Dell-specific and assume the remote share is already reachable from iDRAC.
