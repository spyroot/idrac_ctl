"""Dual-mode tests for boot option and boot-source commands."""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_boot_options_list_returns_member_uris(redfish_api):
    """boot_sources_query returns BootOptions member Redfish URIs."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BootOptions,
        "boot_sources_query",
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, list)
    assert result.data == [
        "/redfish/v1/Systems/System.Embedded.1/BootOptions/HardDisk.List.1-1",
        "/redfish/v1/Systems/System.Embedded.1/BootOptions/NIC.PxeDevice.1-1",
    ]
    assert result.extra["Members@odata.count"] == 2


def test_boot_options_query_returns_collection(redfish_api):
    """boot_options_query returns the BootOptions collection resource."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BootOptionQuery,
        "boot_options_query",
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    json.dumps(result.data)
    assert result.data["@odata.id"] == (
        "/redfish/v1/Systems/System.Embedded.1/BootOptions"
    )
    assert result.data["Members"][0]["@odata.id"].endswith("/HardDisk.List.1-1")


def test_boot_source_query_filters_linked_boot_option(redfish_api):
    """boot_source_query follows BootOptions links and returns the requested device."""
    result = redfish_api.sync_invoke(
        ApiRequestType.QueryBootOption,
        "boot_source_query",
        boot_source="NIC.PxeDevice",
    )

    assert isinstance(result, CommandResult)
    assert list(result.data) == ["NIC.PxeDevice.1-1"]
    option = result.data["NIC.PxeDevice.1-1"]
    json.dumps(option)
    assert option["BootOptionReference"] == "NIC.PxeDevice.1-1"
    assert option["UefiDevicePath"].startswith("PciRoot")


def test_boot_source_pending_unwraps_settings_attributes(redfish_api):
    """query_pending unwraps DellBootSources Settings Attributes."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BootSourcePending,
        "query_pending",
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    assert result.data["BootMode"] == "Uefi"
    assert result.data["UefiBootSeq"][0]["Name"] == "NIC.PxeDevice.1-1"


def test_boot_source_pending_filter_returns_named_attribute(redfish_api):
    """query_pending returns a selected DellBootSources Settings attribute."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BootSourcePending,
        "query_pending",
        data_filter="BootMode",
    )

    assert isinstance(result, CommandResult)
    assert result.data == "Uefi"
