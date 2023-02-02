#!/bin/bash

cd ..
python idrac_ctl.py chassis --filter PowerState
python idrac_ctl.py chassis-reset --reset_type ForceOff
sleep 10
python idrac_ctl.py chassis --filter PowerState
