# running jobs
idrac_ctl idrac_ctl jobs --running

# completed jobs
idrac_ctl jobs --completed

# watch job
idrac_ctl job-watch --job_id JID_746683021869

# delete job
idrac_ctl idrac_ctl.py job-rm JID_746683021869