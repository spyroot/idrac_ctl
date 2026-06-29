"""Dual-mode tests for the firmware query command."""

import json
from urllib.parse import unquote, urlsplit

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult

FIRMWARE_INVENTORY_PATH = "/redfish/v1/UpdateService/FirmwareInventory"


def _assert_firmware_inventory_result(result):
    """Assert the shared firmware inventory collection response shape."""
    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    json.dumps(result.data)
    assert result.data["@odata.id"] == FIRMWARE_INVENTORY_PATH
    assert isinstance(result.data["Members"], list)
    assert result.data["Members"][0]["Id"] == "BIOS"


def test_firmware_query_returns_inventory_collection(redfish_api):
    """firmware_query returns a JSON-serializable firmware inventory collection."""
    result = redfish_api.sync_invoke(ApiRequestType.FirmwareQuery, "firmware_query")

    _assert_firmware_inventory_result(result)


def test_firmware_query_deep_uses_expand_collection_path_in_mock_mode(
    redfish_mock,
    redfish_service,
):
    """firmware_query with do_deep=True GETs FirmwareInventory with $expand."""
    result = redfish_mock.sync_invoke(
        ApiRequestType.FirmwareQuery,
        "firmware_query",
        do_deep=True,
    )

    _assert_firmware_inventory_result(result)
    request = redfish_service.last_request
    assert request.method == "GET"
    assert request.path.lower() == FIRMWARE_INVENTORY_PATH.lower()

    raw_query = request.query or urlsplit(request.url).query
    assert unquote(raw_query) == "$expand=*($levels=1)"
