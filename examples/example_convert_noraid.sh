# first get the list of controllers
python idrac_ctl.py storage-controllers

# we can get list of all drives under particular controller
python idrac_ctl.py storage-drives -c AHCI.Embedded.2-1 --filter Drives,Volumes

In output we see disk that already none raid.

# {
#        "disk_ids": {
#            "Disk.Direct.0-0:AHCI.Embedded.2-1": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.2-1/Drives/Disk.Direct.0-0:AHCI.Embedded.2-1",
#            "Disk.Direct.1-1:AHCI.Embedded.2-1": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.2-1/Drives/Disk.Direct.1-1:AHCI.Embedded.2-1"
#        }
#    },
#    {
#        "none_raid_disk_ids": [
#            "Disk.Direct.0-0:AHCI.Embedded.2-1",
#            "Disk.Direct.1-1:AHCI.Embedded.2-1"
#        ]
#    },
#    {
#        "raid_disk_ids": []
#    }

# convert to none raid.
python idrac_ctl.py storage-convert-noraid -c AHCI.Embedded.2-1
