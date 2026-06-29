# Testing

Before I trust a change, I clear any live iDRAC environment and run the offline suite:

```bash
env -u IDRAC_IP -u IDRAC_USERNAME -u IDRAC_PASSWORD pytest -q
ruff check <changed>
```

`IDRAC_IP`, `IDRAC_USERNAME`, and `IDRAC_PASSWORD` are read by the CLI and by the dual-mode test
fixture. If `IDRAC_IP` is still exported from real hardware work, `redfish_api` switches to live mode,
so unset those variables for the default suite.

## Which Lane To Use

**Mock lane, default.** `tests/conftest.py` builds `MockRedfishService` from the captured DMTF tree in
`idrac_ctl/json_responses/`. Dell-shaped gaps are overlaid from `tests/idrac_fixtures/`. The service
handles `GET`, `POST`, `PATCH`, `DELETE`, and action-style POSTs, so mutating command tests can stay
offline.

Use the `redfish_mock` fixture when you need an `IDracManager` wired to the mock, and
`redfish_service` when you need to inspect requests or state changes.

**Dual-mode lane.** `redfish_api`, defined in `tests/conftest.py`, runs the same test against the mock
by default and against approved hardware when `IDRAC_IP` is set. Tests that require hardware are
marked `@pytest.mark.live` and skip without that variable.

For approved live hardware only:

```bash
export IDRAC_IP=<idrac> IDRAC_USERNAME=root IDRAC_PASSWORD=<password>
pytest -q -m live
```

**Vendor-aware mock lane.** `redfish_mock_factory`, defined in `tests/conftest.py`, overlays
`tests/<vendor>_fixtures/` on the DMTF base. `redfish_mock_factory("supermicro")` serves the GB300
shape (`System_0`, `HGX_Baseboard_0`, `BMC_0`, `HGX_BMC_0`) and lets tests prove that generic reads
do not hardcode Dell ids.

Worked examples:

- `tests/test_vendor_portability.py` checks Supermicro system and manager discovery.
- `tests/test_discover.py` checks `classify_vendor()` for Dell, HPE, Supermicro, and generic roots.
- `tests/test_discover_ids.py` checks multi-member system/manager discovery.
- `tests/test_sensors.py` runs the generic `sensors` command against the Supermicro overlay.

**Emulator lane, opt-in.** `tests/test_emulator_smoke.py` targets an external `sushy-emulator --fake`
process through `REDFISH_EMULATOR_URL`. It is skipped by default and validates generic Redfish
transport, not Dell OEM paths.

```bash
pip install sushy-tools
sushy-emulator --fake -i 127.0.0.1 -p 8000
REDFISH_EMULATOR_URL=http://127.0.0.1:8000 pytest tests/test_emulator_smoke.py
```

## Fixtures And Faithfulness

The captured DMTF tree is generic. Dell-only resources belong in `tests/idrac_fixtures/`, and
non-Dell overlays belong in `tests/<vendor>_fixtures/`. Supermicro coverage is query-only and
fixture-derived from a read-only GB300 observation; the Supermicro capability profile keeps query
parameters and job scheduling conservative until verified. HPE is placeholder-only.

## Mac/Linux Parity

`docker/run-tests.sh` builds `ubuntu:24.04`, installs `.[dev]`, and runs the offline suite. Linux is
case-sensitive and macOS is not, so this catches fixture-path mistakes that can hide on a laptop.
Sensitive local files are excluded from the image.

## Coverage Goal

The target is 80% coverage across the 75 command modules. The project does not gate on coverage yet.
When it does, the right approach is a ratchet: raise `--cov-fail-under` as dual-mode tests land so the
floor never moves backward.

Coverage output needs `pytest-cov` in the active environment:

```bash
python -m pip install pytest-cov
env -u IDRAC_IP -u IDRAC_USERNAME -u IDRAC_PASSWORD pytest --cov=idrac_ctl
```

## Fleet And Concurrency Tests

Fleet/concurrency testing is roadmap. The planned proxy reconcile loop, bounded concurrency engine,
multi-server simulator, latency injection, and benchmark harness are not current default gates. See
[scaling-and-benchmarks.md](scaling-and-benchmarks.md) for the planned shape.
