#!/bin/bash
source ../cluster.env
python ../../idrac_ctl.py bios --filter SetBootOrderEn
