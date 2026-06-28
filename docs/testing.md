# Testing

The suite runs fully offline by default — no iDRAC, no network — and stays green on macOS and Linux.
Hardware and emulator paths are opt-in.

```bash
env -u IDRAC_IP -u IDRAC_USERNAME -u IDRAC_PASSWORD pytest -q
ruff check <changed>
```

Unset the `IDRAC_*` variables for offline runs. The dual-mode `redfish_api` fixture switches to live
mode when `IDRAC_IP` is exported, so a shell used for real iDRAC work should not be reused for the
offline suite without clearing those variables.

## Three lanes

**1. Mock (default, offline).** A stateful `MockRedfishService` (`tests/conftest.py`) serves the
captured DMTF mockup tree (`idrac_ctl/json_responses/`) over a mocked `requests` transport, handling
`GET/POST/PATCH/DELETE` + Actions (PATCH overlays state; an Action POST returns a 202 JID `Location`
like iDRAC). Dell-shaped paths the generic tree lacks are hand-authored in `tests/idrac_fixtures/` and
overlay the captured tree. Fixtures: `redfish_mock`, `redfish_service` (request inspection).

**2. Dual-mode (`redfish_api`).** Write a test once; it runs offline (mock) by default and against real
hardware when `IDRAC_IP` is set. Hardware tests are marked `@pytest.mark.live` and auto-skip without
`IDRAC_IP`. Template: `tests/test_cmd_boot_dualmode.py`.

```bash
export IDRAC_IP=<idrac> IDRAC_USERNAME=root IDRAC_PASSWORD=<pw>
pytest -q -m live          # against an approved, non-production iDRAC
```

**3. Live-like emulator (opt-in).** The OpenStack `sushy-tools` fake driver — no libvirt, no Docker,
supports mutating Actions — stands in as a spec-conformant Redfish server.

```bash
pip install sushy-tools
sushy-emulator --fake -i 127.0.0.1 -p 8000
REDFISH_EMULATOR_URL=http://127.0.0.1:8000 pytest tests/test_emulator_smoke.py
```

It serves generic Redfish (not Dell OEM), so it validates transport and generic capabilities; Dell
paths still use the mock fixtures.

## Mac/Linux parity

`docker/run-tests.sh` builds `ubuntu:24.04`, installs `.[dev]`, and runs the offline suite. Linux is
case-sensitive and macOS is not, so this guards a real bug class (the fixture lookup is deliberately
case-insensitive). Sensitive local files are excluded from the image.

## Fixtures and faithfulness

The captured tree is generic DMTF mockup data; many commands hit Dell-specific paths. The faithful way
to cover them offline is a one-time capture of a real iDRAC with **DMTF Redfish-Mockup-Creator** into
`tests/idrac_fixtures/`. That capture is the main unblock for the 80% coverage goal.

## Coverage goal

Target **80%**, currently lower because the ~100 command modules are exercised only as live tests are
ported to dual-mode. Coverage output requires `pytest-cov` in the active environment:

```bash
python -m pip install pytest-cov
env -u IDRAC_IP -u IDRAC_USERNAME -u IDRAC_PASSWORD pytest --cov=idrac_ctl
```

Enforce a **ratcheting** `--cov-fail-under` (raise as tests land) so the floor never regresses, rather
than a hard gate that fails today.

## Fleet/concurrency tests

The planned proxy reconcile loop and concurrency engine should be tested against a fleet simulator
(N synthetic servers, latency/failure injection) and benchmarked before they become default gates. See
[scaling-and-benchmarks.md](scaling-and-benchmarks.md).
