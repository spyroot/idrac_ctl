"""Shared resource
"""
import json
from enum import auto, Enum
from typing import Optional
from json import JSONEncoder


class ApiRequestType(Enum):
    """Each commands enum.
    """
    JobApply = auto()
    BiosQueryPending = auto()
    ConvertToRaid = auto()
    ConvertNoneRaid = ()
    Drives = auto()
    VolumeInit = auto()
    VolumeQuery = auto()
    ImportOneTimeBoot = auto()
    DellOemTask = auto()
    DellOemDisconnect = auto()
    RemoteServicesRssAPIStatus = auto()
    DellLcQuery = auto()
    RemoteServicesAPIStatus = auto()
    JobRmDellServices = auto()
    JobDellServices = auto()
    TasksList = auto()
    JobWatch = auto()
    BiosChangeSettings = auto()
    BiosRegistry = auto()
    ChangeBootOrder = auto()
    GetNetworkIsoAttachStatus = auto()
    OemAttach = auto()
    DellOemActions = auto()
    QueryIdrac = auto()
    JobDel = auto()
    AttributeClearPending = auto()
    JobGet = auto()
    Jobs = auto()
    BootOptions = auto()
    SystemConfigQuery = auto()
    BiosQuery = auto()
    IDracQuery = auto()
    AttributesQuery = auto()
    BootQuery = auto()
    FirmwareQuery = auto()
    FirmwareInventoryQuery = auto()
    PciDeviceQuery = auto()
    RebootHost = auto()
    SystemQuery = auto()
    VirtualDiskQuery = auto()
    RaidServiceQuery = auto()
    EnableBootOptions = auto()
    StorageQuery = auto()
    Tasks = auto()
    GetTask = auto()
    ImportSystem = auto()
    VirtualMediaGet = auto()
    VirtualMediaInsert = auto()
    VirtualMediaEject = auto()
    CurrentBoot = auto()
    BootOneShot = auto()
    StorageViewQuery = auto()
    StorageListQuery = auto()
    BiosClearPending = auto()
    BootOptionQuery = auto()
    BootSettingsQuery = auto()
    BootSourceClear = auto()
    JobServices = auto()
    ChassisQuery = auto()
    ChassisReset = auto()
    GetAttachStatus = auto()
    DellOemNetIsoBoot = ()
    DellOemDetach = auto()
    TaskGet = auto()

    # idrac manager
    ManagerQuery = auto()
    ManagerReset = auto()

    BiosResetDefault = auto()


class ScheduleJobType(Enum):
    """Each commands enum.
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
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

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


class PowerState(Enum):
    """ IDRAC chassis power state
    """
    On = "On"
    Off = "Off"


class JobState(Enum):
    """IDRAC job states"""
    Failed = "Failed"
    Running = "Running"
    Completed = "Completed"
    Scheduled = "Scheduled"
    RebootCompleted = "RebootCompleted"
    RebootPending = "RebootPending"


class JobTypes(Enum):
    """IDRAC job types"""
    BIOS_CONFIG = "bios_config"
    FIRMWARE_UPDATE = "firmware_update"
    REBOOT_NO_FORCE = "reboot_no_force"


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

class RedfishJson:
    Actions = "Actions"
    Links = "Links"
    Members = "Members"
    Datatime = "DateTime"
    Location = "Location"
    Attributes = "Attributes"
    RegistryEntries = "RegistryEntries"

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

    # This property is an array of references to the systems that this manager has control over.
    ManagerServers = "ManagerForServers"
    # This property is an array of references to the chassis that this manager has control over.
    ManagerForChassis = "ManagerForChassis"
    # Manager.Reset


class RedfishActions:
    BiosReset = "Bios.ResetBios"
    ManagerReset = "#Manager.Reset"
    ComputerSystemReset = "ComputerSystem.Reset"


class RedfishApi:
    Version = "/redfish/v1"
    Managers = f"{Version}/Managers"
    Systems = f"{Version}/Systems"
    Chassis =f"{Version}/Chassis"

    UpdateService = f"{Version}/UpdateService"
    UpdateServiceAction = f"{Version}/{UpdateService}/Actions/SimpleUpdate"

    ManagerAccount = f"{Version}/AccountService"
    COMPUTE_RESET = "/Actions/ComputerSystem.Reset"
    BIOS_RESET = "/Bios/Settings/Actions/Bios.ResetBios"
    BIOS_SETTINGS = "/Bios/Settings"
    BIOS = "/Bios"
    CHASSIS = "/Chassis"
    # Bios.ChangePassword


class SUPERMICRO_API:
    Sessions = f"{RedfishApi.Version}/SessionService/Sessions"
    BiosAttributeRegistry = f"{RedfishApi.Version}/Registries/BiosAttributeRegistry.v1_0_0"
    FirmwareInventoryBackup = f"{RedfishApi.Version}/UpdateService/FirmwareInventory/Backup_BIOS"
    BMC_Backup = f"{RedfishApi.Version}/UpdateService/FirmwareInventory/Backup_BMC"


class IDRAC_API:
    IDRAC_MANAGER = RedfishApi.Managers
    IDRAC_DELL_MANAGERS = f"{RedfishApi.Version}/Dell/Managers"
    IDRAC_TASKS = f"{RedfishApi.Version}/TaskService/Tasks/"
    IDRAC_LLC = "/iDRAC.Embedded.1/DellLCService"
    BIOS_REGISTRY = "/Bios/BiosRegistry"
    BIOS_SETTINGS = RedfishApi.BIOS_SETTINGS
    COMPUTE_RESET = RedfishApi.COMPUTE_RESET
    BIOS = RedfishApi.BIOS


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
    Links = "Links"
    Members = "Members"
    Datatime = "DateTime"
    Location = "Location"
    Attributes = "Attributes"
    RegistryEntries = "RegistryEntries"

    #
    FirmwareVersion = "FirmwareVersion"
    ManagerServers = "ManagerForServers"
    ManageChassis = "ManagerForChassis"
    LastResetTime = "LastResetTime"
    TimezoneName = "TimeZoneName"
    DateTimeLocalOffset = "DateTimeLocalOffset"
    PowerState = "PowerState"
    UUID = "UUID"

    # Job states
    JobState = "JobState"
    TaskStatus = "TaskStatus"
    PercentComplete = "PercentComplete"

    RedfishSettingsApplyTime = "@Redfish.SettingsApplyTime"
    MaintenanceWindowDuration = "MaintenanceWindowDurationInSeconds"
    MaintenanceWindowStartTime = "MaintenanceWindowStartTime"
    ApplyTime = "ApplyTime"


class JobApplyTypes:
    """Job apply types"""
    InMaintenance = "InMaintenanceWindowOnReset"
    AtMaintenance = "AtMaintenanceWindowStart"
    OnReset = "OnReset"
    Immediate = "Immediate"
