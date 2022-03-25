import json
import re
from pathlib import Path
from typing import Optional, Union

import numpy as np

from ichor import constants, patterns
from ichor.common.functools import (buildermethod, cached_property,
                                    classproperty)
from ichor.files.file import File, FileContents
from ichor.files.geometry import GeometryData, GeometryDataFile
from ichor.multipoles import (rotate_dipole, rotate_hexadecapole,
                              rotate_octupole, rotate_quadrupole)


class INT(GeometryDataFile):
    """Wraps around one .int file which is generated by AIMALL for every atom in the system.

    :param path: The Path object corresponding to an .int file
    :param parent: An `Atoms` instance which holds the coordinate information for all atoms in the system.
        This information is needed to form the C matrix when rotating multipoles from the global to the local frame.
    """

    def __init__(self, path: Union[Path, str], parent=None):
        super().__init__(path)
        self.parent = parent
        self.integration_data = FileContents
        self.iqa_data = FileContents
        self.dispersion_data = FileContents
        self.rotated_multipoles_data = FileContents
        self.original_multipoles_data = FileContents

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of AIMALL files which are used"""
        return ".int"

    @classproperty
    def summarized_filetype(cls) -> str:
        """Returns the file extension of json-like files which contain the rotated data from .int files.
        This rotation moves from global Cartesian (given by AIMAll) to local coordinates (based on ALF of atom)."""
        return ".json"

    @buildermethod
    def _read_file(self):
        """Read an .int file. The first time that the .int file is read successfully, a json file with the
        important information is written in the same directory.
        """
        if self.json_path.exists():
            self.read_json()
        else:
            self.read_int()
            self.write_json()

    @property
    def atom_name(self) -> str:
        """Returns the name of the atom, including its index in the molecule. Eg. C1, H2, O3, etc."""
        return self.path.stem.upper()

    @property
    def atom_num(self):
        """Returns the atom index in the system. (atom indices in atom names start at 1)"""
        return int(re.findall("\d+", self.atom_name)[0])

    @property
    def json_path(self) -> Path:
        """ Returns a Path object corresponding to the json file"""
        return self.path.with_suffix(self.summarized_filetype) 

    @property
    def file_contents(self):
        """A list of strings that this class should have accessible as attributes"""
        original_multipole_names = [f"original_{multipole_name}" for multipole_name in constants.multipole_names]
        rotated_multipole_names = [f"rotated_{multipole_name}" for multipole_name in constants.multipole_names]
        return ["iqa"] + original_multipole_names + rotated_multipole_names

    @property
    def integration_error(self):
        """The integration error can tell you if a point has been decomposed into topological atoms correctly. A large integration error signals
        that the point might not be suitable for training as the AIMALL IQA/multipole moments might be inaccurate."""
        return self.integration_data["L"]

    @property
    def iqa(self):
        """Returns the IQA energy of the topological atom that was calculated for this topological atom (since 1 .int file is written for each topological atom)."""
        # TODO: remove the ADD_DISPERSION. This class should only be used to parse .int files and
        # processing the data should be done somewhere else.
        from ichor.qct import ADD_DISPERSION

        iqa = self.iqa_data["E_IQA(A)"]
        if ADD_DISPERSION():
            iqa += self.dispersion
        return iqa

    @property
    def e_intra(self):
        return self.iqa_data["E_IQA_Intra(A)"]

    @property
    def iqa_dispersion(self):
        # TODO: If using dispersion as well, this will be wrong because IQA will have dispersion added already.
        return self.iqa + self.dispersion

    @property
    def q(self):
        """Returns the point charge (monopole moment) of the topological atom."""
        # replace charge with net charge. The Q00 value written in AIMAll does not subtract the nuclear charge.
        return self.original_multipoles_data["q00"]

    @property
    def q00(self):
        """Returns the point charge (monopole moment) of the topological atom."""
        # replace charge with net charge. The Q00 value written in AIMAll does not subtract the nuclear charge.
        return self.q

    @property
    def dipole(self):
        """Returns the magnitude of the dipole moment of the topological atom.
        The magnitude of the vector is not affected by the rotation of multipoles."""
        return np.sqrt(sum([self.original_q10 ** 2, self.original_q11c ** 2, self.original_q11s ** 2]))

    @buildermethod
    def read_int(self):
        """Method used to parse the AIMAll '.int' file"""

        self.integration_data = GeometryData()
        self.iqa_data = GeometryData()
        self.original_multipoles_data = GeometryData()

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
                                # q00 (net charge, with charge of nucleus included) is written here
                                if "q" == tokens[0].strip():
                                    self.original_multipoles_data["q00"] = float(tokens[-1])
                                else:
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
                
                All multipoles are parsed, even though only up to hexadecapoles are used by ichor
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
                                ).lower()
                                # DO NOT read in q00 because the Q[0,0] does not take into account the nuclear charge, but we need that
                                if multipole != "q00":
                                    self.original_multipoles_data[
                                    "original_" + multipole] = float(tokens[-1])
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

        # rotate multipoles after, so that we also store rotated multipoles
        if self.parent:
            self.rotate_multipoles()

    def write_json(self):
        """Write a file in json format that only contains the important information that ICHOR needs for later steps. This speeds up reading times
        if the information needs to be accessed again.

        .. note::
            This method is used to write out both json files (one with rotated and one with original
            non-rotated multipole data). The original json data is written right after
            the original .int file is read in, the rotated 
        """
        # this is the only data that should be written if a parent does not exist
        int_data = {
            "integration": self.integration_data,
            "iqa_data": self.iqa_data,
            "original_multipoles": self.original_multipoles_data,
        }
        # data that can be optionally added if a parent does exist or dispersion data exists
        if self.rotated_multipoles_data:
            int_data["rotated_multipoles"] = self.rotated_multipoles_data
        if self.dispersion_data:
            int_data["dispersion_data"] = self.dispersion_data

        with open(self.json_path, "w") as f:
            json.dump(int_data, f)

    @buildermethod
    def read_json(self):
        """A json file is used to contain only the information needed to make the multipole moments. After reading a .int file for the first time,
        the original .int file from AIMALL is renamed to *.int.bak, and the .int file is made into a json file which only contains the information
        that ICHOR needs for later steps. This speeds up reading times if the information from the .int file is needed again."""
        with open(self.json_path, "r") as f:
            int_data = json.load(f)
            self.integration_data = GeometryData(int_data.get("integration")) if int_data.get("integration") else FileContents
            self.rotated_multipoles_data = GeometryData(int_data.get("rotated_multipoles")) if int_data.get("rotated_multipoles") else FileContents
            self.original_multipoles_data = GeometryData(int_data.get("original_multipoles")) if int_data.get("integration") else FileContents
            self.iqa_data = GeometryData(int_data.get("iqa_data")) if int_data.get("iqa_data") else FileContents
            self.dispersion_data = GeometryData(int_data.get("dispersion_data")) if int_data.get("dispersion_data") else FileContents

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
        self.rotated_multipoles_data = GeometryData()
        self.rotate_dipole()
        self.rotate_quadrupole()
        self.rotate_octupole()
        self.rotate_hexadecapole()
        # technically don't need to add that here because it is not rotated
        # but add it just in case someone wants all the rotated multipoles (including q00)
        self.rotated_multipoles_data["q00"] = self.q00

    @property
    def C(self):
        """ Returns the C rotation matrix calculated for the atom. See the class Atom C method."""

        atom_inst = self.parent.atoms[self.atom_name]
        return atom_inst.C

    # monopole moments (point charges) do not need to be rotated because they are symmetric

    def rotate_dipole(self):
        """Rotates dipole moment from global cartesian to local cartesian. Attributes like self.q11c, self.q11s, etc. are not
        explicitly defined here, but they can be accessed because of the GeometryData __getattr__ implementation, which allows
        accessing dictionary keys as if they were attributes."""
        self.rotated_multipoles_data["rotated_q10"], 
        self.rotated_multipoles_data["rotated_q11c"],
        self.rotated_multipoles_data["rotated_q11s"] = rotate_dipole(
            self.original_q10, self.original_q11c, self.original_q11s, self.C
        )

    def rotate_quadrupole(self):
        """Rotates quadrupole moments from the global to local frame"""
        (
            self.rotated_multipoles_data["rotated_q20"],
            self.rotated_multipoles_data["rotated_q21c"],
            self.rotated_multipoles_data["rotated_q21s"],
            self.rotated_multipoles_data["rotated_q22c"],
            self.rotated_multipoles_data["rotated_q22s"],
        ) = rotate_quadrupole(
            self.original_q20, self.original_q21c, self.original_q21s, self.original_q22c, self.original_q22s, self.C
        )

    def rotate_octupole(self):
        """Rotates octupole moments from the global to local frame"""
        (
            self.rotated_multipoles_data["rotated_q30"],
            self.rotated_multipoles_data["rotated_q31c"],
            self.rotated_multipoles_data["rotated_q31s"],
            self.rotated_multipoles_data["rotated_q32c"],
            self.rotated_multipoles_data["rotated_q32s"],
            self.rotated_multipoles_data["rotated_q33c"],
            self.rotated_multipoles_data["rotated_q33s"],
        ) = rotate_octupole(
            self.original_q30,
            self.original_q31c,
            self.original_q31s,
            self.original_q32c,
            self.original_q32s,
            self.original_q33c,
            self.original_q33s,
            self.C,
        )

    def rotate_hexadecapole(self):
        """Rotates hexadecapole moments from the global to local frame"""
        (
            self.rotated_multipoles_data["rotated_q40"],
            self.rotated_multipoles_data["rotated_q41c"],
            self.rotated_multipoles_data["rotated_q41s"],
            self.rotated_multipoles_data["rotated_q42c"],
            self.rotated_multipoles_data["rotated_q42s"],
            self.rotated_multipoles_data["rotated_q43c"],
            self.rotated_multipoles_data["rotated_q43s"],
            self.rotated_multipoles_data["rotated_q44c"],
            self.rotated_multipoles_data["rotated_q44s"],
        ) = rotate_hexadecapole(
            self.original_q40,
            self.original_q41c,
            self.original_q41s,
            self.original_q42c,
            self.original_q42s,
            self.original_q43c,
            self.original_q43s,
            self.original_q44c,
            self.original_q44s,
            self.C,
        )

    def get_dispersion(self) -> Optional[float]:
        # TODO: THIS DOES NOT NEED TO BE HERE because the pandora directory might not exist. NEED TO PASS in a path from where to get dispersion will be the proper library implementation.
        from ichor.files.pandora import PandoraDirectory

        self.dispersion_data = GeometryData()

        pandora_path = self.path.parent.parent / PandoraDirectory.dirname
        if pandora_path.exists():
            pandora_dir = PandoraDirectory(pandora_path)
            if pandora_dir.morfi.mout.exists():
                interaction_energy = pandora_dir.morfi.mout[
                    self.atom_name
                ].interaction_energy
                self.dispersion_data["dispersion"] = interaction_energy
                self.write_json(self.json_path)
                return interaction_energy
            raise FileNotFoundError(
                f"Cannot find 'MorfiOutput' in {pandora_dir}"
            )
        raise FileNotFoundError(
            f"Cannot find 'PandoraDirectory' in {self.path.parent}"
        )

    @cached_property
    def dispersion(self):
        # TODO: Move this to a different class. Dispersion is not in original .int files and
        # should not be addressed in this class.
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