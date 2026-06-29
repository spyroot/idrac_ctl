"""Dual-mode tests for the manager reset command."""

from idrac_ctl.idrac_shared import ApiRequestType, JobState
from idrac_ctl.manager.cmd_manager_reset import ManagerReset
from idrac_ctl.redfish_manager import CommandResult


def test_manager_reset_posts_graceful_restart_in_mock_mode(
    redfish_mock, redfish_service, monkeypatch
):
    """manager_reset POSTs the graceful reset action and records the job state."""

    def fetch_task(self, task_id):
        assert task_id == redfish_service.JOB_ID
        return JobState.Completed

    monkeypatch.setattr(ManagerReset, "fetch_task", fetch_task)

    result = redfish_mock.sync_invoke(
        ApiRequestType.ManagerReset, "manager_reset"
    )

    assert isinstance(result, CommandResult)
    assert result.data["task_id"] == redfish_service.JOB_ID
    assert result.data["task_state"] == JobState.Completed

    reset_requests = [
        request
        for request in redfish_service.requests
        if request.path.lower().endswith("/actions/manager.reset")
    ]
    assert len(reset_requests) == 1
    request = reset_requests[0]
    assert request.method == "POST"
    assert request.path.lower() == (
        "/redfish/v1/managers/idrac.embedded.1/actions/manager.reset"
    )
    assert request.json() == {"ResetType": "GracefulRestart"}
