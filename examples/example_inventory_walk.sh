# Quick read-only inventory of a server I just racked - no changes
# The big picture: model, serial, firmware
idrac_ctl system
# Chassis health and power state
idrac_ctl chassis
# All PCIe devices (NICs, GPUs, HBAs)
idrac_ctl pci
# Storage controllers and their status
idrac_ctl storage-list
# Physical drives behind the controllers
idrac_ctl storage-drives
# What boot mode and device is set right now
idrac_ctl current_boot
