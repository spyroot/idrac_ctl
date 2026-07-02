#!/usr/bin/env bash
set -euo pipefail

# Read running jobs.
idrac_ctl jobs --running

# Read completed jobs.
idrac_ctl jobs --completed

# Watch one job until it reaches a terminal state.
idrac_ctl job-watch --job_id JID_746683021869

# Delete one approved job.
idrac_ctl job-rm --job_id JID_746683021869
