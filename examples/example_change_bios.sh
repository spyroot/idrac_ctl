#!/usr/bin/env bash
set -euo pipefail

# Disable Memory Test and enable 4G MMIO, then verify after the host comes back.
idrac_ctl bios-registry --attr_name MemTest,MmioAbove4Gb
idrac_ctl bios-change \
  --attr_name MemTest,MmioAbove4Gb \
  --attr_value Disabled,Enabled \
  on-reset \
  --show
idrac_ctl bios-change \
  --attr_name MemTest,MmioAbove4Gb \
  --attr_value Disabled,Enabled \
  on-reset \
  -r
idrac_ctl --no_extra --no_action bios --filter MmioAbove4Gb,MemTest
