"""Shared resource

This is shared Enum, Classes used by idrac ctl.
Many classes mapped directly to JSON schem.

Author Mus spyroot@gmail.com

"""
import json
from enum import auto, Enum
from json import JSONEncoder
from typing import Optional

from .redfish_shared import RedfishApi
from .redfish_shared import RedfishJson
from .redfish_shared import RedfishJsonSpec


class ApiRequestType(Enum):
    """Each commands enum.
    """
    PrivilegeRegistry = auto()
    ComputeUpdate = auto()
    ComputeQuery = auto()
    ComputerSystemReset = auto()

    ConvertToRaid = auto()
    ConvertNoneRaid = ()
    Drives = auto()
    VolumeInit = auto()
    VolumeQuery = auto()
    ImportOneTimeBoot = auto()

    # dell oem
    DellOemTask = auto()
    DellLcQuery = auto()
    DellOemDisconnect = auto()

    RemoteServicesRssAPIStatus = auto()
    RemoteServicesAPIStatus = auto()
    TasksList = auto()

    ChangeBootOrder = auto()
    GetNetworkIsoAttachStatus = auto()
    OemAttach = auto()
    DellOemActions = auto()
    QueryIdrac = auto()

    BootOptions = auto()
    SystemConfigQuery = auto()
    IDracQuery = auto()

    # firmware
    FirmwareQuery = auto()
    FirmwareInventoryQuery = auto()
    PciDeviceQuery = auto()
    SystemQuery = auto()
    VirtualDiskQuery = auto()
    RaidServiceQuery = auto()
    StorageQuery = auto()
    Tasks = auto()
    GetTask = auto()
    ImportSystem = auto()

    # virtual media
    VirtualMediaGet = auto()
    VirtualMediaInsert = auto()
    VirtualMediaEject = auto()
    CurrentBoot = auto()

    # storage
    StorageViewQuery = auto()
    StorageListQuery = auto()

    #
    BootOptionQuery = auto()
    BootOptionsClearPending = auto()
    BootOptionsPending = auto()

    QueryBootOption = auto()
    BootOneShot = auto()
    BootSettingsQuery = auto()
    EnableBootOptions = auto()

    # boot sources
    BootSourcePending = auto()
    BootSourceUpdate = auto()
    BootSourceClear = auto()
    BootSourceRegistry = auto()
    BootQuery = auto()

    GetAttachStatus = auto()
    DellOemNetIsoBoot = ()
    DellOemDetach = auto()
    TaskGet = auto()

    # attribute
    AttributesQuery = auto()
    AttributesUpdate = auto()
    AttributeClearPending = auto()

    # idrac manager
    ManagerQuery = auto()
    ManagerReset = auto()

    # bios related
    BiosRegistry = auto()
    BiosChangeSettings = auto()
    BiosResetDefault = auto()
    BiosClearPending = auto()
    BiosQueryPending = auto()
    BiosQuery = auto()

    # query account
    QueryAccount = auto()
    QueryAccounts = auto()
    QueryAccountService = auto()

    ChassisQuery = auto()
    ChassisReset = auto()
    ChassisUpdate = auto()

    JobGet = auto()
    JobDel = auto()
    Jobs = auto()
    JobApply = auto()
    JobWatch = auto()
    JobServices = auto()

    #  dell services
    JobRmDellServices = auto()
    JobDellServices = auto()

    Discovery = auto()


class ScheduleJobType(Enum):
    """Each commands enum, based on redfish spec.
    """
    NoReboot = auto()
    AutoReboot = auto()
    OnReset = auto()
    Immediate = auto()


class RedfishActionEncoder(JSONEncoder):
    """JSON decoder used to serialize nested dicts.
    """

    def default(self, obj):
        return obj.__dict__


class RedfishAction:
    """Action discovery encapsulate each action to RedfishAction.
    """

    def __init__(self,
                 action_name: Optional[str] = "",
                 target: Optional[str] = "",
                 full_redfish_name: Optional[str] = ""):
        """Action discovered from json respond.
        """
        super().__init__()
        self.action_name = action_name
        self.full_redfish_name = full_redfish_name
        self.target = target
        self.args = None

    def __iter__(self):
        yield from {
            "action_name": self.action_name,
            "full_redfish_name": self.full_redfish_name,
            "target": self.target,
            "args": self.args,
        }.items()

    def add_action_arg(self, arg_name, allowable_value):
        """Add action argument name and allowable values for
        arguments for each args.
        :param arg_name: redfish action argument name
        :param allowable_value: redfish action argument allowable values
        :return:
        """
        if self.args is None:
            self.args = {}
        self.args[arg_name] = allowable_value

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def to_json(self):
        return json.dumps(dict(self), ensure_ascii=False)


class Singleton(type):
    """This idrac_ctl class for all action that singleton
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BootSource(Enum):
    """IDRAC Boot sources"""
    Pxe = "Pxe"
    Floppy = "Floppy"
    CD = "CD"
    Usb = "Usb"
    Hdd = "Hdd"
    Utilities = "Utilities"
    UefiTarget = "UefiTarget"
    BiosSetup = "BiosSetup"


class BiosSetup(Enum):
    """Bios apply once etc"""
    Once = "Once"
    Continuous = "Continuous"
    Disabled = "Disabled"


class ResetType(Enum):
    """Reset types"""
    On = "On"
    ForceOff = "ForceOff"
    GracefulRestart = "GracefulRestart"
    PushPowerButton = "PushPowerButton"
    NMI = "NMI"
    # redfish
    ForceOn = "ForceOn"
    ForceRestart = "ForceRestart"
    PowerCycle = "PowerCycle"


class PowerState(Enum):
    """ IDRAC chassis power state
    """
    On = "On"
    Off = "Off"
    # this not idrac respect in case of error
    Unknown = "Unknown"


class JobState(Enum):
    """IDRAC job states
    https://developer.dell.com/apis/2978/versions/4.xx/docs/101WhatsNew.md
    """
    New = "New"
    Scheduled = "Scheduled"
    Running = "Running"
    Completed = "Completed"
    CompletedWithErrors = "CompletedWithErrors"
    Downloaded = "Downloaded"
    Downloading = "Downloading"
    Scheduling = "Scheduling"
    Waiting = "Waiting"
    Failed = "Failed"
    RebootFailed = "RebootFailed"
    RebootCompleted = "RebootCompleted"
    RebootPending = "RebootPending"
    PendingActivation = "PendingActivation"
    Paused = "Paused"
    Unknown = "Unknown"


class CliJobTypes(Enum):
    """cli option for job types"""
    OsDeploy = "os"
    Bios_Config = "bios_config"
    FirmwareUpdate = "firmware_update"
    RebootNoForce = "reboot_no_force"


class IDRACJobType(Enum):
    """idrac job types
    """
    OSDeploy = "OSDeploy"
    Shutdown = "Shutdown"
    FirmwareUpdate = "FirmwareUpdate"
    RebootNoForce = "RebootNoForce"
    BIOSConfiguration = "BIOSConfiguration"
    FirmwareRollback = "FirmwareRollback"
    RepositoryUpdate = "RepositoryUpdate"
    RebootPowerCycle = "RebootPowerCycle"
    RAIDConfiguration = "RAIDConfiguration"
    NICConfiguration = "NICConfiguration"
    FCConfiguration = "FCConfiguration"
    iDRACConfiguration = "iDRACConfiguration"
    SystemInfoConfiguration = "SystemInfoConfiguration"
    InbandBIOSConfiguration = "InbandBIOSConfiguration"
    ExportConfiguration = "ExportConfiguration"
    ImportConfiguration = "ImportConfiguration"
    RemoteDiagnostics = "RemoteDiagnostics"
    LCLogExport = "LCLogExport"
    HardwareInventoryExport = "HardwareInventoryExport"
    FactoryConfigurationExport = "FactoryConfigurationExport"
    LicenseImport = "LicenseImport"
    LicenseExport = "LicenseExport"
    ThermalHistoryExport = "ThermalHistoryExport"
    LCConfig = "LCConfig",
    LCExport = "LCExport",
    SystemErase = "SystemErase"
    MessageRegistryExport = "MessageRegistryExport"
    UploadCustomDefaults = "UploadCustomDefaults"
    DPUConfig = "DPUConfig"
    ExportDeviceLog = "ExportDeviceLog"
    RealTimeNoRebootConfiguration = "RealTimeNoRebootConfiguration"
    Unknown = "Unknown"


class HTTPMethod(Enum):
    """Base HTTP methods."""
    GET = auto()
    POST = auto()
    PUSH = auto()
    PATCH = auto()
    DELETE = auto()


class RedfishChangePasswordReq:
    json = {
        "PasswordName": "Administrator | User",
        "OldPassword": "OldPasswordText",
        "NewPassword": "NewPasswordText"
    }


class Rest:
    pass


class RestMethodMapping:
    def __init__(self):
        """A generic api to map from a rest to supported HTTP method.
        """
        self._api_call = {}

    def add_api(self, a: Rest, method: HTTPMethod):
        self._api_call[a] = method

    def method(self, a):
        return self._api_call[a]


# ChassisCollection.ChassisCollection


class SupportedScheduledJobs(Enum):
    actions = {
        "ComputerSystem.Reset": ""
                                "Chassis.Reset"
    }


class RedfishSupermicro:
    """Mapping redfish rest to supermicro
    """
    Sessions = f"{RedfishApi.Version}/SessionService/Sessions"
    BiosAttributeRegistry = f"{RedfishApi.Version}/Registries/BiosAttributeRegistry.v1_0_0"
    FirmwareInventoryBackup = f"{RedfishApi.Version}/UpdateService/FirmwareInventory/Backup_BIOS"
    BMC_Backup = f"{RedfishApi.Version}/UpdateService/FirmwareInventory/Backup_BMC"


class IdracJobSvcActions(Enum):
    """Dell IDRAC job services actions."""

    # The CreateRebootJob action is used for creating a reboot job.
    CreateRebootJob = "CreateRebootJob"
    # method is used for deleting jobs from the JobQueue or the job store
    DeleteJobQueue = "DeleteJobQueue"

    SetupJobQueue = "SetupJobQueue"
    SetDeleteOnCompletionTimeout = "SetDeleteOnCompletionTimeout"


class IdracResetActions(Enum):
    """IDRAC Reset actions."""
    ComputerSystemReset = "ComputerSystem.Reset"
    ChassisReset = "Chassis.Reset"
    ManagerReset = "Manager.Reset"


class IDRAC_API:
    """
    Idrac api supported actions
    """
    IDRAC_MANAGER = RedfishApi.Managers
    IDRAC_DELL_MANAGERS = f"{RedfishApi.Version}/Dell/Managers"
    Tasks = f"{RedfishApi.Version}/TaskService/Tasks/"

    IDRAC_LLC = "/iDRAC.Embedded.1/DellLCService"
    BiosRegistry = "/Bios/BiosRegistry"

    Chassis = f"{RedfishApi.Version}/Chassis"

    Jobs = "/Jobs"
    JobService = "JobService"
    TaskService = "TaskService"
    EventService = "EventService"
    UpdateService = "UpdateService"
    TelemetryService = "TelemetryService"
    DellJobService = "DellJobService"
    AccountService = "AccountService"
    DellLCService = "DellLCService"

    JobServiceQuery = f"{RedfishApi.Version}/{JobService}"
    TaskServiceQuery = f"{RedfishApi.Version}/{TaskService}"
    EventServiceQuery = f"{RedfishApi.Version}/{EventService}"
    UpdateServiceQuery = f"{RedfishApi.Version}/{UpdateService}"
    AccountServiceQuery = f"{RedfishApi.Version}/{AccountService}"
    TelemetryServiceQuery = f"{RedfishApi.Version}/{TelemetryService}"

    Accounts = f"{RedfishApi.Version}/{AccountService}/Accounts"
    Account = f"{RedfishApi.Version}/{AccountService}/Accounts/"

    DellOemJobService = f"/Oem/Dell/{DellJobService}"
    DellOemJobServiceAction = f"/Oem/Dell/{DellJobService}/Actions/DellJobService."
    # "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/DellAttributes/System.Embedded.1"
    # "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/DellAttributes/System.Embedded.1"

    BootSourcesRegistryQuery = f"/{RedfishApi.BootSources}/{RedfishApi.BootSourcesRegistry}"

    # /redfish/v1/Registries/ManagerAttributeRegistry/ManagerAttributeRegistry.v1_0_0.json
    # /redfish/v1/AccountService/Roles/{RoleId}
    # The value of the Id property of the Role resource
    BiosSettings = RedfishApi.BiosSettings
    # COMPUTE_RESET = RedfishApi.ComputeReset
    # BIOS = RedfishApi.Bios
    BootOptions = "BootOptions"


# $select=SecurityCertificate.*

class IDRAC_JSON:
    """All Keys we expect idrac uses based on specification.
    """
    Id = "Id"
    # Describes the source of the payload.
    Data_id = "@odata.id"
    # odata type
    Data_type = "@odata.type"
    # Displays the total number of Members in the Resource Collection
    Data_count = "@odata.count"
    # Describes the source of the payload.
    Data_content = "@odata.context"
    # Indicates the "nextLink" when the payload contains partial results
    Data_next = "@odata.nextLink"

    Actions = "Actions"
    Members = "Members"
    Datatime = "DateTime"
    Location = "Location"
    IDracFirmwareVersion = "FirmwareVersion"
    Links = RedfishJsonSpec.Links
    Attributes = RedfishJson.Attributes
    RegistryEntries = "RegistryEntries"

    #
    DateTimeLocalOffset = "DateTimeLocalOffset"
    FirmwareVersion = "FirmwareVersion"
    ManagerServers = "ManagerForServers"
    ManageChassis = "ManagerForChassis"
    LastResetTime = "LastResetTime"
    TimezoneName = "TimeZoneName"
    UUID = "UUID"

    # Job states
    JobState = "JobState"
    TaskState = "TaskState"
    TaskStatus = "TaskStatus"
    PercentComplete = "PercentComplete"

    ApplyTime = "ApplyTime"
    RedfishSettingsApplyTime = "@Redfish.SettingsApplyTime"
    MaintenanceWindowStartTime = "MaintenanceWindowStartTime"
    MaintenanceWindowDuration = "MaintenanceWindowDurationInSeconds"

    # Accounts
    AccountId = "Id"
    Username = "UserName"
    AccountEnabled = "Enabled"
    AccountTypes = "AccountTypes"
    AccountTypesOem = "OEMAccountTypes"
    PasswordExpiration = "PasswordExpiration"
    PasswordChangeRequired = "PasswordChangeRequired"
    AccountRole = "Role"
    AccountRoleId = "RoleId"

    # Chassis
    Reset = "Reset"
    ResetType = "ResetType"

    # chassis schema
    PowerState = "PowerState"


class JobApplyTypes:
    """Job apply types"""
    InMaintenance = "InMaintenanceWindowOnReset"
    AtMaintenance = "AtMaintenanceWindowStart"
    OnReset = "OnReset"
    Immediate = "Immediate"


class IdracApiRespond(Enum):
    """We need report to a client either redfish created task and accepted
    or ok and success.  Note that some API has mismatch between
    200/204  hence it better differentiate each case
    """
    Ok = auto()
    Error = auto()
    Created = auto()
    Success = auto()
    AcceptedTaskGenerated = auto()


class ApiRespondString:
    """We need report to a client either redfish created task and accepted
    or ok and success.  Note that some API has mismatch between
    200/204  hence it better differentiate each case
    """
    Ok = "ok"
    Error = "error"
    Created = "created"
    Success = "success"
    AcceptedTaskGenerated = "accepted"


class BootSourceOverrideEnabled(Enum):
    """IDRAC boot source override modes
    """
    Disabled = "Disabled"
    Continuous = "Continuous"
    Once = "Once"


class BootSourceOverrideMode(Enum):
    """Boot source
    """
    UEFI = "UEFI"
    Legacy = "Legacy"


class MediaTypes(Enum):
    """IDRAC virtual media types
    """
    CD = "CD"
    DVD = "DVD"
    USBStick = "USBStick"


class DellBootSource:
    def __init__(self, device_id, name, enabled: Optional[bool] = True, index: Optional[int] = 1):
        """
        "Enabled": true,
        "Id": "BIOS.Setup.1-1#BootSeq#NIC.Slot.8-1#4f5d8523dbaffba918182fe3adb15032",
        "Index": 2,
        "Name": "NIC.Slot.8-1"

        :param device_id:
        :param name:
        :param index:
        :param enabled:
        """
        self._index = index
        self._name = name
        self._id = device_id
        self._enabled = enabled

    @property
    def Enabled(self) -> bool:
        """if the boot device is Enabled
        :return:
        """
        return self._enabled

    @property
    def Id(self) -> str:
        return self._id

    @property
    def Index(self) -> int:
        """The index number of the boot device in the  order list
        :return:
        """
        return self._index

    @property
    def Name(self) -> str:
        """The fully qualified device descriptor (FQDD) of the boot device
        :return:
        """
        return self._name


class IdracRequestHeaders:
    http_x_auth_token = "X-AUTH-TOKEN"
    xsrf_token = "XSRF-TOKEN"


class IdracRespondHeaders:
    http_allow = "Allow"
    http_www_authentication = "WWW-Authenticate"
    http_www_authentication_realm = "Basic realm=\"RedfishService\""


class IdracRebootJobTypes(Enum):
    """IdracRebootJobTypes is reboot job types for CreateRebootJobReq
    """
    GracefulRebootWithForcedShutdown = "GracefulRebootWithForcedShutdown"
    GracefulRebootWithoutForcedShutdown = "GracefulRebootWithoutForcedShutdown"
    PowerCycle = "PowerCycle"


class CreateRebootJobReq:
    def __init__(self, reboot_job_type: IdracRebootJobTypes, target: str, title: str):
        """The CreateRebootJob action is used for creating a reboot job.
        :param reboot_job_type: IdracRebootJobTypes:  a reboot job type IdracRebootJobTypes
        :param target: Link to invoke action
        :param title: name
        """
        self.CreateRebootJob = {
            "RebootJobType": reboot_job_type.value,
            "target": target,
            "title": title
        }


class TestNetworkShareReq:
    def __init__(self,
                 host="downloads.dell.com",
                 share_type="HTTPS",
                 proxy_support="Off",
                 ignore_cert_warning="On"):
        """
        This a default test network share request type for DellLCService.TestNetworkShare.

        :param host:
        :param share_type:
        :param proxy_support:
        :param ignore_cert_warning:
        """
        self.network_share_req = {
            "IPAddress": host,
            "ShareType": share_type,
            "ProxySupport": proxy_support,
            "IgnoreCertWarning": ignore_cert_warning
        }
        self._success = 200
        self._method = HTTPMethod.POST

    @property
    def success(self):
        return self._success

    @property
    def method(self):
        return self._method
