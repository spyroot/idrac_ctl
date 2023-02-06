#!/bin/bash

# export config
idrac_ctl system-export -f last_config.json

# check no scheduled jobs
idrac_ctl jobs --scheduled

# adjust something in last_config.json
# for example set MmioAbove4Gb to disabled if it enabled.
# now import
idrac_ctl system-import --config last_config.json --shutdown_type Forced -r

# verify value
idrac_ctl --no_extra --no_action bios --filter MmioAbove4Gb
