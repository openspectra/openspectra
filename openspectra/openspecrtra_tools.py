#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

from io import TextIOBase
from typing import Union, List, Tuple, Dict

import numpy as np
from numpy import ma

from openspectra.image import Image, GreyscaleImage, RGBImage, Band, BandDescriptor
from openspectra.openspectra_file import OpenSpectraFile, OpenSpectraHeader, LinearImageStretch, \
    MutableOpenSpectraHeader
from openspectra.utils import OpenSpectraDataTypes, OpenSpectraProperties, Logger, LogHelper


class RegionOfInterest:
    """A region of interest is an area on an image of a specific size.
    Note: all indexes are expected to be zero based."""

    def __init__(self, area:np.ndarray, x_zoom_factor:float, y_zoom_factor:float,
            image_height:int, image_width:int, descriptor:Union[BandDescriptor, Dict[Band, BandDescriptor]],
            display_name=None, map_info:OpenSpectraHeader.MapInfo=None):
        """area is basically a list of [x, y] pairs, that is the area should have a shape
        of (num pixels, 2)"""

        shape = area.shape
        if len(shape) != 2:
            raise ValueError("Parameter 'area' dimensions are not valid, expect a 2 dimensional array")

        if shape[1] != 2:
            raise ValueError(
                "Parameter 'area' dimensions are not valid, expect the second dimension of the array to be 2")

        # index to use when we're being iterated over
        self.__index = -1
        self.__display_name = display_name

        # TODO do I need to keep area?
        # self.__area = area

        # TODO need a way we can tie this region back to the original image?
        # TODO verify area is less than or equal to image size???
        self.__image_height = image_height
        self.__image_width = image_width

        self.__descriptor:BandDescriptor = descriptor

        if type(self.__descriptor) is dict:
            self.__description = descriptor[Band.RED].label() + ", "
            self.__description += descriptor[Band.GREEN].band_label() + ", "
            self.__description += descriptor[Band.BLUE].band_label()
        else:
            self.__description = self.__descriptor.label()

        # split the points back into x and y values and convert to 1 to 1 space and 0 based
        if x_zoom_factor != 1.0:
            self.__x_points = np.floor(area[:, 0] / x_zoom_factor).astype(np.int16)
        else:
            self.__x_points = area[:, 0]

        if y_zoom_factor != 1.0:
            self.__y_points = np.floor(area[:, 1] / y_zoom_factor).astype(np.int16)
        else:
            self.__y_points = area[:, 1]

        if self.__x_points.size != self.__y_points.size:
            raise ValueError("Number of x points doesn't match number of y points")

        # if we scaled down a zoomed in image we need to filter out duplicate points
        if x_zoom_factor > 1.0 or y_zoom_factor > 1.0:
            scaled_points = np.column_stack((self.__x_points, self.__y_points))
            scaled_points = np.unique(scaled_points, axis=0)
            self.__x_points = scaled_points[:, 0]
            self.__y_points = scaled_points[:, 1]

        # limit to use when we're being iterated over
        self.__iter_limit = self.__x_points.size - 1

        self.__x_coords = None
        self.__y_coords = None
        self.__map_info:OpenSpectraHeader.MapInfo = map_info
        self.__calculate_coords()

    def __iter__(self):
        # make sure index is at -1
        self.__index = -1
        return self

    def __next__(self):
        if self.__index >= self.__iter_limit:
            raise StopIteration
        else:
            self.__index += 1
            return self

    def __calculate_coords(self):
        if self.__map_info is not None:
            coordinates = self.__map_info.calculate_coordinates(self.__x_points, self.__y_points)
            self.__x_coords = coordinates[0]
            self.__y_coords = coordinates[1]

    def x_point(self) -> int:
        """get the x point while iterating"""
        return self.__x_points[self.__index]

    def y_point(self) -> int:
        """get the y point while iterating"""
        return self.__y_points[self.__index]

    def x_coordinate(self) -> float:
        """get the x coordinate while iterating"""
        if self.__x_coords is not None:
            return self.__x_coords[self.__index]
        else:
            return None

    def y_coordinate(self) -> float:
        """get the y coordinate while iterating"""
        if self.__y_coords is not None:
            return self.__y_coords[self.__index]
        else:
            return None

    def x_points(self) -> np.ndarray:
        return self.__x_points

    def y_points(self) -> np.ndarray:
        return self.__y_points

    def image_height(self) -> int:
        return self.__image_height

    def image_width(self) -> int:
        return self.__image_width

    def descriptor(self) -> Union[BandDescriptor, Dict[Band, BandDescriptor]]:
        return self.__descriptor

    def description(self) -> str:
        return self.__description

    def display_name(self) -> str:
        return self.__display_name

    def set_display_name(self, name:str):
        self.__display_name = name

    def map_info(self) -> OpenSpectraHeader.MapInfo:
        return self.__map_info

    def set_map_info(self, map_info:OpenSpectraHeader.MapInfo):
        self.__map_info = map_info
        self.__calculate_coords()


class PlotData:

    def __init__(self, x_data:np.ndarray, y_data:np.ndarray,
            x_label:str=None, y_label:str=None, title:str=None, color:str= "b",
            line_style:str= "-", legend:str=None):
        self.x_data = x_data
        self.y_data = y_data
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.color = color
        self.line_style = line_style
        self.legend = legend


class LinePlotData(PlotData):

    def __init__(self, x_data:np.ndarray, y_data:np.ndarray,
            x_label:str=None, y_label:str=None, title:str=None, color:str= "b",
            line_style:str= "-", legend:str=None):
        super().__init__(x_data, y_data, x_label, y_label, title, color, line_style, legend)


class HistogramPlotData(PlotData):

    def __init__(self, x_data:np.ndarray, y_data:np.ndarray, bins:int,
            x_label:str=None, y_label:str=None, title:str=None, color:str= "b",
            line_style:str= "-", legend:str=None,
            lower_limit:Union[int, float]=None, upper_limit:Union[int, float]=None):
        super().__init__(x_data, y_data, x_label, y_label, title, color, line_style, legend)
        self.bins = bins
        self.__lower_limit = lower_limit
        self.__upper_limit = upper_limit

    def lower_limit(self) -> Union[int, float]:
        return self.__lower_limit

    def set_lower_limit(self, limit:Union[int, float]):
        self.__lower_limit = limit

    def upper_limit(self) -> Union[int, float]:
        return self.__upper_limit

    def set_upper_limit(self, limit:Union[int, float]):
        self.__upper_limit = limit


class Bands:

    def __init__(self, bands:np.ndarray, labels:List[Tuple[str, str]]):
        self.__bands = bands
        self.__labels = labels

        # TODO verify indexing matching up?

    def bands(self, index:int=None)-> np.ndarray:
        if index is not None:
            return self.__bands[index, :]
        else:
            return self.__bands

    def labels(self) -> List[Tuple[str, str]]:
        return self.__labels

    def bands_shape(self) -> Tuple[int, int]:
        return self.__bands.shape


class BandStatistics(Bands):

    def __init__(self, bands:np.ndarray, labels:List[Tuple[str, str]]=None):
        super().__init__(bands, labels)
        self.__mean = bands.mean(0)
        # TODO is this correct?
        self.__min = bands.min(0)
        # TODO is this correct?
        self.__max = bands.max(0)
        self.__std = bands.std(0)
        self.__mean_plus = self.__mean + self.__std
        self.__mean_minus = self.__mean - self.__std

    def mean(self) -> np.ndarray:
        return self.__mean

    def min(self) -> np.ndarray:
        return self.__min

    def max(self) -> np.ndarray:
        return self.__max

    def plus_one_std(self)-> np.ndarray:
        return self.__mean_plus

    def minus_one_std(self)-> np.ndarray:
        return self.__mean_minus

    def std(self):
        return self.__std


class BandStaticsPlotData():

    def __init__(self, __band_stats:BandStatistics, wavelengths:np.ndarray, title:str=None):
        self.__band_stats = __band_stats
        self.__wavelengths = wavelengths
        if title is not None:
            self.__title = title
        else:
            self.__title = "Band Stats"

    def mean(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.mean(),
            "Wavelength", "Magnitude", self.__title, "b", legend="mean")

    def min(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.min(),
            "Wavelength", "Magnitude", self.__title, "r", legend="min")

    def max(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.max(),
            "Wavelength", "Magnitude", self.__title, "r", legend="max")

    def plus_one_std(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.plus_one_std(),
            "Wavelength", "Magnitude", self.__title, "g", legend="std+")

    def minus_one_std(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.minus_one_std(),
            "Wavelength", "Magnitude", self.__title, "g", legend="std-")


# TODO needs much attention!!!
class OpenSpectraBandTools:
    """A class for working on OpenSpectra files.
    Note: all indexes are expected to be zero based."""

    __LOG:Logger = LogHelper.logger("OpenSpectraBandTools")

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def bands(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray]) -> Bands:
        return Bands(self.__clean_data(self.__file.bands(lines, samples)), self.__file.header().band_labels())

    def band_statistics(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray]) -> BandStatistics:
        return BandStatistics(self.__clean_data(self.__file.bands(lines, samples)))

    def statistics_plot(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray],
            title:str=None) -> BandStaticsPlotData:
        band_stats = self.band_statistics(lines, samples)
        return BandStaticsPlotData(band_stats, self.__file.header().wavelengths(), title)

    def spectral_plot(self, line:int, sample:int) -> LinePlotData:
        band = self.__clean_data(self.__file.bands(line, sample))

        wavelengths = self.__file.header().wavelengths()
        # OpenSpectraBandTools.__LOG.debug("plotting spectra with min: {0}, max: {1}", band.min(), band.max())

        # TODO something better than having to know to do band[0, :] here?? Use Bands??
        return LinePlotData(wavelengths, band[0, :], "Wavelength", "Magnitude",
            "Spectrum S-{0}, L-{1}".format(sample + 1, line + 1))

    def band_descriptor(self, band_index:int) -> BandDescriptor:
        header = self.__file.header()
        band_label = header.band_label(band_index)
        bad_bands = header.bad_band_list()
        is_bad_band = bad_bands is not None and bad_bands[band_index]
        data_ignore_val = header.data_ignore_value()
        default_stretch: LinearImageStretch = header.default_stretch()

        return BandDescriptor(self.__file.name(), band_label[0], band_label[1],
            is_bad_band, data_ignore_val, default_stretch)

    def __clean_data(self, bands:np.ndarray) -> np.ndarray:
        result = bands
        header = self.__file.header()

        # If there is an ignore value maske any occurrences
        if header.data_ignore_value() is not None:
            result = ma.masked_equal(bands, header.data_ignore_value())

        # If there are bad bands mask them
        if header.bad_band_list() is not None:
            if not ma.isMaskedArray(result):
                result = ma.masked_array(result, mask=header.bad_band_list())
            else:
                result.mask = result.mask | header.bad_band_list()

        return self.__bogus_noise_cleanup(result)

    # TODO work around for now for 1 float file, remove noise from data for floats
    # TODO will need a general solution also for images too?
    # TODO where will this live
    @staticmethod
    def __bogus_noise_cleanup(bands:np.ndarray) -> np.ndarray:
        clean_bands = bands
        if clean_bands.dtype in OpenSpectraDataTypes.Floats:
            if clean_bands.min() == np.nan or clean_bands.max() == np.nan or clean_bands.min() == np.inf or clean_bands.max() == np.inf:
                clean_bands = ma.masked_invalid(clean_bands)

            # TODO certain areas look a bit better when filtered by different criteria, must be a better way
            # if clean_bands.std() > 1.0:
            # if clean_bands.std() > 0.1:
            # clean_bands = ma.masked_outside(clean_bands, -0.01, 0.05)
            clean_bands = ma.masked_outside(clean_bands, 0.0, 1.0)

        return clean_bands


class OpenSpectraRegionTools:
    """A class for working with Regions of Interest"""

    __LOG:Logger = LogHelper.logger("OpenSpectraRegionTools")

    def __init__(self, region:RegionOfInterest, band_tools:OpenSpectraBandTools):
        self.__region = region
        self.__band_tools = band_tools
        self.__map_info:OpenSpectraHeader.MapInfo = self.__region.map_info()
        self.__projection = None

        self.__has_map_info = False
        if self.__map_info is not None:
            self.__projection = self.__map_info.projection_name()
            if self.__map_info.projection_zone() is not None:
                self.__projection += (" " + str(self.__map_info.projection_zone()))
            if self.__map_info.projection_area() is not None:
                self.__projection += (" " + self.__map_info.projection_area())
            self.__projection += (" " + self.__map_info.datum())

            self.__output_format = "{0},{1},{2},{3}"
            self.__data_header = "sample,line,x_coordinate,y_coordinate"
            self.__has_map_info = True
        else:
            self.__output_format = "{0},{1}"
            self.__data_header = "sample,line"

    def save_region(self, file_name:str=None, text_stream:TextIOBase=None, include_bands:bool=True):
        OpenSpectraRegionTools.__LOG.debug("Save region to: {0}", file_name)
        # OpenSpectraRegionTools.__LOG.debug("Area: {0}", self.__region.area().tolist())

        bands:Bands = None
        if include_bands:
            bands = self.__band_tools.bands(self.__region.y_points(), self.__region.x_points())

            if bands.bands_shape()[0] != self.__region.x_points().size:
                raise ValueError("Number of bands didn't match number of points")

        if file_name is not None:
            with open(file_name, "w") as out:
                self.__write_output(out, bands)
        elif text_stream is not None:
            self.__write_output(text_stream, bands)
        else:
            raise ValueError("Must pass either a file name or text stream")

    def __write_output(self, out:TextIOBase, bands:Bands):
        descriptor = self.__region.descriptor()
        if type(descriptor) is dict:
            file_name = descriptor[Band.RED].file_name()
            band_name = ",".join([descriptor[Band.RED].band_name(),
                                  descriptor[Band.GREEN].band_name(),
                                  descriptor[Band.BLUE].band_name()])
            wavelength = ",".join([descriptor[Band.RED].wavelength_label(),
                                   descriptor[Band.GREEN].wavelength_label(),
                                   descriptor[Band.BLUE].wavelength_label()])
        else:
            file_name = descriptor.file_name()
            band_name = descriptor.band_name()
            wavelength = descriptor.wavelength_label()

        out.write("# name:{0}\n".format(self.__region.display_name()))
        out.write("# file name:{0}\n".format(file_name))
        out.write("# band name:{0}\n".format(band_name))
        out.write("# wavelength:{0}\n".format(wavelength))
        out.write("# image width:{0}\n".format(self.__region.image_width()))
        out.write("# image height:{0}\n".format(self.__region.image_height()))
        if self.__projection is not None:
            out.write("# projection:{0}\n".format(self.__projection))
        out.write("# description:{0}\n".format(self.__region.description()))
        out.write("# data:\n")

        # TODO output formatting?  Specific number of decimal places to print?
        out.write(self.__get_data_header(bands))
        band_index:int = 0
        for r in self.__region:
            if self.__has_map_info:
                out.write(
                    self.__output_format.format(r.x_point() + 1, r.y_point() + 1, r.x_coordinate(), r.y_coordinate()))
            else:
                out.write(self.__output_format.format(r.x_point() + 1, r.y_point() + 1))

            if bands is not None:
                out.write("," + ",".join([str(item) for item in bands.bands(band_index)]) + "\n")
                band_index += 1
            else:
                out.write("\n")

    def __get_data_header(self, bands:Bands=None) -> str:
        header:str = self.__data_header
        if bands is not None:
            header += ","
            header += ",".join(["-".join(item) for item in bands.labels()])

        return header + "\n"


class OpenSpectraImageTools:
    """A class for creating Images from OpenSpectra files.
    Note: all indexes are expected to be zero based."""

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def greyscale_image(self, band:int, band_descriptor:BandDescriptor) -> GreyscaleImage:
        return GreyscaleImage(self.__file.raw_image(band), band_descriptor)

    def rgb_image(self, red:int, green:int, blue:int,
            red_descriptor:BandDescriptor, green_descriptor:BandDescriptor, blue_descriptor:BandDescriptor) -> RGBImage:
        # Access each band seperately so we get views of the data for efficiency
        return RGBImage(self.__file.raw_image(red), self.__file.raw_image(green),
            self.__file.raw_image(blue), red_descriptor, green_descriptor, blue_descriptor)


class OpenSpectraHistogramTools:
    """A class for generating histogram data from Images.
    Note: all indexes are expected to be zero based."""

    def __init__(self, image:Image):
        self.__image = image
        if isinstance(self.__image, GreyscaleImage):
            self.__type = "greyscale"
        elif isinstance(self.__image, RGBImage):
            self.__type = "rgb"
        else:
            raise TypeError("Unknown image type")

    def raw_histogram(self, band:Band=None) -> HistogramPlotData:
        """If band is included and the image is Greyscale it is ignores
        If image is RGB and band is missing an error is raised"""

        if self.__type == "rgb" and band is None:
            raise ValueError("band argument is required when image is RGB")

        raw_data = self.__image.raw_data(band)
        plot_data = OpenSpectraHistogramTools.__get_hist_data(raw_data)
        plot_data.x_label = "Magnitude"
        plot_data.y_label = "Count  "
        plot_data.title = "Raw " + self.__image.label(band)
        plot_data.color = "r"
        plot_data.set_lower_limit(self.__image.low_cutoff(band))
        plot_data.set_upper_limit(self.__image.high_cutoff(band))
        return plot_data

    def adjusted_histogram(self, band:Band=None) -> HistogramPlotData:

        if self.__type == "rgb" and band is None:
            raise ValueError("band argument is required when image is RGB")

        image_data = self.__image.image_data(band)
        plot_data = OpenSpectraHistogramTools.__get_hist_data(image_data)
        plot_data.x_label = "Pixel Values"
        plot_data.y_label = "Count"
        plot_data.title = "Adjusted " + self.__image.label(band)
        plot_data.color = "b"
        return plot_data

    @staticmethod
    def __get_hist_data(data:np.ndarray) -> HistogramPlotData:
        type = data.dtype
        if type in OpenSpectraDataTypes.Ints:
            x_range = (data.min(), data.max())
            bins = data.max() - data.min()
            return HistogramPlotData(x_range, data.flatten(), bins=bins)
        elif type in OpenSpectraDataTypes.Floats:
            x_range = (data.min(), data.max())
            bins = OpenSpectraProperties.FloatBins
            return HistogramPlotData(x_range, data.flatten(), bins=bins)
        else:
            raise TypeError("Data with type {0} is not supported".format(type))


class CubeParams:
    """A class for defining the dimension and interleave of a new data cube
    Note: all indexes are expected to be zero based."""

    def __init__(self, interleave:str, lines:Tuple[int, int],
            samples:Tuple[int, int], bands:Union[Tuple[int, int], List[int]]):
        self.__interleave = interleave
        self.__lines = lines
        self.__samples = samples
        # if we get a list with a single value convert it to a Slice?
        if isinstance(bands, list) and len(bands) == 1:
            self.__bands = (bands[0], bands[0] + 1)
        else:
            self.__bands = bands

    def __str__(self):
        return ", ".join(["interleave: " + self.__interleave,
                          "lines: {}".format(self.__lines),
                          "samples: {}".format(self.__samples),
                          "bands: {}".format(self.__bands)])

    def interleave(self) -> str:
        return self.__interleave

    def lines(self) -> Tuple[int, int]:
        """See openspectra.openspecrtra_tools.SubCubeTools for an explaination
        of how these parameters are used"""
        return self.__lines

    def samples(self) -> Tuple[int, int]:
        """See openspectra.openspecrtra_tools.SubCubeTools for an explaination
        of how these parameters are used"""
        return self.__samples

    def bands(self) -> Union[Tuple[int, int], List[int]]:
        """See openspectra.openspecrtra_tools.SubCubeTools for an explaination
        of how these parameters are used"""
        return self.__bands


class SubCubeTools:
    """The range and list index parameters in this class are zero based and
    follow the standard Python and Numpy slicing rules.  See
    https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html.  Therefore the lines,
    samples, and bands (the tuple version) parameters have a valid range of 0 to the total
    count for each parameter which is the value found in the file's header.  So for example
    to select all the lines to be included in the sub cube the lines parameter would be
    (0, OpenSpectraHeader.lines()).  The list form of the bands argument is a list of
    band indexes to be included in the sub cube and is intended to be used when a
    non-contiguous set of bands is needed.  Valid values are
    0 to OpenSpectraHeader.band_count() - 1"""

    __LOG:Logger = LogHelper.logger("SubCubeTools")

    def __init__(self, source_file:OpenSpectraFile, new_cube_params:CubeParams=None):
        """Expects a source OpenSpectraFile and optionally new parameter for a new sub cube.
        If new_cube_params is None the source_file full dimensions are initially set"""

        self.__source_file = source_file
        self.__source_header:OpenSpectraHeader = self.__source_file.header()

        self.__interleave:str = None
        self.__lines:Tuple[int, int] = None
        self.__samples:Tuple[int, int] = None
        self.__bands:Union[Tuple[int, int], List[int]] = None

        if new_cube_params is not None:
            self.__interleave = new_cube_params.interleave()
            self.__lines = new_cube_params.lines()
            self.__samples = new_cube_params.samples()
            self.__bands = new_cube_params.bands()
        else:
            self.__interleave = self.__source_header.interleave()
            self.__lines = (0, self.__source_header.lines())
            self.__samples = (0, self.__source_header.samples())
            self.__bands = (0, self.__source_header.band_count())

        self.__sub_cube:np.ndarray = None
        self.__sub_cube_header:MutableOpenSpectraHeader = None

    def __validate(self):
        """treat a None value as include the full range"""
        if self.__interleave is None:
            self.__interleave = self.__source_header.interleave()
        else:
            self.__validate_interleave(self.__interleave)

        if self.__lines is None:
            self.__lines = (0, self.__source_header.lines())
        else:
            self.__validate_lines(self.__lines)

        if self.__samples is None:
            self.__samples = (0, self.__source_header.samples())
        else:
            self.__validate_samples(self.__samples)

        if self.__bands is None:
            self.__bands = (0, self.__source_header.band_count())
        else:
            self.__validate_bands(self.__bands)

    @staticmethod
    def __validate_interleave(interleave:str):
        if OpenSpectraHeader.BIL_INTERLEAVE != interleave and \
                OpenSpectraHeader.BIP_INTERLEAVE != interleave and \
                OpenSpectraHeader.BSQ_INTERLEAVE != interleave:
            raise ValueError("Interleave must be one of {}, {}, or {}".
                format(OpenSpectraHeader.BIL_INTERLEAVE, OpenSpectraHeader.BIP_INTERLEAVE,
                    OpenSpectraHeader.BSQ_INTERLEAVE))

    def __validate_lines(self, lines:Tuple[int, int]):
        if min(lines) < 0:
            raise ValueError("Values for lines must be 0 or greater")

        if max(lines) > self.__source_header.lines():
            raise ValueError("Value for lines must be less than or equal to {}".format(self.__source_header.lines()))

    def __validate_samples(self, samples:Tuple[int, int]):
        if min(samples) < 0:
            raise ValueError("Values for samples must be 0 or greater")

        if max(samples) > self.__source_header.samples():
            raise ValueError("Values for samples must be less than  or equal to {}".format(self.__source_header.samples()))

    def __validate_bands(self, bands:Union[Tuple[int, int], List[int]]):
        if isinstance(bands, list):
            len_bands = len(bands)
            if len(set(bands)) != len_bands:
                raise ValueError("Duplicate values detected in band list")

            if len_bands > self.__source_header.band_count():
                raise ValueError("Number of bands in band list cannot exceed {}".format(self.__source_header.band_count()))

            if min(bands) < 0:
                raise ValueError("Minimum value for bands is 0")

            if max(bands) > self.__source_header.band_count():
                raise ValueError("Maximum allowed index value for bands is {}".format(self.__source_header.band_count()))
        else:
            if min(bands) < 0:
                raise ValueError("Values for bands must be 0 or greater")

            if max(bands) > self.__source_header.band_count():
                raise ValueError("Values for bands must be less than  or equal to {}".format(self.__source_header.band_count()))

    def __convert_interleave(self):

        source_interleave = self.__source_header.interleave()
        if self.__interleave == source_interleave:
            return

        if source_interleave == OpenSpectraHeader.BIL_INTERLEAVE:
            # BIL axis order is (lines, bands, samples)

            if self.__interleave == OpenSpectraHeader.BSQ_INTERLEAVE:
                # BSQ axis order is (bands, lines, samples)
                self.__sub_cube = self.__sub_cube.transpose(1, 0, 2)

            elif self.__interleave == OpenSpectraHeader.BIP_INTERLEAVE:
                # BIP axis order is (line, sample, bands)
                self.__sub_cube = self.__sub_cube.transpose(0, 2, 1)

            else:
                SubCubeTools.__LOG.error(
                    "Unexpected interleave value in __convert_interleave().  Value was: {}".
                        format(self.__interleave))

        elif source_interleave == OpenSpectraHeader.BIP_INTERLEAVE:
            # BIP axis order is (line, sample, bands)

            if self.__interleave == OpenSpectraHeader.BIL_INTERLEAVE:
                # BIL axis order is (lines, bands, samples)
                self.__sub_cube = self.__sub_cube.transpose(0, 2, 1)

            elif self.__interleave == OpenSpectraHeader.BSQ_INTERLEAVE:
                # BSQ axis order is (bands, lines, samples)
                self.__sub_cube = self.__sub_cube.transpose(2, 0, 1)

            else:
                SubCubeTools.__LOG.error(
                    "Unexpected interleave value in __convert_interleave().  Value was: {}".
                        format(self.__interleave))

        elif source_interleave == OpenSpectraHeader.BSQ_INTERLEAVE:
            # BSQ axis order is (bands, lines, samples)

            if self.__interleave == OpenSpectraHeader.BIL_INTERLEAVE:
                # BIL axis order is (lines, bands, samples)
                self.__sub_cube = self.__sub_cube.transpose(1, 0, 2)

            elif self.__interleave == OpenSpectraHeader.BIP_INTERLEAVE:
                # BIP axis order is (line, sample, bands)
                self.__sub_cube = self.__sub_cube.transpose(1, 2, 0)

            else:
                SubCubeTools.__LOG.error(
                    "Unexpected interleave value in __convert_interleave().  Value was: {}".
                        format(self.__interleave))
        else:
            SubCubeTools.__LOG.error(
                "Unexpected interleave value in __convert_interleave().  Value was: {}".
                    format(source_interleave))

    def __create_header(self):
        self.__sub_cube_header = MutableOpenSpectraHeader(os_header=self.__source_header)
        self.__sub_cube_header.set_interleave(self.__interleave)
        self.__sub_cube_header.set_lines(max(self.__lines) - min(self.__lines))
        self.__sub_cube_header.set_samples(max(self.__samples) - min(self.__samples))

        if isinstance(self.__bands, list):
            band_slicer = self.__bands
            band_count = len(band_slicer)
        else:
            band_slicer = slice(self.__bands[0], self.__bands[1])
            band_count = max(self.__bands) - min(self.__bands)

        # update bands info
        new_band_names = self.__source_header.band_names()
        if new_band_names is not None:
            new_band_names = new_band_names[band_slicer]
        new_wavelengths = self.__source_header.wavelengths()[band_slicer]
        new_bad_bands = self.__source_header.bad_band_list()
        if new_bad_bands is not None:
            new_bad_bands = new_bad_bands[band_slicer]

        self.__sub_cube_header.set_bands(band_count, new_band_names, new_wavelengths, new_bad_bands)

        # If there unsupported properties some might be band related so try to
        # work the out here
        unsupported_props = self.__source_header.unsupported_props()
        for key, value in unsupported_props.items():
            if isinstance(value, list) and len(value) == self.__source_header.band_count():
                new_prop_value = value[band_slicer]
                unsupported_props[key] = new_prop_value

        self.__sub_cube_header.set_unsupported_props(unsupported_props)

        # set header offset to 0, we don't support offsets in the data file
        # at this time
        self.__sub_cube_header.set_header_offset(0)

        # check to see if map info needs updating, it the original reference pixel
        # is not included in the sub cube
        map_info = self.__sub_cube_header.map_info()
        if map_info is not None:
            orig_x_ref = map_info.x_reference_pixel() - 1
            orig_y_ref = map_info.y_reference_pixel() - 1

            is_updated = False
            new_x_ref = orig_x_ref
            if not (min(self.__samples) <= orig_x_ref <= max(self.__samples)):
                new_x_ref = min(self.__samples)
                is_updated = True

            new_y_ref = orig_y_ref
            if not (min(self.__lines) <= orig_y_ref <= max(self.__lines)):
                new_y_ref = min(self.__lines)
                is_updated = True

            new_coords = map_info.calculate_coordinates(new_x_ref, new_y_ref)
            self.__sub_cube_header.set_x_reference(new_x_ref + 1, new_coords[0])
            self.__sub_cube_header.set_y_reference(new_y_ref + 1, new_coords[1])

    def create_sub_cube(self):
        # validate params
        self.__validate()
        SubCubeTools.__LOG.debug("create_sub_cube validation passed...")

        # slice out the sub cube
        self.__sub_cube = self.__source_file.cube(self.__lines, self.__samples, self.__bands)
        self.__sub_cube = self.__sub_cube.astype(self.__source_header.data_type())
        # SubCubeTools.__LOG.debug("create_sub_cube sub cube created: {0}", self.__sub_cube)
        SubCubeTools.__LOG.debug("create_sub_cube sub cube created")

        # do the interleave conversion if needed
        self.__convert_interleave()

        # update header and map info if needed
        self.__create_header()
        SubCubeTools.__LOG.debug("create_sub_cube header created: {0}", self.__sub_cube_header.dump())

    def save(self, file_name:str):
        if self.__sub_cube  is not None and self.__sub_cube_header is not None:
            # TODO check name?  strip extensions?

            # write data file
            flat_iterator = self.__sub_cube.flat
            with open(file_name, "wb") as out_file:
                for item in flat_iterator:
                    out_file.write(item)

                out_file.flush()

            # write header
            self.__sub_cube_header.save(file_name)

    def interleave(self) -> str:
        return self.__interleave

    def set_interleave(self, interleave:str):
        SubCubeTools.__validate_interleave(interleave)
        self.__interleave = interleave

    def lines(self) -> Tuple[int, int]:
        return self.__lines

    def set_lines(self, lines:Tuple[int, int]):
        self.__validate_lines(lines)
        self.__lines = lines

    def samples(self) -> Tuple[int, int]:
        return self.__samples

    def set_samples(self, samples:Tuple[int, int]):
        self.__validate_samples(samples)
        self.__samples = samples

    def bands(self) -> Union[Tuple[int, int], List[int]]:
        return self.__bands

    def set_bands(self, bands:Union[Tuple[int, int], List[int]]):
        self.__validate_bands(bands)
        self.__bands = bands
