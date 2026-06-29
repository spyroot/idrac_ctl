# Quick out-of-band sensor health check across all chassis (works on Dell and Supermicro)
# Dump every sensor and pull just the temps for a glance
idrac_ctl sensors | jq '.data[] | select(.Name | test("Temp")) | {Name, Reading, ReadingUnits, Health}'
# Confirm we're looking at the right box
idrac_ctl chassis
# System summary
idrac_ctl system
# Power supplies, fans, and voltages
idrac_ctl sensors | jq '.data[] | select(.Name | test("PS|Fan|Volt")) | {Name, Reading, ReadingUnits, Health}'
