"""Offline regression test: importing the discovery command must not import numpy.

The discovery command (idrac_ctl/discovery/cmd_discovery.py) only needs numpy for
``np.save`` inside ``save_url_file_mapping``. A top-level ``import numpy`` made the
whole module unimportable in environments without numpy, which blocked collecting
the offline pytest suite. The import is now lazy, so importing the module must not
pull numpy into ``sys.modules``.

Author Mus spyroot@gmail.com
"""
import importlib
import sys


def test_discovery_module_imports_without_numpy():
    """Importing cmd_discovery fresh does not import numpy at module load time."""
    module_name = "idrac_ctl.discovery.cmd_discovery"

    # Drop any cached copies so the import really re-executes the module body.
    sys.modules.pop(module_name, None)
    sys.modules.pop("numpy", None)

    importlib.import_module(module_name)

    assert "numpy" not in sys.modules, (
        "importing idrac_ctl.discovery.cmd_discovery must not import numpy; "
        "the numpy import should be lazy inside save_url_file_mapping"
    )
