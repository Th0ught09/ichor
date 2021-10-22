import json
import re
from typing import Optional

import numpy as np

from ichor import constants, patterns
from ichor.common.functools import (buildermethod, cached_property,
                                    classproperty)
from ichor.common.io import move
from ichor.files import FileState
from ichor.files.file import File, FileContents
from ichor.files.geometry import GeometryData, GeometryDataFile


class INT(GeometryDataFile, File):
    """Wraps around one .int file which is generated by AIMALL for every atom in the system.

    :param path: The Path object corresponding to an .int file
    :param parent: An `Atoms` instance which holds the coordinate information for all atoms in the system. This information is needed to form the C matrix when rotating multipoles from the global to the local frame.
    """

    def __init__(self, path, parent=None):
        File.__init__(self, path)
        GeometryDataFile.__init__(self)

        self.parent = parent

        self.integration_data = FileContents
        self.multipoles_data = FileContents
        self.iqa_data = FileContents
        self.dispersion_data = FileContents

    @property
    def atom(self) -> str:
        """Returns the name of the atom, including its index in the molecule. Eg. C1, H2, O3, etc."""
        return self.path.stem.upper()

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of AIMALL files which are used"""
        return ".int"

    @classproperty
    def backup_filetype(cls) -> str:
        """Returns the file extension of AIMALL files which are stored as backup files. These backup files are the original AIMALL files,
        which are renamed so that a json file can be written out as .int instead."""
        return ".bak"

    @buildermethod
    def _read_file(self):
        """Read an .int file. The first time that the .int file is read successfully, a json file with the
        important information is written in the same directory. This json file has the suffix `.int` from now on
        and the original `.int` file is stored with suffix `.int.bak` for backup."""
        try:
            self.read_json()
        except json.decoder.JSONDecodeError:
            self.read_int()
            # Backup only if read correctly
            # E_IQA_Inter(A) Last Line that needs to be parsed, if this is here then the
            # rest of the values we care about should be
            if "E_IQA_Inter(A)" in self.iqa_data.keys():
                self.backup_int()
                self.write_json()
            else:
                # Delete corrupted file so it can be regenerated
                self.delete()

    @buildermethod
    def read_int(self):
        """Method used to parse the AIMAll '.int' file"""

        self.integration_data = GeometryData()
        self.iqa_data = GeometryData()
        self.dispersion_data = GeometryData()
        self.multipoles_data = GeometryData()

        with open(self.path, "r") as f:
            for line in f:
                """
                Following this line, is a bunch of key value pairs (separated by =) of the basin integration results such as:
                - atomic charge
                - integration error
                most of the other data is garbage but is parsed anyway for ease of use and a 'just in case' mentality
                """
                if "Results of the basin integration:" in line:
                    line = next(f)
                    while line.strip():
                        for match in re.finditer(patterns.AIMALL_LINE, line):
                            tokens = match.group().split("=")
                            try:
                                self.integration_data[
                                    tokens[0].strip()
                                ] = float(tokens[-1])
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
                """
                Following this line is 3 lines we can skip followed by the multipoles
                each multipole is labelled as Q[l,|m|,?] as described such as:
                - Q[0,0] = ...
                - Q[4,4,s] = ...
                
                These will be parsed into the following keys:
                - q00 = ...
                - q44s = ...
                
                All multipoles are parsed even though only hexadecapoles are used by ichor
                again 'just in case'
                """
                if "Real Spherical Harmonic Moments Q[l,|m|,?]" in line:
                    _ = next(f)
                    _ = next(f)
                    _ = next(f)
                    line = next(f)
                    while line.strip():
                        if "=" in line:
                            tokens = line.split("=")
                            try:
                                multipole = (
                                    tokens[0]
                                    .strip()
                                    .replace("[", "")
                                    .replace(",", "")
                                    .replace("]", "")
                                )
                                self.multipoles_data[
                                    multipole.lower()
                                ] = float(tokens[-1])
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
                """
                Following this line, we can skip a line and then we have more key value pairs for the iqa data
                Only the E_IQA value is used by ichor but following the 'just in case' mentality, we parse all
                values and store them for access later
                """
                if 'IQA Energy Components (see "2EDM Note"):' in line:
                    _ = next(f)
                    line = next(f)
                    while line.strip():
                        if "=" in line:
                            tokens = line.split("=")
                            try:
                                self.iqa_data[tokens[0].strip()] = float(
                                    tokens[-1]
                                )
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)

        # this should call the multipoles_data.setter, which should make all the q00,q10, etc. attributes
        # thus, the GeometryData getattr method will not look into __dict__, but __getattribute__ will be used directly
        # self.multipoles_data = raw_multipoles_data
        # after setting all the attributes, we rotate them and modify them as needed.
        if self.parent:
            self.rotate_multipoles()

    def rotate_multipoles(self):
        """
        Multipoles from AIMAll are calculated in the global spherical frame whereas DL_FFLUX requires
        multipoles in the local spherical frame. To convert from global to local spherical, one must
        convert from global spherical to global cartesian, rotate global cartesian to local cartesian
        then convert local cartesian to local spherical coordinates. This only has to be done once as
        the result of the rotation is stored in the json int file.

        The spherical-cartesian conversion can be found in Appendix E of:
        Stone, Anthony. The Theory of Intermolecular Forces,
        Oxford University Press, Incorporated, 2013.
        """
        self.rotate_dipole()
        self.rotate_quadrupole()
        self.rotate_octupole()
        self.rotate_hexadecapole()

    @cached_property
    def C(self):
        """
        Mills, M.J.L., Popelier, P.L.A., 2014.
        Electrostatic Forces: Formulas for the First Derivatives of a Polarizable,
        Anisotropic Electrostatic Potential Energy Function Based on Machine Learning.
        Journal of Chemical Theory and Computation 10, 3840–3856.. doi:10.1021/ct500565g

        Eq. 25-30
        """
        from ichor.atoms.calculators.feature_calculator import \
            ALFFeatureCalculator

        atom = self.parent.atoms[self.atom]
        x_axis = ALFFeatureCalculator.calculate_x_axis_atom(atom)
        xy_plane = ALFFeatureCalculator.calculate_xy_plane_atom(atom)

        r12 = x_axis.coordinates - atom.coordinates
        r13 = xy_plane.coordinates - atom.coordinates

        mod_r12 = np.linalg.norm(r12)

        r12 /= mod_r12

        ex = r12
        s = sum(ex * r13)
        ey = r13 - s * ex

        ey /= np.sqrt(sum(ey * ey))
        ez = np.cross(ex, ey)
        return np.array([ex, ey, ez])

    # monopole moments (point charges) do not need to be rotated because they are symmetric

    def rotate_dipole(self):
        """Rotates dipole moment from global cartesian to local cartesian. Attributes like self.q11c, self.q11s, etc. are not
        explicitly defined here, but they can be accessed because of the GeometryData __getattr__ implementation, which allows
        accessing dictionary keys as if they were attributes."""
        # Global cartesian dipole moment d is a simple rearrangement of the spherical form
        d = np.array(
            [self.q11c, self.q11s, self.q10]
        )  # these can be accessed like this because of GeometryData __getattr__ method

        # Rotation of 1D cartesian tensor from global to local frame
        rotated_d = np.einsum("ia,a->i", self.C, d)

        # Rearrange local cartesian tensor back to spherical form
        self.q10 = rotated_d[2]
        self.q11c = rotated_d[0]
        self.q11s = rotated_d[1]

    def rotate_quadrupole(self):
        """Rotates quadrupole moments from the global to local frame"""

        # transform global spherical tensor to global cartesian tensor
        q_xx = 0.5 * constants.rt3 * self.q22c - self.q20
        q_xy = 0.5 * constants.rt3 * self.q22s
        q_xz = 0.5 * constants.rt3 * self.q21c
        q_yy = -0.5 * constants.rt3 * self.q22c + self.q20
        q_yz = 0.5 * constants.rt3 * self.q21s
        q_zz = self.q20

        q = np.array(
            [[q_xx, q_xy, q_xz], [q_xy, q_yy, q_yz], [q_xz, q_yz, q_zz]]
        )

        # rotate global cartesian to local cartesian frame
        rotated_q = np.einsum("ia,jb,ab->ij", self.C, self.C, q)

        # transform local cartesian to local spherical tensor
        self.q20 = rotated_q[2, 2]
        self.q21c = constants.rt12_3 * rotated_q[0, 2]
        self.q21s = constants.rt12_3 * rotated_q[1, 2]
        self.q22c = constants.rt3_3 * (rotated_q[0, 0] - rotated_q[1, 1])
        self.q22s = constants.rt12_3 * rotated_q[0, 1]

    def rotate_octupole(self):
        """Rotates octupole moments from the global to local frame"""

        # transform global spherical tensor to global cartesian tensor
        o_xxx = constants.rt5_8 * self.q33c - constants.rt3_8 * self.q31c
        o_xxy = constants.rt5_8 * self.q33s - constants.rt1_24 * self.q31s
        o_xxz = constants.rt5_12 * self.q32c - 0.5 * self.q30
        o_xyy = -(constants.rt5_8 * self.q33c + constants.rt1_24 * self.q31c)
        o_xyz = constants.rt5_12 * self.q32s
        o_xzz = constants.rt2_3 * self.q31c
        o_yyy = -(constants.rt5_8 * self.q33s + constants.rt3_8 * self.q31s)
        o_yyz = -(constants.rt5_12 * self.q32c + 0.5 * self.q30)
        o_yzz = constants.rt2_3 * self.q31s
        o_zzz = self.q30

        o = np.array(
            [
                [
                    [o_xxx, o_xxy, o_xxz],
                    [o_xxy, o_xyy, o_xyz],
                    [o_xxz, o_xyz, o_xzz],
                ],
                [
                    [o_xxy, o_xyy, o_xyz],
                    [o_xyy, o_yyy, o_yyz],
                    [o_xyz, o_yyz, o_yzz],
                ],
                [
                    [o_xxz, o_xyz, o_xzz],
                    [o_xyz, o_yyz, o_yzz],
                    [o_xzz, o_yzz, o_zzz],
                ],
            ]
        )

        # rotate global cartesian to local cartesian frame
        rotated_o = np.einsum("ia,jb,kc,abc->ijk", self.C, self.C, self.C, o)

        # transform local cartesian to local spherical tensor
        self.q30 = rotated_o[2, 2, 2]
        self.q31c = constants.rt_3_3 * rotated_o[0, 2, 2]
        self.q31s = constants.rt_3_3 * rotated_o[1, 2, 2]
        self.q32c = constants.rt_3_5 * (
            rotated_o[0, 0, 2] - rotated_o[1, 1, 2]
        )
        self.q32s = 2 * constants.rt_3_5 * rotated_o[0, 1, 2]
        self.q33c = constants.rt_1_10 * (
            rotated_o[0, 0, 0] - 3 * rotated_o[0, 1, 1]
        )
        self.q33s = constants.rt_1_10 * (
            3 * rotated_o[0, 0, 1] - rotated_o[1, 1, 1]
        )

    def rotate_hexadecapole(self):
        """Rotates hexadecapole moments from the global to local frame"""

        # transform global spherical tensor to global cartesian tensor
        h_xxxx = (
            0.375 * self.q40
            - 0.25 * constants.rt5 * self.q42c
            + 0.125 * constants.rt35 * self.q44c
        )
        h_xxxy = 0.125 * (
            constants.rt35 * self.q44s - constants.rt5 * self.q42s
        )
        h_xxxz = 0.0625 * (
            constants.rt70 * self.q43c - 3.0 * constants.rt10 * self.q41c
        )
        h_xxyy = 0.125 * self.q40 - 0.125 * constants.rt35 * self.q44c
        h_xxyz = 0.0625 * (
            constants.rt70 * self.q43s - constants.rt10 * self.q41s
        )
        h_xxzz = 0.5 * (0.5 * constants.rt5 * self.q42c - self.q40)
        h_xyyy = -0.125 * (
            constants.rt5 * self.q42s + constants.rt35 * self.q44s
        )
        h_xyyz = -0.0625 * (
            constants.rt10 * self.q41c + constants.rt70 * self.q43c
        )
        h_xyzz = 0.25 * constants.rt5 * self.q42s
        h_xzzz = constants.rt5_8 * self.q41c
        h_yyyy = (
            0.375 * self.q40
            + 0.25 * constants.rt5 * self.q42c
            + 0.125 * constants.rt35 * self.q44c
        )
        h_yyyz = -0.0625 * (
            3.0 * constants.rt10 * self.q41s + constants.rt70 * self.q43s
        )
        h_yyzz = -0.5 * (0.5 * constants.rt5 * self.q42c + self.q40)
        h_yzzz = constants.rt5_8 * self.q41s
        h_zzzz = self.q40

        h = np.array(
            [
                [
                    [
                        [h_xxxx, h_xxxy, h_xxxz],
                        [h_xxxy, h_xxyy, h_xxyz],
                        [h_xxxz, h_xxyz, h_xxzz],
                    ],
                    [
                        [h_xxxy, h_xxyy, h_xxyz],
                        [h_xxyy, h_xyyy, h_xyyz],
                        [h_xxyz, h_xyyz, h_xyzz],
                    ],
                    [
                        [h_xxxz, h_xxyz, h_xxzz],
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xxzz, h_xyzz, h_xzzz],
                    ],
                ],
                [
                    [
                        [h_xxxy, h_xxyy, h_xxyz],
                        [h_xxyy, h_xyyy, h_xyyz],
                        [h_xxyz, h_xyyz, h_xyzz],
                    ],
                    [
                        [h_xxyy, h_xyyy, h_xyyz],
                        [h_xyyy, h_yyyy, h_yyyz],
                        [h_xyyz, h_yyyz, h_yyzz],
                    ],
                    [
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xyyz, h_yyyz, h_yyzz],
                        [h_xyzz, h_yyzz, h_yzzz],
                    ],
                ],
                [
                    [
                        [h_xxxz, h_xxyz, h_xxzz],
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xxzz, h_xyzz, h_xzzz],
                    ],
                    [
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xyyz, h_yyyz, h_yyzz],
                        [h_xyzz, h_yyzz, h_yzzz],
                    ],
                    [
                        [h_xxzz, h_xyzz, h_xzzz],
                        [h_xyzz, h_yyzz, h_yzzz],
                        [h_xzzz, h_yzzz, h_zzzz],
                    ],
                ],
            ]
        )

        # rotate global cartesian to local cartesian frame
        h_rotated = np.einsum(
            "ia,jb,kc,ld,abcd->ijkl", self.C, self.C, self.C, self.C, h
        )

        # transform local cartesian to local spherical tensor
        self.q40 = h_rotated[2, 2, 2, 2]
        self.q41c = constants.rt_8_5 * h_rotated[0, 2, 2, 2]
        self.q41s = constants.rt_8_5 * h_rotated[1, 2, 2, 2]
        self.q42c = (
            2
            * constants.rt_1_5
            * (h_rotated[0, 0, 2, 2] - h_rotated[1, 1, 2, 2])
        )
        self.q42s = 4 * constants.rt_1_5 * h_rotated[0, 1, 2, 2]
        self.q43c = (
            2
            * constants.rt_2_35
            * (h_rotated[0, 0, 0, 2] - 3 * h_rotated[0, 1, 1, 2])
        )
        self.q43s = (
            2
            * constants.rt_2_35
            * (3 * h_rotated[0, 0, 1, 2] - h_rotated[1, 1, 1, 2])
        )
        self.q44c = constants.rt_1_35 * (
            h_rotated[0, 0, 0, 0]
            - 6 * h_rotated[0, 0, 1, 1]
            + h_rotated[1, 1, 1, 1]
        )
        self.q44s = (
            4
            * constants.rt_1_35
            * (h_rotated[0, 0, 0, 1] - h_rotated[0, 1, 1, 1])
        )

    @buildermethod
    def read_json(self):
        """A json file is used to contain only the information needed to make the multipole moments. After reading a .int file for the first time,
        the original .int file from AIMALL is renamed to *.int.bak, and the .int file is made into a json file which only contains the information
        that ICHOR needs for later steps. This speeds up reading times if the information from the .int file is needed again."""
        with open(self.path, "r") as f:
            int_data = json.load(f)
            self.integration_data = GeometryData(int_data["integration"])
            self.multipoles_data = GeometryData(int_data["multipoles"])
            self.iqa_data = GeometryData(int_data["iqa_data"])
            if "dispersion_data" in int_data.keys():
                self.dispersion_data = GeometryData(
                    int_data["dispersion_data"]
                )
            else:
                self.dispersion_data = GeometryData()

    @property
    def file_contents(self):
        return ["iqa", *constants.multipole_names]

    @property
    def backup_path(self):
        """The path to the renamed .int file which was made by AIMALL."""
        return self.path.parent / (self.path.name + ".bak")

    def backup_int(self):
        """Move the original .int file that was generated by AIMALL to its new path (renames it to *.int.bak)."""
        self.move(self.backup_path)

    def revert_backup(self):
        """Move the original .int file (which is now stored as *.int.bak) to its original path *.int"""
        if self.backup_path.exists():
            move(self.backup_path, self.path)

    def write_json(self):
        """Write the .int file in json format that only contains the important information that ICHOR needs for later steps. This speeds up reading times
        if the information needs to be accessed again."""
        int_data = {
            "integration": self.integration_data,
            "multipoles": self.multipoles_data,
            "iqa_data": self.iqa_data,
            "dispersion_data": self.dispersion_data or {},
        }

        with open(self.path, "w") as f:
            json.dump(int_data, f)

    @property
    def num(self):
        """Returns the atom index in the system. (1-index)"""
        return int(re.findall("\d+", self.atom)[0])

    @property
    def integration_error(self):
        """The integration error can tell you if a point has been decomposed into topological atoms correctly. A large integration error signals
        that the point might not be suitable for training as the AIMALL IQA/multipole moments might be inaccurate."""
        return self.integration_data["L"]

    @property
    def iqa(self):
        """Returns the IQA energy of the topological atom that was calculated for this topological atom (since 1 .int file is written for each topological atom)."""
        from ichor.qct import ADD_DISPERSION

        iqa = self.iqa_data["E_IQA(A)"]
        if ADD_DISPERSION():
            iqa += self.dispersion
        return iqa

    @property
    def e_intra(self):
        return self.iqa_data["E_IQA_Intra(A)"]

    def get_dispersion(self) -> Optional[float]:
        from ichor.files.pandora import PandoraDirectory

        pandora_path = self.path.parent.parent / PandoraDirectory.dirname
        if pandora_path.exists():
            pandora_dir = PandoraDirectory(pandora_path)
            if pandora_dir.morfi.mout.exists():
                interaction_energy = pandora_dir.morfi.mout[
                    self.atom
                ].interaction_energy
                self.dispersion_data["dispersion"] = interaction_energy
                self.write_json()
                return interaction_energy
            raise FileNotFoundError(
                f"Cannot find 'MorfiOutput' in {pandora_dir}"
            )
        raise FileNotFoundError(
            f"Cannot find 'PandoraDirectory' in {self.path.parent}"
        )

    @cached_property
    def dispersion(self):
        if (
            self.dispersion_data is not None
            and "dispersion" in self.dispersion_data.keys()
        ):
            return self.dispersion_data["dispersion"]
        try:
            return self.get_dispersion()
        except FileNotFoundError:
            raise AttributeError(
                f"'{self.path}' instance of '{self.__class__.__name__}' has no attribute 'dispersion'"
            )

    @property
    def iqa_dispersion(self):
        return self.iqa + self.dispersion

    @property
    def multipoles(self):
        """Returns a dictionary of the multipole moments that were calculated for this particular topological atom (since 1 .int file is written for each topological atom)."""
        multipoles = {
            multipole: self.multipoles_data[multipole]
            for multipole in constants.multipole_names
        }
        multipoles["q00"] = self.q  # replace charge with net charge
        return multipoles

    @property
    def q(self):
        """Returns the point charge (monopole moment) of the topological atom."""
        return self.integration_data["q"]

    @property
    def q00(self):
        """Returns the point charge (monopole moment) of the topological atom."""
        return self.q

    @property
    def dipole(self):
        """Returns the magnitude of the dipole moment of the topological atom."""
        return np.sqrt(sum([self.q10 ** 2, self.q11c ** 2, self.q11s ** 2]))

    def delete(self):
        """Delete the .int file from disk."""
        self.path.unlink()
