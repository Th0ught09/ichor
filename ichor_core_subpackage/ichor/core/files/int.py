from pathlib import Path
from typing import Union, List, Dict, Optional
from enum import Enum

from ichor.core.common.str import get_digits
import numpy as np
from ichor.core.common.functools import classproperty
from ichor.core.common.types import Coordinates3D
from ichor.core.files.file import FileContents, ReadFile, File
from ichor.core.files.file_data import HasProperties
from ichor.core.multipoles import (
    rotate_dipole,
    rotate_hexadecapole,
    rotate_octupole,
    rotate_quadrupole,
)
from ichor.core.constants import (
    spherical_monopole_labels,
    spherical_dipole_labels,
    spherical_quadrupole_labels,
    spherical_octupole_labels,
    spherical_hexadecapole_labels,
)
from ichor.core.atoms import Atoms
from ichor.core.common.io import relpath, convert_to_path


class CriticalPointType(Enum):
    Bond = "BCP"
    Ring = "RCP"
    Cage = "CCP"


class CriticalPoint(Coordinates3D):
    def __init__(
        self,
        index: int,
        ty: CriticalPointType,
        x,
        y,
        z,
        connecting_atoms: List[str],
    ):
        super().__init__(x, y, z)
        self.index: int = index
        self.type: CriticalPointType = ty
        self.connecting_atoms = connecting_atoms


class ParentNotDefined(ValueError):
    pass


class INT(HasProperties, ReadFile):
    """Wraps around one .int file which is generated by AIMALL for every atom in the system.

    :param path: The Path object corresponding to an .int file
    :param parent: An `Atoms` instance which holds the coordinate information for all atoms in the system.
        This information is needed to form the C matrix when rotating multipoles from the global to the local frame.
    """

    def __init__(self, path: Union[Path, str], parent: Atoms = None):
        super().__init__(path)

        # need to have this to rotate multipole moments as they require
        # the whole molecular geometry (int files do not contain that.)
        self._parent = parent

        # we can use this to figure out the
        self.current_directory: Path = FileContents
        self.inp_file_path: Path = FileContents
        self.wfn_file_path: Path = FileContents
        self.out_file_path: Path = FileContents

        self.atom_name: str = FileContents
        self.title: str = FileContents

        self.critical_points: List[CriticalPoint] = FileContents
        self.dft_model: str = FileContents

        self.net_charge: float = FileContents
        self.basin_integration_results: Dict[str, float] = FileContents
        self.global_spherical_multipoles: Dict[str, float] = FileContents
        self.iqa_energy_components: Dict[str, float] = FileContents

        self.total_time: int = FileContents

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of AIMALL files which are used"""
        return ".int"

    @property
    def parent(self) -> Atoms:
        if self._parent is None:
            if not self.wfn.path.exists():
                raise ParentNotDefined(
                    f"'parent' not defined for '{self.path}' instance of '{self.__class__.__name__}'"
                ) from FileNotFoundError(f"No Such File '{self.wfn.path}'")
            else:
                return self.wfn.atoms
        return self._parent

    @parent.setter
    def parent(self, parent: Atoms):
        self._parent = parent

    @property
    def wfn(self) -> "WFN":
        from ichor.core.files import WFN

        return WFN(self.wfn_file_path)

    @property
    def properties(self) -> Dict[str, float]:
        return {**{"iqa": self.iqa}, **self.local_spherical_multipoles()}

    @property
    def bond_critical_points(self) -> List[CriticalPoint]:
        return [
            cp
            for cp in self.critical_points
            if cp.type is CriticalPointType.Bond
        ]

    @property
    def ring_critical_points(self) -> List[CriticalPoint]:
        return [
            cp
            for cp in self.critical_points
            if cp.type is CriticalPointType.Ring
        ]

    @property
    def cage_critical_points(self) -> List[CriticalPoint]:
        return [
            cp
            for cp in self.critical_points
            if cp.type is CriticalPointType.Cage
        ]

    def _path_relative_to_aimall(self, int_path: Path, other: Path) -> Path:
        return relpath(self.path.parent, Path.cwd()) / relpath(
            other, int_path.parent
        )

    def _read_file(self):
        """Read an .int file. The first time that the .int file is read successfully, a json file with the
        important information is written in the same directory.
        """
        with open(self.path, "r") as f:
            line = next(f)
            while "Current Directory" not in line:
                line = next(f)

            # TODO: don't really need these paths as they are relative. add later if needed
            self.current_directory = Path(line.split()[-1])
            next(f)  # blank line

            inp_file_path = self.current_directory / Path(next(f).split()[-1])
            wfn_file_path = self.current_directory / Path(next(f).split()[-1])
            out_file_path = self.current_directory / Path(next(f).split()[-1])

            self.inp_file_path = self._path_relative_to_aimall(
                out_file_path, inp_file_path
            )
            self.wfn_file_path = self._path_relative_to_aimall(
                out_file_path, wfn_file_path
            )
            self.out_file_path = self._path_relative_to_aimall(
                out_file_path, out_file_path
            )

            next(f)  # blank line
            self.title = next(f).split()[-1].strip()

            line = next(f)
            while "critical points" not in line:
                line = next(f)

            line = next(f)
            self.critical_points = []
            while "Optional parameters" not in line:
                if "CP" in line:
                    record = line.split()
                    index = int(record[0])
                    ty = CriticalPointType(record[1])
                    x = float(record[3])
                    y = float(record[4])
                    z = float(record[5])
                    atoms = record[6:] if len(record) >= 7 else []
                    self.critical_points.append(
                        CriticalPoint(index, ty, x, y, z, atoms)
                    )
                line = next(f)

            next(f)
            self.dft_model = next(f).split(":")[-1].strip()

            line = next(f)
            while "Integration is over atom" not in line:
                line = next(f)
            self.atom_name = line.split()[-1].strip()

            line = next(f)
            while "Results of the basin integration" not in line:
                line = next(f)

            self.basin_integration_results = {}
            record = next(f).split()
            self.basin_integration_results[record[0].strip()] = float(
                record[2]
            )
            self.net_charge = float(record[5])
            line = next(f)
            while "Atomic Traceless Quadrupole" not in line:
                if "=" in line:
                    record = line.split("=")
                    self.basin_integration_results[record[0].strip()] = float(
                        record[1].split()[0]
                    )
                line = next(f)

            while "Real Spherical Harmonic Moments" not in line:
                line = next(f)

            next(f)
            next(f)
            next(f)

            self.global_spherical_multipoles = {}
            line = next(f)
            while "=" in line:
                record = line.split("=")
                multipole_name = "".join(
                    c
                    for c in record[0].lower().strip()
                    if c not in {"[", "]", ","}
                )
                self.global_spherical_multipoles[multipole_name] = float(
                    record[1]
                )
                line = next(f)

            # replace q00 so that it subtracts the nuclear charge
            self.global_spherical_multipoles["q00"] = self.net_charge

            while "IQA Energy Components" not in line:
                line = next(f)

            next(f)

            self.iqa_energy_components = {}
            line = next(f)
            while "=" in line:
                name, _, value = line.rpartition("=")
                self.iqa_energy_components[name.strip()] = float(value)
                line = next(f)

            while "Total time" not in line:
                line = next(f)

            self.total_time = int(line.split()[3])

    @property
    def atom_num(self) -> int:
        """Returns the atom index in the system. (atom indices in atom names start at 1)"""
        return get_digits(self.atom_name)

    @property
    def integration_error(self) -> float:
        """The integration error can tell you if a point has been decomposed into topological atoms correctly. A large integration error signals
        that the point might not be suitable for training as the AIMALL IQA/multipole moments might be inaccurate."""
        return self.basin_integration_results["L"]

    @property
    def iqa(self) -> float:
        """Returns the IQA energy of the topological atom that was calculated for this topological atom (since 1 .int file is written for each topological atom)."""
        # YulianM: removed the ADD_DISPERSION. This class should only be used to parse .int files and
        # processing the data should be done somewhere else.

        return self.iqa_energy_components["E_IQA(A)"]

    @property
    def e_intra(self) -> float:
        return self.iqa_energy_components["E_IQA_Intra(A)"]

    @property
    def q(self) -> float:
        """Returns the point charge (monopole moment) of the topological atom."""
        # replace charge with net charge. The Q00 value written in AIMAll does not subtract the nuclear charge.
        return self.net_charge

    @property
    def q00(self) -> float:
        """Returns the point charge (monopole moment) of the topological atom."""
        # replace charge with net charge. The Q00 value written in AIMAll does not subtract the nuclear charge.
        return self.q

    @property
    def dipole_mag(self) -> float:
        """Returns the magnitude of the dipole moment of the topological atom.
        The magnitude of the vector is not affected by the rotation of multipoles."""
        return np.sqrt(
            sum(
                [
                    self.q10**2,
                    self.q11c**2,
                    self.q11s**2,
                ]
            )
        )

    def local_spherical_multipoles(
        self, C_matrix: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """Rotates global spherical multipoles into local spherical multipoles. Optionally
        a rotation matrix can be passed in. Otherwise, the wfn file associated with this int file
        (as read in from the int file) will be used (if it exists).

        :param C_matrix: Optional rotation matrix to be used to rotate multipoles.
        :raises FileNotFoundError: If no `C_matrix` is passed in and the wfn file associated
            with the int file does not exist. Then we cannot calculate multipoles.
        """

        C = (
            C_matrix
            if C_matrix is not None
            else self.parent[self.atom_name].C()
        )

        local_spherical_multipoles = {spherical_monopole_labels[0]: self.q00}

        local_dipole_moments = rotate_dipole(
            *(
                self.global_spherical_multipoles[dipole_label]
                for dipole_label in spherical_dipole_labels
            ),
            C,
        )
        for dipole_name, dipole_value in zip(
            spherical_dipole_labels, local_dipole_moments
        ):
            local_spherical_multipoles[dipole_name] = dipole_value

        local_quadrupole_moments = rotate_quadrupole(
            *(
                self.global_spherical_multipoles[quadrupole_label]
                for quadrupole_label in spherical_quadrupole_labels
            ),
            C,
        )
        for quadrupole_name, quadrupole_value in zip(
            spherical_quadrupole_labels, local_quadrupole_moments
        ):
            local_spherical_multipoles[quadrupole_name] = quadrupole_value

        local_octupole_moments = rotate_octupole(
            *(
                self.global_spherical_multipoles[octupole_label]
                for octupole_label in spherical_octupole_labels
            ),
            C,
        )
        for octupole_name, octupole_value in zip(
            spherical_octupole_labels, local_octupole_moments
        ):
            local_spherical_multipoles[octupole_name] = octupole_value

        local_hexadecapole_moments = rotate_hexadecapole(
            *(
                self.global_spherical_multipoles[hexadecapole_label]
                for hexadecapole_label in spherical_hexadecapole_labels
            ),
            C,
        )
        for hexadecapole_name, hexadecapole_value in zip(
            spherical_hexadecapole_labels, local_hexadecapole_moments
        ):
            local_spherical_multipoles[hexadecapole_name] = hexadecapole_value

        return local_spherical_multipoles
