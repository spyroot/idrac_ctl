# Safe Operations

Author: Mus <spyroot@gmail.com>

I treat BMC work like production operations. First read the state, then preview the payload, then apply
with an explicit intent flag, then verify.

## The Pattern

1. Read the current state.
2. Preview the change with `--show` or `--dry_run` when the command supports it.
3. Apply only with an explicit flag such as `--confirm`, `--commit`, or `-r`.
4. Verify with a read-only command, job watch, or task watch.

## Power Reset

```bash
idrac_ctl system-reset --reset_type GracefulRestart --dry_run
idrac_ctl system-reset --reset_type GracefulRestart --confirm
idrac_ctl system
```

`system-reset`, defined in `idrac_ctl/compute/cmd_system_reset.py`, is guarded. A dry run previews the
action without resetting the host.

## BIOS Change

```bash
idrac_ctl bios --filter SysProfile,ProcCStates,MemFrequency
idrac_ctl bios-change --from_spec specs/realtime.opt.spec.json on-reset --show
idrac_ctl bios-change --from_spec specs/realtime.opt.spec.json on-reset --commit
idrac_ctl jobs
```

Use `-r` only when you are ready for the host reset.

## Firmware Update

```bash
idrac_ctl firmware-update --image_uri https://example.invalid/firmware.exe --dry_run
```

Only run the confirm path with an approved firmware image, a maintenance window, and a recovery plan:

```bash
idrac_ctl firmware-update --image_uri https://firmware.example/vendor/image.exe --confirm
```

## What I Avoid

- No passwords on argv.
- No raw credentials in git-tracked files.
- No destructive examples against production BMCs.
- No live Redfish canary unless the target is approved and the operation is read-only or guarded.
