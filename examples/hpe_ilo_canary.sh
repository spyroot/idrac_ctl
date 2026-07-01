#!/usr/bin/env bash
#
# HPE iLO canary — prove idrac_ctl talks to a REAL HTTP Redfish service on a
# non-Dell box, with no hardware, using HPE's open-source iLO Redfish emulator
# (BSD-3, https://github.com/HewlettPackard/ilo-redfish-emulator). It ships iLO
# mockups for several ProLiant trees; we serve the DL380a (H100 NVL) one.
#
# Requires: docker + docker compose, git, and idrac_ctl installed.
# Everything here is READ-ONLY (system-reset runs as a dry-run without --confirm).
set -euo pipefail

WORK="${TMPDIR:-/tmp}/ilo-redfish-emulator"
PORT="${HPE_EMULATOR_PORT:-45678}"
TREE="${HPE_EMULATOR_TREE:-DL380a}"

# 1) fetch the emulator (once) and serve one iLO tree over HTTPS on $PORT
[ -d "$WORK" ] || git clone --depth 1 https://github.com/HewlettPackard/ilo-redfish-emulator "$WORK"
cd "$WORK"
EXTERNAL_PORT="$PORT" MOCKUP_FOLDER="$TREE" docker compose up -d
trap 'docker compose down' EXIT
sleep 5   # let the service come up

# 2) point idrac_ctl at it — the emulator uses root / root_password on localhost
export IDRAC_IP="127.0.0.1" IDRAC_PORT="$PORT"
export IDRAC_USERNAME="root" IDRAC_PASSWORD="root_password"
export PYTHONWARNINGS="ignore:Unverified HTTPS request"

# 3) run vendor-neutral READ commands against the live HPE tree
idrac_ctl sensors                                   # chassis sensor readings
idrac_ctl network-adapters                          # NICs / DPUs
idrac_ctl metric-reports                            # TelemetryService values
idrac_ctl component-integrity                       # SPDM attestation state
idrac_ctl actions                                   # every action + its risk level
idrac_ctl system-reset --reset_type GracefulRestart # DRY-RUN preview (no --confirm)

echo "HPE iLO canary OK — idrac_ctl drove a live non-Dell Redfish service."
