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


class HTTPMethod(Enum):
    """Base HTTP methods.
    """
    GET = auto()
    POST = auto()
    PUSH = auto()
    PATCH = auto()
    DELETE = auto()
