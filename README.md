# idrac_ctl
Standalone command line tool provide option to interact with Dell iDRAC 
via Redfish REST API.  It supports both asynchronous and synchronous options 
to interact with iDRAC.


# Overview
This tool provides an option to interact with Dell iDRAC via the command line and execute almost 
every workflow you can do via Web UI. The idrac_ctl, by default, outputs everything in JSON, 
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

Make sure you are using python >= 3.9
```bash
git clone https://github.com/spyroot/idrac_ctl.git
cd idrac_ctl
pip install -r requirements.txt
python idrac_ctl.py --help
```

Now I'm still trying to optimize the root menu for easy consumption. For now, all subcommands are in root, 
hence format idrac_ctl command optional_args

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
If you pass for the same command --deep flag, it will recursively walk for each action 
and collect a unified view.

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
Set BIOS boot in one shot. In this setting on reboot, we will boot from CD-ROM when installation is complete. 
BIOS will boot OS from the default location. i.e., whatever is first on the list.

```bash
python idrac_ctl.py boot_one_shot --device Cd
# note Cd is default anyway
# --uefi_target if we need indicate UEFI device id.
```

Now reboot a host.

```reboot
python idrac_ctl.py reboot --reset_type PowerCycle
python idrac_ctl.py reboot --reset_type GracefulRestart
```

Note in my example, we didn't use UEFI.   If you need to use UEFI.
First, get UEFI ids

```bash
python idrac_ctl.py boot_source
```

Each device has a UefiDevicePath key. You can pass this key to insert media action 
if you need to boot from UEFI.

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
}
```

Note 
```bash
idrac_ctl.py boot_one_shot --uefi_target
```

## Export/Import system configuration

The export config, by default, will create a task and wait for completion. So will see 
the status bar progress.  If we don't want to wait, we can pass --the async flag.  
In this setting, each request to iDRAC send asynchronously, and we don't want results 
for job completion.

```bash
python idrac_ctl.py system-export --filename system.json
python idrac_ctl.py system-import --config system.json
```

If we don't need to wait, we can pass --async. It will create a job, but it will not wait 
for a job to complete.

```bash
python idrac_ctl.py export --filename system.json
```

```bash
python idrac_ctl.py export --filename system.json --async
```

This command will output job_id that we can use with job --job_id to get a job status

```json 
{
    "job_id": "JID_745386566338"
}
```

You can later fetch a result of job.

```bash
python idrac_ctl.py  job --job_id JID_745386566338

```

## Example attaching ISO from CIFS share and using Dell OEM API.

Install Samba,  in my case I share /var/www/html/ which I also use for nginx

```bash
sudo apt install samba
systemctl status smbd --no-pager -l
sudo systemctl enable --now smbd
sudo ufw allow samba
sudo usermod -aG sambashare $USER
sudo systemctl start --now smbd

echo "[sambashare]
    comment = Samba on www
    path = /var/www/html/
    read only = no
    browsable = yes" >> /etc/samba/smb.conf

sudo systemctl restart smbd
```

Now we can mount.  Note in my case I use default username vmware and password 123456.

```bash
python idrac_ctl.py oem-attach --ip_addr $CIFS_SERVER --share_name sambashare --remote_image ubuntu-22.04.1-desktop-amd64.iso
```

Now we can check status.

```bash
python idrac_ctl.py oem-attach-status
{
    "DriversAttachStatus": "NotAttached",
    "ISOAttachStatus": "Attached"
}
```

```idrac_ctl.py oem-net-ios-status
python idrac_ctl.py oem-net-ios-status
{
    "HostAttachedStatus": "Attached",
    "HostBootedFromISO": "No",
    "IPAddr": "10.241.7.99",
    "ISOConnectionStatus": "ConnectionUp",
    "ImageName": "ubuntu-22.04.1-desktop-amd64.iso",
    "ShareName": "sambashare",
    "UserName": "vmware"
}
```

## Example changing BIOS values

First, obtain a list of all possible attributes and values that BIOS supports. 
Note many values we can't change. Keep attention to the read-only flag.

Also, note if a reboot is required or not.

```bash
python idrac_ctl.py bios-registry --attr_list
```

For example attribute PowerCycleRequest.

```bash
python idrac_ctl.py bios-registry --attr_name PowerCycleRequest
```

```json
[
    {
        "AttributeName": "PowerCycleRequest",
        "CurrentValue": null,
        "DisplayName": "Power Cycle Request",
        "DisplayOrder": 10008,
        "HelpText": "Specifies how the system reacts when system transitions to S5 state.  When set to None, the transition to S5 is normal.  When set to Full Power Cycle, the system will temporarily be forced into a lower power state, similar to removing and replacing AC.",
        "Hidden": false,
        "Immutable": false,
        "MenuPath": "./MiscSettingsRef",
        "ReadOnly": false,
        "ResetRequired": true,
        "Type": "Enumeration",
        "Value": [
            {
                "ValueDisplayName": "None",
                "ValueName": "None"
            },
            {
                "ValueDisplayName": "Full Power Cycle",
                "ValueName": "FullPowerCycle"
            }
        ],
        "WarningText": null,
        "WriteOnly": false
    }
]
```

We can also query for a BIOS attributes that we can change. 

Save result to a file and find value that you need change.

```bash
python idrac_ctl.py bios-registry --filter-read_only -f bios.json
```

In my case I disable Mem Test and enabled MmioAbove4Gb

```bash
python idrac_ctl.py bios-change  --attr_name MemTest,MmioAbove4Gb --attr_value Disabled,Enabled
```


Please use the  [GitHub issue] tracker (https://github.com/spyroot/idrac_ctl/issues) submit bugs or request features.

More example TBD.
