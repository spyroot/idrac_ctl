"""Dual-mode tests for system configuration commands."""

from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_manager import CommandResult
from idrac_ctl.system.cmd_system_config import ExportSystemConfig


def test_system_export_posts_expected_payload_in_mock_mode(
    redfish_mock, redfish_service, monkeypatch
):
    """system-export POSTs the requested export options and records the task."""
    task_state = {"TaskState": "Completed", "TaskStatus": "OK"}

    def fetch_task(self, task_id):
        assert task_id == redfish_service.JOB_ID
        return task_state

    monkeypatch.setattr(ExportSystemConfig, "fetch_task", fetch_task)

    result = redfish_mock.sync_invoke(
        ApiRequestType.SystemConfigQuery,
        "sysconfig_query",
        export_format="xml",
        export_use="Clone",
        include_in_export="IncludeReadOnly",
        target="BIOS",
    )

    assert isinstance(result, CommandResult)
    assert result.data["task_id"] == redfish_service.JOB_ID
    assert result.data["task_state"] == task_state

    request = redfish_service.last_request
    assert request.method == "POST"
    assert request.path.lower().endswith(
        "/redfish/v1/managers/idrac.embedded.1/actions/oem/"
        "eid_674_manager.exportsystemconfiguration"
    )
    assert request.json() == {
        "ExportFormat": "XML",
        "ShareParameters": {
            "Target": "BIOS",
            "FileName": "",
        },
        "IncludeInExport": "IncludeReadOnly",
        "ExportUse": "Clone",
    }
