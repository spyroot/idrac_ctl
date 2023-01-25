# running jobs
python idrac_ctl.py jobs --running

# completed jobs
python idrac_ctl.py jobs --completed

# watch job
python idrac_ctl.py job-watch --job_id JID_746683021869

# delete job
python idrac_ctl.py job-rm JID_746683021869