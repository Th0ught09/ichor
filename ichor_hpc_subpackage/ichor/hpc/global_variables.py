import platform

from ichor.hpc.batch_system.local import LocalBatchSystem
from ichor.hpc.batch_system.parallel_environment import ParallelEnvironments
from ichor.hpc.batch_system.sge import SunGridEngine
from ichor.hpc.batch_system.slurm import SLURM
from ichor.hpc.file_structure import FileStructure
from ichor.hpc.log import setup_logger
from ichor.hpc.machine import init_machine, Machine
from ichor.hpc.submission_script.script_names import ScriptNames

FILE_STRUCTURE = FileStructure()

BATCH_SYSTEM = LocalBatchSystem
if SunGridEngine.is_present():
    BATCH_SYSTEM = SunGridEngine
if SLURM.is_present():
    BATCH_SYSTEM = SLURM

# will be Machine.Local if machine is not in list of names
machine_name: str = platform.node()
MACHINE = init_machine(machine_name)

PARALLEL_ENVIRONMENT = ParallelEnvironments()
PARALLEL_ENVIRONMENT[Machine.csf3]["smp.pe"] = 2, 32
PARALLEL_ENVIRONMENT[Machine.csf4]["serial"] = 1, 1
PARALLEL_ENVIRONMENT[Machine.csf4]["multicore"] = 2, 32
PARALLEL_ENVIRONMENT[Machine.ffluxlab]["smp"] = 2, 44
PARALLEL_ENVIRONMENT[Machine.local]["smp"] = 1, 100

logger = setup_logger("ICHOR", "ichor.log")
timing_logger = setup_logger("TIMING", "ichor.timing")


SCRIPT_NAMES = ScriptNames(
    {
        "gaussian": "GAUSSIAN.sh",
        "aimall": "AIMALL.sh",
        "ferebus": "FEREBUS.sh",
        "ichor": ScriptNames(
            {
                "gaussian": "ICHOR_GAUSSIAN.sh",
                "aimall": "ICHOR_AIMALL.sh",
                "ferebus": "ICHOR_FEREBUS.sh",
                "active_learning": "ICHOR_ACTIVE_LEARNING.sh",
                "make_sets": "ICHOR_MAKE_SETS.sh",
                "collate_log": "ICHOR_COLLATE_LOG.sh",
                "dlpoly": ScriptNames(
                    {
                        "setup": "ICHOR_DLPOLY_SETUP.sh",
                        "gaussian": "ICHOR_DLPOLY_GAUSSIAN.sh",
                        "energies": "ICHOR_DLPOLY_ENERGIES.sh",
                    }
                ),
                "pandora": ScriptNames(
                    {
                        "pyscf": "ICHOR_PANDORA_PYSCF.sh",
                        "morfi": "ICHOR_PANDORA_MORFI.sh",
                    }
                ),
            }
        ),
        "pandora": ScriptNames(
            {"pyscf": "PANDORA_PYSCF.sh", "morfi": "PANDORA_MORFI.sh"}
        ),
        "dlpoly": "DLPOLY.sh",
        "dlpoly_gaussian": "ICHOR_DLPOLY_GAUSSIAN.sh",
        "amber": "AMBER.sh",
        "cp2k": "CP2K.sh",
        "opt": ScriptNames(
            {"gaussian": "GEOM_OPT.sh", "convert": "GEOM_OPT_CONVERT.sh"}
        ),
        "analysis": ScriptNames(
            {"geometry": "GEOMETRY_ANALYSIS.sh", "rotate-mol": "ROTATE_MOL.sh"}
        ),
    }
)
