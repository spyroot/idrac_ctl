#!/usr/bin/env bash
set -euo pipefail

# Preview and apply a small WorkloadProfile spec.
cat > /tmp/workload_profile.spec.json <<'JSON'
{
  "Attributes": {
    "WorkloadProfile": "LowLatencyOptimizedProfile"
  }
}
JSON

idrac_ctl bios-registry --attr_name WorkloadProfile
idrac_ctl bios-change --from_spec /tmp/workload_profile.spec.json on-reset --show
idrac_ctl bios-change --from_spec /tmp/workload_profile.spec.json on-reset -r
