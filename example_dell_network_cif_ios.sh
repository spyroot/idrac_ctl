# check if you have anything already attached.
python idrac_ctl.py oem-net-ios-status

#
python idrac_ctl.py oem-attach-status

# note if connected you need disconnect
python idrac_ctl.py oem-disconnect

#
python idrac_ctl.py oem-attach --ip_addr "$CIFS_SERVER" --share_name sambashare --remote_image ubuntu-22.04.1-desktop-amd64.iso

#
python idrac_ctl.py oem-net-ios-status

#{  Note HostBootedFromISO flag
#    "HostAttachedStatus": "Attached",
#    "HostBootedFromISO": "No",
#    "IPAddr": "x.x.x.x",
#    "ISOConnectionStatus": "ConnectionUp",
#    "ImageName": "ubuntu-22.04.1-desktop-amd64.iso",
#    "ShareName": "sambashare",
#    "UserName": "vmware"
#}

python idrac_ctl.py oem-boot-netios --ip_addr "$CIFS_SERVER" --share_name sambashare --remote_image ubuntu-22.04.1-desktop-amd64.iso

# we can get status
python idrac_ctl.py oem-net-iso-task

# task
python idrac_ctl.py oem-net-iso-task
#[
#    {
#        "@odata.context": "/redfish/v1/$metadata#Task.Task",
#        "@odata.id": "/redfish/v1/TaskService/Tasks/OSDeployment",
#        "@odata.type": "#Task.v1_5_1.Task",
#        "Description": "Server Configuration and other Tasks running on iDRAC are listed here",
#        "EndTime": "",
#        "Id": "OSDeployment",
#        "Messages": [
#            {
#                "Message": "The command was successful.",
#                "MessageArgs": [],
#                "MessageArgs@odata.count": 0,
#                "MessageId": "OSD1"
#            }
#        ],
#        "Messages@odata.count": 1,
#        "Name": "BootToNetworkISO",
#        "PercentComplete": null,
#        "TaskState": "Completed",
#        "TaskStatus": "OK"
#    },
#    null,
#    null
#]

# checking job finished
python idrac_ctl.py job -j JID_746727125416

#{
#    "@odata.context": "/redfish/v1/$metadata#DellJob.DellJob",
#    "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/Jobs/JID_746727125416",
#    "@odata.type": "#DellJob.v1_2_0.DellJob",
#    "ActualRunningStartTime": "2023-01-25T12:51:52",
#    "ActualRunningStopTime": "2023-01-25T12:58:13",
#    "CompletionTime": "2023-01-25T12:58:13",
#    "Description": "Job Instance",
#    "EndTime": null,
#    "Id": "JID_746727125416",
#    "JobState": "Completed",
#    "JobType": "OSDeploy",
#    "Message": "The command was successful.",
#    "MessageArgs": [],
#    "MessageArgs@odata.count": 0,
#    "MessageId": "OSD1",
#    "Name": "OSD: BootTONetworkISO",
#    "PercentComplete": 100,
#    "StartTime": "2023-01-25T12:51:52",
#    "TargetSettingsURI": null
#}