"""Dual-mode test for the boot-source query command.

Runs offline by default against the mock service (using the iDRAC-shaped fixture
in tests/idrac_fixtures/), and against real hardware when IDRAC_IP is set. This is
the template for porting the remaining live-only command tests: invoke the command
through sync_invoke and assert the CommandResult shape.

Author Mus spyroot@gmail.com
"""
import json

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult


def test_boot_query(redfish_api):
    """boot_query returns a JSON-serializable CommandResult from /BootSources."""
    result = redfish_api.sync_invoke(
        ApiRequestType.BootQuery, "boot_query"
    )
    assert isinstance(result, CommandResult)
    assert isinstance(result.data, dict)
    # the payload must be JSON-serializable (CLI renders it as JSON)
    json.dumps(result.data)
    # in mock mode the fixture carries the iDRAC boot-source attributes
    assert result.data["@odata.id"].endswith("/BootSources")
