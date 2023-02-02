#!/bin/bash
IDRAC_REMOTE_HTTP="10.241.7.99"
python ../idrac_ctl.py eject_vm
# power down wait 20 sec and try to mount
python idrac_ctl.py chassis-reset --reset_type ForceOff
sleep 20
python ../idrac_ctl.py insert_vm --uri_path http://"$IDRAC_REMOTE_HTTP"/ph4-rt-refresh_adj.iso --device_id 1
