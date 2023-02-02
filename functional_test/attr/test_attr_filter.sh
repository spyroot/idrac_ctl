#!/bin/bash
source ../cluster.env
python ../../idrac_ctl.py attr --deep --filter USBFront.1.Enable
