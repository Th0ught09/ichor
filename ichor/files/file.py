import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from ichor.common.functools import (buildermethod, classproperty)
from ichor.common.io import move
from ichor.common.obj import (object_getattribute)
from ichor.files.path_object import PathObject


class FileReadError(Exception):
    pass


class FileState(Enum):
    """An enum that is used to make it easier to check the current file state.
    Blocked is actually not used currently."""

    Unread = 1
    Reading = 2
    Read = 3
    Blocked = -1


class FileContentsType:
    pass

    def __bool__(self):
        return False


FileContents = FileContentsType()


class File(PathObject, ABC):
    """Abstract Base Class for any type of file that is used by ICHOR."""

    state: FileState = FileState.Unread
    _contents: List[str] = []

    def __init__(self, path: Optional[Union[Path, str]] = None):
        # if path is not None, then we initialize super to check if path exists
        if path is not None:
            super().__init__(path)
            self.state = FileState.Unread
            self._contents = []
        # if path is none, then we assume there is nothing to be read in.
        # therefore, the data passed in the init method will be used to construct the file
        # and used later if the file is being written out.
        else:
            self.state = FileState.Read

            

    @buildermethod
    def read(self, *args, **kwargs) -> None:
        """Read the contents of the file. Depending on the type of file, different parts will be read in."""
        if self.path.exists() and self.state is FileState.Unread:
            for var, inst in vars(self).items():
                if inst is FileContents:
                    self._contents.append(var)
            self.state = FileState.Reading
            self._read_file(
                *args, **kwargs
            )  # self._read_file is different based on which type of file is being read (GJF, AIMALL, etc.)
            self.state = FileState.Read

    @abstractmethod
    def _read_file(self, *args, **kwargs):
        """ Abstract method detailing how to read contents of a file. Every type of file (gjf, int, etc.)
        is written in a different format and contains different information, so every file reading is
        different."""
        pass

    def dump(self):
        """ Sets all attributes in self._contents to FileContents. self._contents
        is a list of strings corresponding to attributes which are initially of type
        FileContents (and are changed when a file is read). This method essentially resets
        an instance to the time where the file associated with the instance is not read in yet
        and no data has been stored. Also resets the state to FileState.Unread ."""
        for var in self._contents:
            setattr(self, var, FileContents)
        self.state = FileState.Unread

    @classproperty
    @abstractmethod
    def filetype(self) -> str:
        """ Abstract class property which returns the suffix associated with the filetype.
        For example, for GJF class, this will return `.gjf`"""
        pass

    @property
    def _file_contents(self):
        return list(dir(self)) + self.file_contents

    @property
    def file_contents(self) -> List[str]:
        return []

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """ Checks the suffix of the given path matches the filetype associated with class that subclasses from File
        :param path: A Path object to check
        :return: True if the Path object has the same suffix as the class filetype, False otherwise
        """
        return path.suffix == cls.filetype

    def move(self, dst) -> None:
        """Move the file to a new destination.

        :param dst: The new path to the file. If a directory, the file is moved inside the directory.
        """
        if dst.is_dir():
            dst /= self.path.name
        move(self.path, dst)

    def write(self, path: Optional[Path] = None):
        """ This write method should only be called if no other write method exists. A
        write method is implemented for files that we typically write out (such as 
        .xyz or .gjf files). But other files (which are outputs of a program, such as .wfn,
        and .int), we only need to read and do not have to write out ourselves."""
        raise NotImplementedError(
            f"'write' method not implemented for {self.__class__.__name__}"
        )

    @contextmanager
    def block(self):
        """ Blocks a file from being read. Contents of the file cannot be read."""
        self._save_state = self.state
        try:
            self.state = FileState.Blocked
            yield
        finally:
            self.unblock()

    def unblock(self):
        """ Unblocks a blocked file."""
        if self.state is FileState.Blocked:
            self.state = self._save_state

    def __getattribute__(self, item):
        """This is what gets called when accessing an attribute of an instance. Here, we check if the attribute exists or not.
        If the attribute does not exist, then read the file and update its filestate. Then try to return the value of the attribute, if
        the attribute still does not exist after reading the file, then return an AttributeError.

        One must be careful to make sure all attributes that want to be accessed lazily must be an attribute of the class and
        not to override __getattribute__ in subclasses of PathObject.

        :param item: The attribute that needs to be accessed.
        """

        # check if the attribute has value FileContents, if not read file
        try:
            if super().__getattribute__(item) is FileContents:
                self.read()
        except AttributeError:  # todo: see if we can get rid of the need for this as can cause issues if there is truly an AttributeError in self.read()
            if item in self._file_contents:
                self.read()

        # now that the file is read, return the attribute that should exist now
        try:
            return super().__getattribute__(item)
        except AttributeError:
            raise AttributeError(
                f"{object_getattribute(self, 'path')} instance of {object_getattribute(self, '__class__').__name__} has no attribute {item}"
            )

    def __getitem__(self, item):
        """Tries to return the item indexed with [] brackets. If the item does not exist and the filestate is Unread, then
        read the file and try to access the item again. If the item still does not exist, then throw a KeyError."""
        try:
            return super().__getitem__(item)
        except KeyError:
            if self.state is FileState.Unread:
                self.read()
                return self.__getitem__(item)
        raise KeyError(f"No '{item}' item found for '{self.path}'")
