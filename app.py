import importlib
import sys
from idrac_ctl import idrac_main_ctl


def main():
    try:
        idrac_main_ctl()
    except ModuleNotFoundError:
        print('Invalid command')
        sys.exit(1)
