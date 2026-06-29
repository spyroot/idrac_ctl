"""Dual-mode smoke tests for optional out-of-band Redfish read commands."""

import pytest

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult

GPU_OOB_READ_COMMANDS = (
    (ApiRequestType.MetricReportDefinitions, "metric-definitions"),
    (ApiRequestType.MetricReports, "metric-reports"),
    (ApiRequestType.ComponentIntegrity, "component-integrity"),
    (ApiRequestType.NetworkAdapters, "network-adapters"),
    (ApiRequestType.NvLinkPorts, "nvlink-ports"),
)


@pytest.mark.parametrize(("request_type", "command_name"), GPU_OOB_READ_COMMANDS)
def test_gpu_oob_commands_return_list_payloads(redfish_api, request_type, command_name):
    """OOB read commands return lists and tolerate missing optional collections."""
    result = redfish_api.sync_invoke(request_type, command_name)

    assert isinstance(result, CommandResult)
    assert isinstance(result.data, list)
    assert result.error is None

    if redfish_api.idrac_ip == "mock-idrac":
        assert result.data == []
