#!/bin/bash
IDRAC_REMOTE_HTTP="10.241.7.99"
python ../idrac_ctl.py insert_vm --uri_path http://"$IDRAC_REMOTE_HTTP"/ph4-rt-refresh_adj.iso --device_id 1
