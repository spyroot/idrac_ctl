#!/bin/bash

idrac_ctl chassis --filter PowerState
idrac_ctl chassis-reset --reset_type On
sleep 10
python idrac_ctl.py chassis --filter PowerState
