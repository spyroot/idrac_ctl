# Example one shoot boot from ISO
# First eject
idrac_ctl get_vm
idrac_ctl eject_vm --device_id 1
# confirm
idrac_ctl get_vm

# insert virtual media
idrac_ctl insert_vm --uri_path http://10.241.7.99/ubuntu-22.04.1-desktop-amd64.iso --device_id 1
# check
idrac_ctl get_vm

# adjust one shoot boot setting and reboot host.  it will boot from virtual media.
idrac_ctl boot-one-shot --device Cd -r
