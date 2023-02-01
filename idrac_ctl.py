"""Main entry for idrac_ctl

The main interface consumed is iDRAC Manager class.
Each command registered dynamically and dispatch to respected execute method
by invoking request from IDRAC Manager.

Author Mus spyroot@gmail.com
"""
from idrac_ctl.idrac_main import idrac_main_ctl
if __name__ == "__main__":
    idrac_main_ctl()
