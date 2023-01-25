# Example first we disable Memory Test and enable MmioAbove4Gb snd reboot a host
python idrac_ctl.py bios-registry --attr_name MemTest,MmioAbove4Gb
python idrac_ctl.py bios-change  --attr_name MemTest,MmioAbove4Gb --attr_value Disabled,Enabled on-reset -r
python idrac_ctl.py --no_extra --no_action bios --filter MmioAbove4Gb,MemTest
