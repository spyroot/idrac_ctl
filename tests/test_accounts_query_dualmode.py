"""Dual-mode test for the accounts query command."""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_accounts_query_returns_account_collection(redfish_api):
    """query_accounts returns the iDRAC account collection."""
    result = redfish_api.sync_invoke(ApiRequestType.QueryAccounts, "query_accounts")

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    json.dumps(result.data)
    assert result.data["@odata.id"] == "/redfish/v1/AccountService/Accounts"
    assert result.data["Members"][0]["@odata.id"] == (
        "/redfish/v1/AccountService/Accounts/2"
    )
