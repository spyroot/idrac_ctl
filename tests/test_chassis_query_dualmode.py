"""Dual-mode test for the chassis query command."""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_chassis_query_returns_idrac_chassis_collection(redfish_api):
    """chassis_service_query returns the iDRAC chassis collection."""
    result = redfish_api.sync_invoke(
        ApiRequestType.ChassisQuery, "chassis_service_query"
    )

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, CommandResult)
    assert isinstance(result.data.data, dict)
    json.dumps(result.data.data)
    assert result.data.data["@odata.id"] == "/redfish/v1/Chassis"
    assert result.data.data["Members"][0]["@odata.id"] == (
        "/redfish/v1/Chassis/System.Embedded.1"
    )
