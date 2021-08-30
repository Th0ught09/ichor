from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.globals import Machine
from ichor.modules import GaussianModules, Modules
from ichor.submission_script.check_manager import CheckManager
from ichor.submission_script.command_line import CommandLine, SubmissionError

# matt_todo: I think gaussian.py is a bit ambiguous name. Make into something like aimall_submission_script.py to be more precise.
class GaussianCommand(CommandLine):
    def __init__(
        self,
        gjf_file: Path,
        gjf_output: Optional[Path] = None,
        check: bool = True,
    ):
        self.gjf_file = gjf_file
        self.gjf_output = gjf_output or gjf_file.with_suffix(".gau")
        self.check = check

    @property
    def data(self) -> List[str]:
        # matt_todo: What is the difference between .gau and .wfn files. Maybe mention is somewhere in the documentation.
        """Return a list of the absolute paths of the Gaussian input file (.gjf) and the output file (.gau)"""
        return [str(self.gjf_file.absolute()), str(self.gjf_output.absolute())]

    @classproperty
    def modules(self) -> Modules:
        """ Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return GaussianModules

    @classproperty
    def command(self) -> str:
        """Returns the command used to run Gaussian on different machines."""
        from ichor.globals import GLOBALS

        if GLOBALS.MACHINE is Machine.csf3:
            return "$g09root/g09/g09"
        elif GLOBALS.MACHINE is Machine.ffluxlab:
            return "g09"
        elif GLOBALS.MACHINE is Machine.local:
            return "g09_test"
        raise SubmissionError(
            f"Command not defined for '{self.__name__}' on '{GLOBALS.MACHINE.name}'"
        )

    @classproperty
    def ncores(self) -> int:
        """Returns the number of cores that Gaussian should use for the job."""
        from ichor.globals import GLOBALS

        return GLOBALS.GAUSSIAN_CORE_COUNT

    def repr(self, variables: List[str]) -> str:
        """ Returns a strings which is then written out to the final submission script file.
        If the outputs of the job need to be checked (by default self.check is set to True, so job outputs are checked),
        then the corres
        """

        # matt_todo: maybe add a check to see if the correct number of arrays is passed in.

        cmd = f"{self.command} {variables[0]} {variables[1]}"  # variables[0] ${arr1[$SGE_TASK_ID-1]}, variables[1] ${arr2[$SGE_TASK_ID-1]}

        if self.check:
            from ichor.globals import GLOBALS

            cm = CheckManager(
                check_function="check_gaussian_output",
                check_args=[variables[0]],
                ntimes=GLOBALS.GAUSSIAN_N_TRIES,
            )
            return cm.check(cmd)
        else:
            return cmd
