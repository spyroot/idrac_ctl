"""Dual-mode tests for BIOS pending and registry commands."""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_bios_pending_returns_pending_attributes(redfish_api):
    """bios_query_pending unwraps Attributes from the pending BIOS settings resource."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BiosQueryPending,
        "bios_query_pending",
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    json.dumps(result.data)
    assert result.data["BootMode"] == "Uefi"
    assert result.data["SriovGlobalEnable"] == "Enabled"


def test_bios_pending_filter_returns_single_attribute_value(redfish_api):
    """bios_query_pending returns the selected pending BIOS attribute value."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BiosQueryPending,
        "bios_query_pending",
        data_filter="SriovGlobalEnable",
    )

    assert isinstance(result, CommandResult)
    assert result.data == "Enabled"


def test_bios_registry_returns_registry_entries(redfish_api):
    """bios_registry returns BIOS registry attributes."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BiosRegistry,
        "bios_registry",
        is_registry_only=True,
        is_value_only=False,
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, list)
    json.dumps(result.data)
    assert result.data[0]["AttributeName"] == "ProcCStates"
    assert result.data[0]["ReadOnly"] is False


def test_bios_registry_filters_attribute_names(redfish_api):
    """bios_registry filters registry entries by requested attribute name."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BiosRegistry,
        "bios_registry",
        attr_name="SriovGlobalEnable",
        is_value_only=False,
    )

    assert isinstance(result, CommandResult)
    assert len(result.data) == 1
    assert result.data[0]["AttributeName"] == "SriovGlobalEnable"
    assert result.data[0]["Value"] == [
        {"ValueName": "Enabled"},
        {"ValueName": "Disabled"},
    ]
