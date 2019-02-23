#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import logging
from pathlib import Path
import re
from typing import List, Union
import numpy as np

from openspectra.image import RGBImage, GreyscaleImage
from openspectra.utils import LogHelper, Logger


class OpenSpectraHeader:
    """A class that reads, validates and makes open spectra header file details available"""

    __LOG:Logger = LogHelper.logger("OpenSpectraHeader")

    __BAND_NAMES = "band names"
    __BANDS = "bands"
    __DATA_TYPE = "data type"
    __HEADER_OFFSET = "header offset"
    __INTERLEAVE = "interleave"
    __LINES = "lines"
    __REFLECTANCE_SCALE_FACTOR = "reflectance scale factor"
    __SAMPLES = "samples"
    __WAVELENGTHS = "wavelength"

    __DATA_TYPE_DIC = {'1': np.uint8,
                       '2': np.int16,
                       '3': np.int32,
                       '4': np.float32,
                       '5': np.float64,
                       '6': np.complex64,
                       '9': np.complex128,
                       '12': np.uint16,
                       '13': np.uint32,
                       '14': np.int64,
                       '15': np.uint64}

    def __init__(self, file_name):
        self.__path = Path(file_name)
        self.__props = dict()

    def dump(self) -> str:
        return "Props:\n" + str(self.__props)

    def load(self):
        OpenSpectraHeader.__LOG.debug("File: {0} exists: {1}", self.__path.name, self.__path.exists())

        if self.__path.exists() and self.__path.is_file():
            OpenSpectraHeader.__LOG.info("Opening file {0} with mode {1}", self.__path.name, self.__path.stat().st_mode)

            with self.__path.open() as headerFile:
                for line in headerFile:
                    line = line.rstrip()
                    # TODO any validation that needs to be done first??

                    if re.search("=", line) is not None:
                        line_pair: List[str] = re.split("=", line)
                        if len(line_pair) == 2:
                            key = line_pair[0].strip()
                            value = line_pair[1].lstrip()
                            if re.search("{", value):
                                self.__read_bracket(key, value, headerFile)
                            else:
                                self.__props[key] = value

                        else:
                            # raise OpenSpectraHeaderError("Invalid format, found more than one '=' on a line")
                            # TODO need to support lines like,
                            # map info = {UTM, 1.000, 1.000, 620006.407, 2376995.930, 7.8000000000e+000, 7.8000000000e+000, 4, North, WGS-84, units=Meters, rotation=29.00000000}
                            OpenSpectraHeader.__LOG.warning("Encountered line with more than one '=', I'm not "
                                "smart enough to handle that yet! Ignoring it for now.  Line is:\n {0}", line)

            # now verify what we read makes sense and do some conversion to data type we want
            self.__validate()

        else:
            raise OpenSpectraHeaderError("File {0} not found".format(self.__path.name))

    def band_label(self, band:int) -> tuple:
        """Returns a tuple where that contains two strings,
        the band name and wavelength """
        return self.__band_labels[band]

    def band_labels(self) -> list:
        """Returns a list of tuples where each tuple is contains two strings,
        the band name and wavelength """
        return self.__band_labels

    def band_name(self, band:int) -> str:
        """Returns the band name for the given band index"""
        return self.__props.get(OpenSpectraHeader.__BAND_NAMES)[band]

    def band_names(self) -> list:
        """Returns a list of strings of the band names"""
        return self.__props.get(OpenSpectraHeader.__BAND_NAMES)

    def data_type(self):
        data_type = self.__props.get(OpenSpectraHeader.__DATA_TYPE)
        return self.__DATA_TYPE_DIC.get(data_type)

    def samples(self) -> int:
        return self.__samples

    def lines(self) -> int:
        return self.__lines

    def band_count(self) -> int:
        return self.__bands

    def wavelengths(self):
        return self.__wavelengths

    def interleave(self):
        return self.__props.get(OpenSpectraHeader.__INTERLEAVE)

    def header_offset(self):
        return self.__header_offset

    def reflectance_scale_factor(self):
        return self.__reflectance_scale_factor

    def __read_bracket(self, key, value, header_file):
        done = False
        line = value.strip("{").strip()
        list_value = list()

        # check for closing } on same line
        if re.search("}", line):
            line = line.strip("}").strip()
            done = True

        # if there are any entries on the first line handle them
        if line:
            elements = line.split(",")
            if len(elements) > 0:
                list_value = elements

        if not done:
            section = ""
            for line in header_file:
                section += line.rstrip()
                if re.search("}", line):
                    section = section.rstrip("}").rstrip()
                    break

            list_value += section.split(",")

        map(str.strip, list_value)
        self.__props[key] = list_value

    def __validate(self):
        self.__samples = int(self.__props[OpenSpectraHeader.__SAMPLES])
        self.__lines = int(self.__props[OpenSpectraHeader.__LINES])
        self.__bands = int(self.__props[OpenSpectraHeader.__BANDS])

        if self.__samples is None or self.__samples <= 0:
            raise OpenSpectraHeaderError("Value for 'samples' in header is not valid: {0}"
                .format(self.__samples))

        if self.__lines is None or self.__lines <= 0:
            raise OpenSpectraHeaderError("Value for 'lines' in header is not valid: {0}"
                .format(self.__lines))

        if self.__bands is None or self.__bands <= 0:
            raise OpenSpectraHeaderError("Value for 'bands' in header is not valid: {0}"
                .format(self.__bands))

        band_names = self.__props.get(OpenSpectraHeader.__BAND_NAMES)
        wavelengths_str = self.__props.get(OpenSpectraHeader.__WAVELENGTHS)

        # possible to have only bands or wavelenghts or both or neither
        if band_names is None:
            band_names = ["Band " + index for index in np.arange(
                1, self.__bands + 1, 1, np.int16).astype(str)]
        else:
            if len(band_names) != self.__bands:
                raise OpenSpectraHeaderError(
                    "Number of 'band names' {0} does not match number of bands {1}".
                        format(len(band_names), self.__bands))

        if wavelengths_str is None:
            wavelengths_str = np.arange(
                1, self.__bands + 1, 1, np.float64).astype(str)
        else:
            if len(wavelengths_str) != self.__bands:
                raise OpenSpectraHeaderError(
                    "Number of wavelengths {0} does not match number of bands {1}".
                        format(len(wavelengths_str), self.__bands))

        self.__wavelengths = np.array(wavelengths_str, np.float64)
        self.__band_labels = list(zip(band_names, wavelengths_str))

        self.__header_offset = int(self.__props[OpenSpectraHeader.__HEADER_OFFSET])
        # TODO missing sometimes??
        if OpenSpectraHeader.__REFLECTANCE_SCALE_FACTOR in self.__props:
            self.__reflectance_scale_factor = np.float64(
                self.__props[OpenSpectraHeader.__REFLECTANCE_SCALE_FACTOR])

        # TODO data_type - make sure we recognize and support?
        # TODO interleave - make sure we recognize and support?
        # TODO byte_order - make sure we recognize and support?
        # TODO additional validation????


class Shape():

    def __init__(self, x, y, z):
        self.__shape = (x, y, z)
        self.__size = x * y * z

    def shape(self) -> (int, int, int):
        return self.__shape

    def size(self) -> int:
        return self.__size

    def lines(self) -> int:
        pass

    def samples(self) -> int:
        pass

    def bands(self) -> int:
        pass


class BILShape(Shape):

    def __init__(self, lines, samples, bands):
        super().__init__(lines, bands, samples)

    def lines(self) -> int:
        return self.shape()[0]

    def samples(self) -> int:
        return self.shape()[2]

    def bands(self) -> int:
        return self.shape()[1]


class BQSShape(Shape):

    def __init__(self, lines, samples, bands):
        super().__init__(bands, lines, samples)

    def lines(self) -> int:
        return self.shape()[1]

    def samples(self) -> int:
        return self.shape()[2]

    def bands(self) -> int:
        return self.shape()[0]


class BIPShape(Shape):

    def __init__(self, lines, samples, bands):
        super().__init__(lines, samples, bands)

    def lines(self) -> int:
        return self.shape()[0]

    def samples(self) -> int:
        return self.shape()[1]

    def bands(self) -> int:
        return self.shape()[2]


class FileModel():

    def __init__(self, path:Path, header:OpenSpectraHeader):
        self._file: np.ndarray = None
        self._path = path

        # size in bytes of each data element in the file
        self._data_type = np.dtype(header.data_type())

        # TODO set based on byte_order from header but doesn't seem to make a difference
        self._data_type.newbyteorder("L")
        # data_type.newbyteorder("B")

    def load(self, shape:Shape):
        pass

    def file(self) -> np.ndarray:
        return self._file

    def name(self):
        return self._path.name

    def data_type(self):
        return self._file.dtype

    def _validate(self, shape:Shape):
        if self._file.size != shape.size():
            raise OpenSpectraFileError("Expected {0} data points but found {1}".
                format(shape.size(), self._file.size))


class FileTypeDelegate():

    def __init__(self, shape:Shape, file_model:FileModel):
        self.__shape = shape
        self._file_model = file_model

    def image(self, band:Union[int, tuple]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        pass

    def bands(self, line:Union[int, tuple, np.ndarray], sample:Union[int, tuple, np.ndarray]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple or ndarray returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        pass

    def shape(self) -> Shape:
        return self.__shape


class BILFileDelegate(FileTypeDelegate):
    """An 'interleave': 'bil' file"""

    def __init__(self, header:OpenSpectraHeader, file_model:FileModel):
        # inspect header info to make sure it's what we expect
        if header.interleave() != "bil":
            raise OpenSpectraFileError("Expected a file with interleave type 'bil' got {0}".
                format(header.interleave()))

        super().__init__(
            BILShape(header.lines(), header.samples(), header.band_count()), file_model)

    def image(self, band:Union[int, tuple]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        return self._file_model.file()[:, band, :]

    def bands(self, line:Union[int, tuple, np.ndarray], sample:Union[int, tuple, np.ndarray]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple or ndarray returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        return self._file_model.file()[line, :, sample]


class BQSFileDelegate(FileTypeDelegate):
    """An 'interleave': 'bsq' file"""

    def __init__(self, header:OpenSpectraHeader, file_model:FileModel):
        # inspect header info to make sure it's what we expect
        if header.interleave() != "bsq":
            raise OpenSpectraFileError("Expected a file with interleave type 'bsq' got {0}".
                format(header.interleave()))

        super().__init__(
            BQSShape(header.lines(), header.samples(), header.band_count()), file_model)

    def image(self, band:Union[int, tuple]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        return self._file_model.file()[band, :, :]

    def bands(self, line:Union[int, tuple, np.ndarray], sample:Union[int, tuple, np.ndarray]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple or ndarray returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        return self._file_model.file()[:, line, sample]


class BIPFileDelegate(FileTypeDelegate):
    """An 'interleave': 'bip' file"""

    def __init__(self, header:OpenSpectraHeader, file_model:FileModel):
        # inspect header info to make sure it's what we expect
        if header.interleave() != "bip":
            raise OpenSpectraFileError("Expected a file with interleave type 'bip' got {0}".
                format(header.interleave()))

        super().__init__(
            BIPShape(header.lines(), header.samples(), header.band_count()), file_model)

    def image(self, band:Union[int, tuple]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        return self._file_model.file()[:, :, band]

    def bands(self, line:Union[int, tuple, np.ndarray], sample:Union[int, tuple, np.ndarray]) -> np.ndarray:
        """It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple or ndarray returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        return self._file_model.file()[line, sample, :]


class MemoryModel(FileModel):

    def __init__(self, path:Path, header: OpenSpectraHeader):
        super().__init__(path, header)

    def load(self, shape:Shape):
        self._file = np.array([], self._data_type)
        with self._path.open("rb") as file:
            bytes_in = file.read()
            while bytes_in:
                self._file = np.append(self._file, np.frombuffer(bytes_in, self._data_type))
                bytes_in = file.read()

        self._validate(shape)
        self._file = self._file.reshape(shape.shape())


class MappedModel(FileModel):

    def __init__(self, path:Path, header: OpenSpectraHeader):
        super().__init__(path, header)

    def load(self, shape:Shape):
        self._file = np.memmap(self._path, dtype = self._data_type, mode = 'r',
            shape = shape.shape())
        self._validate(shape)


class OpenSpectraFile:

    __LOG:Logger = LogHelper.logger("OpenSpectraFile")

    def __init__(self, header:OpenSpectraHeader, file_delegate:FileTypeDelegate,
            memory_model:FileModel):
        # self.__path = Path(file_name)
        # self.header.load()
        # TODO later we'll pass these in from a factory function?
        # self.__memory_model = MemoryModel(self.header)

        self.__header = header
        self.__memory_model = memory_model
        self.__file_delegate = file_delegate
        self.__validate()

        if OpenSpectraFile.__LOG.isEnabledFor(logging.DEBUG):
            # TODO seems a little weird, maybe the file delegate should provide access to the file?
            # TODO so how far do we want to go with the delegate, expose file?  Only expose file props/methods?
            OpenSpectraFile.__LOG.debug("Shape: {0}", self.__memory_model.file().shape)
            OpenSpectraFile.__LOG.debug("NDim: {0}", self.__memory_model.file().ndim)
            OpenSpectraFile.__LOG.debug("Size: {0}", self.__memory_model.file().size)
            OpenSpectraFile.__LOG.debug("Type: {0}", self.__memory_model.file().dtype)

            # TODO so this causes performance problems on large file even with memory mapped, probably has to read the whole file
            # TODO doesn't consume a bunch of memory in the end.
            # OpenSpectraFile.__LOG.debug("Min: {0}, Max: {1}", self.__memory_model.file().min(), self.__memory_model.file().max())

        # TODO this causes all memory to get used up then released and takes a long time but works when copy=False
        # TODO doesn't seem to recover at all if copy=True
        # view = np.ma.masked_invalid(self.__memory_model.file(), False)
        # view = np.ma.masked_outside(view, -1, 1, False)
        # OpenSpectraFile.__LOG.debug("Filtered Min: {0}, Max: {1}, Size: {2}", view.min(), view.max(), view[~view.mask].size)

    def raw_image(self, band:Union[int, tuple]) -> np.ndarray:
        """Return the image data for the given band.
        It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        return self.__file_delegate.image(band)

    def bands(self, line:Union[int, tuple, np.ndarray], sample:Union[int, tuple, np.ndarray]) -> np.ndarray:
        """Return all of the band values for a given pixel.
        It's important to understand that selecting images with an int index
        returns a view of the underlying data while using a tuple or ndarray returns a copy.
        See https://docs.scipy.org/doc/numpy-1.16.0/user/basics.indexing.html
        for more details"""
        self.__validate_band_args(line, sample)
        return self.__file_delegate.bands(line, sample)

    def name(self) -> str:
        return self.__memory_model.name()

    def header(self) -> OpenSpectraHeader:
        return self.__header

    def __validate(self):
        if self.__memory_model.data_type() != self.__header.data_type():
            raise TypeError("Header file type {0}, does not match actually data type {1}",
                self.__header.data_type(), self.__memory_model.data_type())

    def __validate_band_args(self, line:Union[int, tuple, np.ndarray], sample:Union[int, tuple, np.ndarray]):
        if isinstance(line, int) and isinstance(sample, int):
            pass
        elif isinstance(line, tuple) and isinstance(sample, tuple):
            if len(line) != len(sample):
                raise ValueError("tuple arguments must have the same length")

        elif isinstance(line, np.ndarray) and isinstance(sample, np.ndarray):
            if line.ndim != 1 or sample.ndim != 1:
                raise ValueError("ndarray arguments must have a dimension of 1")

            if line.size != sample.size:
                raise ValueError("ndarray arguments must have the same size")

        else:
            raise TypeError("'line' and 'sample' arguments must have the same type")


class OpenSpectraFileFactory:
    """An object oriented way to create an OpenSpectra file"""

    __LOG: logging.Logger = LogHelper.logger("OpenSpectraFileFactory")

    @staticmethod
    def create_open_spectra_file(file_name) -> OpenSpectraFile:
        path = Path(file_name)

        if path.exists() and path.is_file():
            OpenSpectraFileFactory.__LOG.info("Opening {0} with mode {1}", path.name, path.stat().st_mode)

            header = OpenSpectraHeader(file_name + ".hdr")
            header.load()
            file_type = header.interleave()

            # TODO logic to choose a memory model
            memory_model:FileModel = MappedModel(path, header)

            if file_type == "bil":
                file_delegate = BILFileDelegate(header, memory_model)
            elif file_type == 'bsq':
                file_delegate = BQSFileDelegate(header, memory_model)
            elif file_type == 'bip':
                file_delegate = BIPFileDelegate(header, memory_model)
            else:
                raise OpenSpectraHeaderError("Unexpected file type: {0}".format(file_type))

            # TODO this is kind of weird
            memory_model.load(file_delegate.shape())
            return OpenSpectraFile(header, file_delegate, memory_model)

        else:
            raise OpenSpectraFileError("File {0} not found".format(path))


def create_open_spectra_file(file_name) -> OpenSpectraFile:
    """A function based way to create an OpenSpectra file"""

    return OpenSpectraFileFactory.create_open_spectra_file(file_name)


class OpenSpectraHeaderError(Exception):
    """Raised when there's a problem with the header file"""
    pass


class OpenSpectraFileError(Exception):
    """Raised when there's a problem with the data file"""
    pass

