# from bios import BiosQuery
# from hardware import HardwareInventorQuery
from .system.cmd_system import *
from .system.cmd_system_config import *
from .system.cmd_system_import import *

from .cmd_boot import *
from .cmd_power_state import *
from base.raid.cmd_raid_service import *
from .bios.cmd_bios import *
from .bios.cmd_bios_clear_pending import *
from .attribute.cmd_attribute import *
from .attribute.cmd_attribute_clear_pending import *
from .boot_source.cmd_boot_source_enable import *
from .boot_source.cmd_boot_sources_list import *
from .boot_source.cmd_boot_source_get import *
from .boot_source.cmd_boot_options import *
from .boot_source.cmd_boot_settings import *
from .boot_source.cmd_clear_pending import *
from .jobs.cmd_jobs import *
from .jobs.cmd_job_get import *
from .jobs.cmd_job_services import *
from .cmd_firmware import *
from .cmd_firmware_inv import *
from .pci.cmd_pci import *
from .cmd_get_task import *
from .jobs.cmd_job_del import *
from .cmd_manager import *
from .cmd_virtual_media_get import *
from .cmd_virtual_media_insert import *
from .cmd_virtual_media_eject import *
from .cmd_current_boot import *
from .cmd_boot_one_shot import *
from .cmd_virtual_disk import *

from .cmd_query import *

# storage
from .storage.cmd_storage_controllers import *
from .storage.cmd_storage_list import *
from .storage.cmd_storage_get import *

from .chassis.cmd_chassis_query import *
from .chassis.cmd_chasis_reset import *
