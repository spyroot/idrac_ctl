# BIOS Profiles

Author: Mus <spyroot@gmail.com>

BIOS profiles make host tuning repeatable. I use them for low-latency work, Dell profile presets,
custom BIOS specs, and platform-specific Intel or AMD tuning.

## Safe Flow

```bash
idrac_ctl bios-registry --attr_name SysProfile
idrac_ctl bios-change --from_spec specs/realtime.opt.spec.json on-reset --show
idrac_ctl bios-change --from_spec specs/realtime.opt.spec.json on-reset --commit
idrac_ctl jobs
idrac_ctl bios --filter SysProfile,ProcCStates,MemFrequency
```

`bios-change` requires an apply mode: `on-reset`, `auto-boot`, or `maintenance`. `--show` previews the
payload and does not apply changes.

## Included Recipes

- `examples/example_low_latency_profile.sh` applies `specs/realtime.opt.spec.json`.
- `examples/example_dell_system_profile.sh` uses Dell `SysProfile` or `WorkloadProfile`.
- `examples/example_custom_profile.sh` creates a small JSON profile and applies it.
- `examples/example_bios_optimize_intel.sh` shows Intel performance and power knobs.
- `examples/example_bios_optimize_amd.sh` shows AMD NUMA and performance knobs.
- `examples/example_fast_boot.sh` turns off slow boot checks where the BIOS supports them.

## Practical Rule

Read the registry before applying a profile. Vendors and BIOS generations do not use identical
attribute names or allowed values. If an attribute is not in the registry, skip it until the platform
owner confirms the equivalent setting.
