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

## More advanced example. 

Let say we need boot one shot from ISO file from HTTP link and start
unattended kickstart installation.

First, check if any virtual media is already attached and check the device id.
```bash
python idrac_ctl.py get_virtual_media
```

If you need to eject virtual media
```bash
python idrac_ctl.py eject_virtual_media --device_id 1
```

Now insert virtual media. If you fancy you can start local HTTP listener 
and pass your IP.
```bash
python idrac_ctl.py insert_virtual_media --uri_path http://10.241.7.99/ubuntu-22.04.1-desktop-amd64.iso --device_id 1
```

Confirm that virtual media inserted
```bash
python idrac_ctl.py get_virtual_media
```

We see image attached from get_virtual_media

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
Set BIOS boot in one shot. In this setting on reboot, we will boot from CDROM when installation is complete. 
BIOS will boot OS from the default location. i.e., whatever is first on the list.

```bash
python idrac_ctl.py boot_one_shot --device Cd
# note Cd is default anyway
# --uefi_target if we need indicate UEFI device id.
```

Now reboot.

```reboot
python idrac_ctl.py reboot --reset_type PowerCycle
python idrac_ctl.py reboot --reset_type GracefulRestart
```

Note in my example, we didn't use UEFI.   If you need use UEFI.
First get UEFI ids

```bash
python idrac_ctl.py boot_source
```

Each device has a UefiDevicePath key. This is basically a 
key you can pass to insert media action.

```json
{
            "@odata.context": "/redfish/v1/$metadata#BootOption.BootOption",
            "@odata.id": "/redfish/v1/Systems/System.Embedded.1/BootOptions/NIC.Slot.8-1",
            "@odata.type": "#BootOption.v1_0_4.BootOption",
            "BootOptionEnabled": true,
            "BootOptionReference": "NIC.Slot.8-1",
            "Description": "Current settings of the Legacy Boot option",
            "DisplayName": "NIC in Slot 8 Port 1: IBA ICE Slot D800 v2500",
            "Id": "NIC.Slot.8-1",
            "Name": "Legacy Boot option",
            "UefiDevicePath": "BBS(0x80,IBA ICE Slot D800 v2500)"
        },
```

Note 
```bash
idrac_ctl.py boot_one_shot --uefi_target
```

More example TBD.
