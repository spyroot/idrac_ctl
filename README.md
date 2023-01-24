# idrac_ctl
Dell iDRAC command line tool

# Overview
This tool provides an option to interact with Dell iDRAC via the command line and execute almost 
every workflow you can do via Web UI. The idract_ctl, by default, outputs everything in JSON, 
so you can easily pass it to any other tools to filter. Some commands provide an option to 
filter on action or specific fields, and s is still ongoing work. The tool developed in extendability 
mind. Each command registered dynamically. It sufficiently indicates the import statement 
in __init__ to load the custom command.
 
# Initial steps

Set the environment variable, so you don't need to pass each time.

```bash
export IDRAC_IP=MY_IP
export IDRAC_PASSWORD=MY_USERNAME
export IDRAC_USERNAME=root
```

Now I'm still trying to optimize the root menu for easy consumption. For now, all subcommands are in root, 
hence format idract_ctl command optional_args

List of subcommands.

```
subcommand:
                        system for subcommands
    job_del             delete a job
    clear_pending       reboots the system
    job                 fetch a job
    jobs                fetch list of jobs
    boot_source         fetch the boot source
    export              exports system configuration.
    bios                fetch the bios information
    attribute           fetch the attribute view
    boot                fetch the boot source
    firmware            fetch the firmware view
    firmware_inventory  fetch the firmware inventory view
    pci                 fetch the pci device or function
    reboot              reboots the system
    system              fetch the system view.
    raid                fetch the bios information
    set_boot_source     Fetch the boot source
    get_boot_source     fetch the boot source for device/devices
    storage             fetch the storage information
    task                exports system configuration.
    import              fetch the firmware view
    manager             fetch the attribute view
    get_virtual_media   fetch the virtual media
    insert_virtual_media
                        insert virtual media
    eject_virtual_media
                        eject the virtual media
    current_boot        fetch the boot source for device/devices
```

From a system we can view all compute system action and attributes.
```bash
python idrac_ctl.py system
```
trimmed output

```bash
{
    "@odata.context": "/redfish/v1/$metadata#ComputerSystem.ComputerSystem",
    "@odata.id": "/redfish/v1/Systems/System.Embedded.1",
    "@odata.type": "#ComputerSystem.v1_16_0.ComputerSystem",
    "Actions": {
        "#ComputerSystem.Reset": {
            "ResetType@Redfish.AllowableValues": [
                "On",
                "ForceOff",
                "ForceRestart",
                "GracefulRestart",
                "GracefulShutdown",
                "PushPowerButton",
                "Nmi",
                "PowerCycle"
            ],
            "target": "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
        }
    },
    "AssetTag": "",
    "Bios": {
        "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Bios"
    },
```
If you pass for a same command --deep flag it will recursively walk 
for each action and collect unified view.

More advanced example,  if we need boot one shot from ISO file from HTTP link.

First check what is attached and device id.
```bash
python idrac_ctl.py get_virtual_media
```

If you need eject
```bash
python idrac_ctl.py get_virtual_media
```

If you need inject virtual media
```bash
python idrac_ctl.py insert_virtual_media --uri_path http://10.241.7.99/ubuntu-22.04.1-desktop-amd64.iso --device_id 1
```

Confirm that virtiual media inserted
```bash
python idrac_ctl.py get_virtual_media
```

We see image attached

```json
[
        {
            "@odata.context": "/redfish/v1/$metadata#VirtualMedia.VirtualMedia",
            "@odata.id": "/redfish/v1/Systems/System.Embedded.1/VirtualMedia/1",
            "@odata.type": "#VirtualMedia.v1_4_0.VirtualMedia",
            "Actions": {
                "#VirtualMedia.EjectMedia": {
                    "target": "/redfish/v1/Systems/System.Embedded.1/VirtualMedia/1/Actions/VirtualMedia.EjectMedia"
                },
                "#VirtualMedia.InsertMedia": {
                    "target": "/redfish/v1/Systems/System.Embedded.1/VirtualMedia/1/Actions/VirtualMedia.InsertMedia"
                }
            },
            "ConnectedVia": "URI",
            "Description": "iDRAC Virtual Media Instance",
            "Id": "1",
            "Image": "http://10.241.7.99/ubuntu-22.04.1-desktop-amd64.iso",
            "ImageName": "ubuntu-22.04.1-desktop-amd64.iso",
            "Inserted": true,
            "MediaTypes": [
                "CD",
                "DVD",
                "USBStick"
            ],
            "MediaTypes@odata.count": 3,
            "Name": "VirtualMedia Instance 1",
            "Password": null,
            "TransferMethod": "Stream",
            "TransferProtocolType": "HTTP",
            "UserName": null,
            "WriteProtected": true
        }
]
```

Now reboot.

```reboot
python idrac_ctl.py reboot --reset_type PowerCycle
python idrac_ctl.py reboot --reset_type GracefulRestart
```

More example TBD.
