#!/bin/bash

# export config
python idrac_ctl.py system-export -f last_config.json

# check no scheduled jobs
python idrac_ctl.py jobs --scheduled

# adjust something in last_config.json
# for example set MmioAbove4Gb to disabled if it enabled.
# now import
python idrac_ctl.py system-import --config last_config.json --shutdown_type Forced -r

# verify value
python idrac_ctl.py --no_extra --no_action bios --filter MmioAbove4Gb
