"""Dual-mode test for the Dell Lifecycle Controller service query command."""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_dell_lc_service_query_returns_actions(redfish_api):
    """dell_lc_services returns the Dell LC service resource and its actions."""
    result = redfish_api.sync_invoke(ApiRequestType.DellLcQuery, "dell_lc_services")

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, CommandResult)
    assert isinstance(result.data.data, dict)
    json.dumps(result.data.data)
    assert result.data.data["@odata.id"] == (
        "/redfish/v1/Dell/Managers/iDRAC.Embedded.1/DellLCService"
    )
    assert result.data.data["ServiceEnabled"] is True
    assert "GetRemoteServicesAPIStatus" in result.discovered
    assert "GetRSStatus" in result.discovered
