"""Shared resource
"""
import json
from enum import auto, Enum
from typing import Optional


class ApiRequestType(Enum):
    """Each commands enum.
    """
    QueryIdrac = auto()
    JobDel = auto()
    AttributeClearPending = auto()
    JobGet = auto()
    Jobs = auto()
    BootOptions = auto()
    SystemConfigQuery = auto()
    BiosQuery = auto()
    IDrackQuery = auto()
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
    ResetManager = auto()
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


class RedfishAction:
    """Action discovery encapsulate each action to RedfishAction.
    """

    def __init__(self,
                 action_name: Optional[str] = "",
                 target: Optional[str] = "",
                 full_redfish_name: Optional[str] = ""):
        self.action_name = action_name
        self.target = target
        self.full_redfish_name = full_redfish_name
        self.args = None

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


class Singleton(type):
    """This base class for all action that singleton
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
