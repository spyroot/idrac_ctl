# Quick discovery of an unknown host - what is it and what does it expose
# Classify the vendor and walk the Redfish tree
idrac_ctl discovery
# System info: model, serial, firmware
idrac_ctl system
# Chassis: power, thermal, health
idrac_ctl chassis
# PCI devices to spot add-in cards (NICs, GPUs, HBAs)
idrac_ctl pci
# Storage controllers and attached drives
idrac_ctl storage-list
