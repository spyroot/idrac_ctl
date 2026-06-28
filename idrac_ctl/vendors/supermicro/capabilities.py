"""Supermicro capability profile (placeholder).

Scaffolding for a future Supermicro vendor package. Supermicro publishes no
official Python Redfish SDK or emulator, so values stay conservative until
validated against real hardware. Fill in as Supermicro command modules are added.

Author Mus spyroot@gmail.com
"""
from ..base import VendorCapabilities, register

SUPERMICRO = register(
    VendorCapabilities(
        vendor="supermicro",
        oem_prefix="Supermicro",
    )
)
