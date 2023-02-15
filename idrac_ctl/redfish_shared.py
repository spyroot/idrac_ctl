from enum import auto, Enum


class RedfishActions(Enum):
    BiosReset = "Bios.ResetBios"
    ManagerReset = "#Manager.Reset"
    ComputerSystemReset = "ComputerSystem.Reset"


class RedfishApiRespond:
    """This base redfish api error.
    IDRAC overwrite so in case of different semantics
    we don't have special cases.
    """
    Ok = auto()
    Error = auto()
    Success = auto()
    AcceptedTaskGenerated = auto()


class RedfishJsonSpec:
    """

    """
    Links = "Links"
    Location = "Links"
    WwwAuthentication = "WWW-Authenticate"


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
    #
    MembersCount = "Members@odata.count"


    # This property is an array of references to the systems that this manager has control over.
    ManagerServers = "ManagerForServers"
    # This property is an array of references to the chassis that this manager has control over.
    ManagerForChassis = "ManagerForChassis"
    # Manager.Reset

    Attributes = "Attributes"


class RedfishApi:
    """
    """
    Version = "/redfish/v1"
    Managers = f"{Version}/Managers"
    Systems = f"{Version}/Systems"
    Chassis = f"{Version}/Chassis"

    UpdateService = f"{Version}/UpdateService"
    UpdateServiceAction = f"{Version}/{UpdateService}/Actions/SimpleUpdate"

    ManagerAccount = f"{Version}/AccountService"
    COMPUTE_RESET = "/Actions/ComputerSystem.Reset"
    BIOS_RESET = "/Bios/Settings/Actions/Bios.ResetBios"
    BIOS_SETTINGS = "/Bios/Settings"
    BIOS = "/Bios"
    CHASSIS = "/Chassis"
