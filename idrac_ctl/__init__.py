# from bios import BiosQuery
# from hardware import HardwareInventorQuery
from .redfish_shared import *

from .system.cmd_system import *
from .system.cmd_system_config import *
from .system.cmd_system_import import *
#
from .cmd_boot import *
from .dell_lc.cmd_dell_lc_api import *
from .dell_lc.cmd_dell_lc_rs import *
from .dell_lc.cmd_dell_lc_services import *
#
# compute
from .compute.cmd_power_state import *
from .compute.cmd_compute_setting import *

from .idrac_shared import *
from .raid.cmd_raid_service import *
#
# bios commands
from .bios.cmd_bios import *
from .bios.cmd_bios_clear_pending import *
from .bios.cmd_bios_pending import *
from .bios.cmd_change_boot_order import *
from .bios.bios_registry import *
from .bios.cmd_change_bios import *
from .bios.cmd_bios_reset_default import *
#
from .attribute.cmd_attribute import *
from .attribute.cmd_attribute_clear_pending import *
from .attribute.cmd_attribute_update import *
#
#
# # jobs command
from .jobs.cmd_jobs import *
from .jobs.cmd_job_get import *
from .jobs.cmd_job_services import *
from .jobs.cmd_job_watch import *
from .jobs.cmd_job_del import *
from .jobs.cmd_job_dell_services import *
from .jobs.cmd_job_delete_all import *
from .jobs.cmd_job_apply import *
#
# # firmwares cmds
from .firmware.cmd_firmware import *
from .firmware.cmd_firmware_inv import *

from .pci.cmd_pci import *

# manager cmds
from .manager.cmd_manager import *
from .manager.cmd_manager_reset import *


# virtual medial cmds
from .virtual_media.cmd_virtual_media_get import *
from .virtual_media.cmd_virtual_media_insert import *
from .virtual_media.cmd_virtual_media_eject import *
from .cmd_current_boot import *

from .cmd_query import *

# storage
from .storage.cmd_storage_controllers import *
from .storage.cmd_storage_list import *
from .storage.cmd_storage_get import *
from .storage.cmd_drives import *
from .storage.cmd_convert_none_raid import *
from .storage.cmd_convert_to_raid import *

# chassis cmd
from .chassis.cmd_chassis_query import *
from .chassis.cmd_chasis_reset import *
from .chassis.cmd_chassis_query import *

# dell oem attach
from .delloem.delloem_attach_status import *
from .delloem.delloem_actions import *
from .delloem.delloem_attach import *
from .delloem.delloem_detach import *
from .delloem.delloem_disconnect import *
from .delloem.delloem_get_networkios import *
from .delloem.delloem_boot_netios import *
from .delloem.delloem_os_deployment import *


# tasks
from .tasks.cmd_tasks_list import *
from .tasks.cmd_tasks_get import *
from .tasks.cmd_task_watch import *

from .volumes.cmd_initilize import *
from .volumes.cmd_volumes import *
from .volumes.cmd_virtual_disk import *

# boot options
from .boot_options.cmd_boot_option_list import *
from .boot_options.cmd_boot_options_query import *


# boot sources
from .boot_source.cmd_boot_one_shot import *
from .boot_source.cmd_boot_settings import *
from .boot_source.cmd_boot_source_get import *
from .boot_source.cmd_clear_pending import *
from .boot_source.cmd_pending import *
from .boot_source.cmd_enable import *
from .boot_source.cmd_update import *
from .boot_source.cmd_boot_source_registry import *

# account
from .accounts.cmd_accounts import *
from .accounts.cmd_query_account import *
from .accounts.cmd_account_svc import *
from .accounts.cmd_privilage_registry import *

from .discovery.cmd_discovery import *
