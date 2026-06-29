"""Offline proof that discovery resolves real non-Dell ids on a Supermicro tree.

Uses the vendor-aware ``redfish_mock_factory("supermicro")`` to serve redacted
GB300 NVL fixtures (two ComputerSystems System_0 + HGX_Baseboard_0, two Managers
BMC_0 + HGX_BMC_0) through the real ``requests`` code path. This proves the
multi-member ``discover_computer_system_ids`` / ``discover_manager_ids`` resolvers
return the ACTUAL vendor ids — not the hardcoded Dell System.Embedded.1 /
iDRAC.Embedded.1 — i.e. the P0 portability work holds on a real non-Dell shape.

NOTE (follow-up): ``idrac_manage_servers`` resolves a single system via the LAST
Managers member (value_from_json_list), which on this 2-manager box is HGX_BMC_0 ->
HGX_Baseboard_0 (the GPU baseboard), not the host System_0. Host-vs-baseboard
selection is a separate engine increment; these tests pin the multi-member
discovery the fix will build on.
"""


def test_supermicro_systems_discovered(redfish_mock_factory):
    """discover_computer_system_ids enumerates both real members, not a Dell id."""
    mgr, _ = redfish_mock_factory("supermicro")
    ids = mgr.discover_computer_system_ids()
    assert ids == [
        "/redfish/v1/Systems/System_0",
        "/redfish/v1/Systems/HGX_Baseboard_0",
    ]
    assert "/redfish/v1/Systems/System.Embedded.1" not in ids


def test_supermicro_managers_discovered(redfish_mock_factory):
    """discover_manager_ids enumerates BMC_0 + HGX_BMC_0, not iDRAC.Embedded.1."""
    mgr, _ = redfish_mock_factory("supermicro")
    ids = mgr.discover_manager_ids()
    assert ids == [
        "/redfish/v1/Managers/BMC_0",
        "/redfish/v1/Managers/HGX_BMC_0",
    ]
    assert "/redfish/v1/Managers/iDRAC.Embedded.1" not in ids


def test_supermicro_host_system_present(redfish_mock_factory):
    """The host ComputerSystem (System_0) is discoverable for host-scoped ops."""
    mgr, _ = redfish_mock_factory("supermicro")
    assert "/redfish/v1/Systems/System_0" in mgr.discover_computer_system_ids()


def test_dell_overlay_unaffected_by_vendor_factory(redfish_mock):
    """The default Dell-shaped mock still resolves System.Embedded.1 (no regression)."""
    assert redfish_mock.idrac_manage_servers == "/redfish/v1/Systems/System.Embedded.1"


def test_supermicro_idrac_manage_servers_picks_host(redfish_mock_factory):
    """On the 2-system GB300, idrac_manage_servers resolves the HOST (System_0),
    not the GPU baseboard HGX_Baseboard_0 that last-member selection would pick."""
    mgr, _ = redfish_mock_factory("supermicro")
    assert mgr.idrac_manage_servers == "/redfish/v1/Systems/System_0"
