#!/bin/bash
source ../device/device.env
python idrac_ctl.py chassis --filter PowerState
