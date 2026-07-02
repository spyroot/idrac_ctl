# Speed up POST / boot: fast memory training + skip the full memory test
# Discover the exact attribute names on your box (they differ by vendor/CPU)
idrac_ctl bios-registry --attr_name MemFastTraining
idrac_ctl bios-registry --attr_name MemTest
# Enable fast memory training, disable the long memory test, apply on reset
idrac_ctl bios-change --attr_name MemFastTraining --attr_value Enabled on-reset
idrac_ctl bios-change --attr_name MemTest --attr_value Disabled on-reset -r
# Confirm after reboot
idrac_ctl bios --filter MemFastTraining
