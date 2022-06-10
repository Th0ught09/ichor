from pathlib import Path
from typing import Union

from ichor.core.atoms import AtomsNotFoundError
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.file import FileContents
from ichor.core.files.geometry import AtomData, GeometryDataFile, GeometryFile
from ichor.core.files.gjf import GJF
from ichor.core.files.ints import INTs
from ichor.core.files.optional_file import OptionalFile, OptionalPath
from ichor.core.files.pandora import PandoraDirectory, PandoraInput
from ichor.core.files.wfn import WFN
from ichor.core.files.xyz import XYZ


class PointDirectory(GeometryFile, GeometryDataFile, AnnotatedDirectory):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.

    Attributes:
        cls.gjf Optional[GJF]: Used when iterating over __annotations__
        cls.wfn Optional[WFN]: Used when iterating over __annotations__
        cls.ints Optional[INTs]: Used when iterating over __annotations__
    """

    xyz: OptionalPath[XYZ] = OptionalFile
    gjf: OptionalPath[GJF] = OptionalFile
    wfn: OptionalPath[WFN] = OptionalFile
    ints: OptionalPath[INTs] = OptionalFile
    pandora_input: OptionalPath[PandoraInput] = OptionalFile
    pandora: OptionalPath[PandoraDirectory] = OptionalFile

    def __init__(self, path: Union[Path, str]):
        GeometryFile.__init__(self, path, atoms=FileContents)
        GeometryDataFile.__init__(self, path)
        AnnotatedDirectory.__init__(self, path)

    def _read_file(self, *args, **kwargs):
        for file in self.files():
            file._read_file(*args, **kwargs)
        for directory in self.directories():
            directory._read_file(*args, **kwargs)

    def _parse(self):
        super()._parse()  # call AnnotatedDirectory.parse method
        if not self.xyz:
            for f in self.files():
                if isinstance(f, GeometryFile):
                    self.xyz = XYZ(
                        Path(self.path) / (self.path.name + XYZ.filetype),
                        atoms=f.atoms,
                    )
        for p in self.path_objects():
            if hasattr(p, "parent"):
                p.parent = self

    @property
    def atoms(self):
        """Returns the `Atoms` instance which the `PointDirectory` encapsulates."""
        # always try to get atoms from wfn file first because the wfn file contains the final geometry.
        # you can run into the issue where you did an optimization (so .xyz/gjf are different from wfn)
        # then predictions - true will be way off because you are predicting on different geometries
        for f in self.files():
            if isinstance(f, WFN):
                return f.atoms
        for f in self.files():
            if isinstance(f, GeometryFile):
                return f.atoms
        raise AtomsNotFoundError(f"'atoms' not found for point '{self.path}'")

    @atoms.setter
    def atoms(self, value):
        if value is not FileContents:
            if not self.xyz.exists():
                self.xyz = XYZ(self.path / f"{self.path.name}{XYZ.filetype}")
            self.xyz = XYZ(self.xyz.path, value)

    def get_atom_data(self, atom) -> AtomData:
        if self.ints.exists():
            try:
                return AtomData(self.atoms[atom], self.ints[atom])
            except KeyError:
                raise KeyError(
                    f"No atom '{atom}' found in '{self.__class__.__name__}' instance '{self.path}'"
                )
        else:
            return AtomData(self.atoms[atom])

    def get_property(self, item: str):
        return getattr(self.ints, item)

    def __getattr__(self, item):
        tried = []
        for d in self.directories():
            try:
                return getattr(d, item)
            except AttributeError:
                tried.append(d.path)
        for f in self.files():
            try:
                return getattr(f, item)
            except AttributeError:
                tried.append(f.path)

        raise AttributeError(
            f"'{self.path}' instance of '{self.__class__.__name__}' has no attribute '{item}', searched: '{tried}'"
        )

    def __repr__(self):
        return str(self.path)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_atom_data(item)
        return super().__getitem__(item)
