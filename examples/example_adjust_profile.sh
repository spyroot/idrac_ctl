idrac_ctl bios-change --from_spec spec/set_profile_example.json
# or
echo "{
  \"Attributes\": {
    \"WorkloadProfile\": \"LowLatencyOptimizedProfile\"
  }
}" > new_spec.json