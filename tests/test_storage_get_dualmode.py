"""Dual-mode test for the storage-get command."""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_storage_get_returns_controller_resource(redfish_api):
    """storage_get fetches the requested iDRAC storage controller."""
    result = redfish_api.sync_invoke(
        ApiRequestType.StorageViewQuery,
        "storage_get",
        controller="RAID.Integrated.1-1",
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    json.dumps(result.data)
    assert result.data["@odata.id"] == (
        "/redfish/v1/Systems/System.Embedded.1/Storage/RAID.Integrated.1-1"
    )
    assert result.data["Id"] == "RAID.Integrated.1-1"
