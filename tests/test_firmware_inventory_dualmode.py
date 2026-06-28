"""Dual-mode test for the firmware inventory command."""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_firmware_inventory_returns_inventory_collection(redfish_api):
    """firmware_inv_query returns the firmware inventory collection."""
    result = redfish_api.sync_invoke(
        ApiRequestType.FirmwareInventoryQuery, "firmware_inv_query"
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    json.dumps(result.data)
    assert result.data["@odata.id"] == "/redfish/v1/UpdateService/FirmwareInventory"
    assert result.data["Members"][0]["Id"] == "BIOS"
