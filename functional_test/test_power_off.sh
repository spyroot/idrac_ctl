#!/bin/bash

python idrac_ctl chassis --filter PowerState
python idrac_ctl chassis-reset --reset_type ForceOff
sleep 10
python idrac_ctl.py chassis --filter PowerState
