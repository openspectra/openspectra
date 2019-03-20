#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
import time
from typing import Union

import numpy as np
from numpy import ma

from openspectra.image import Image, GreyscaleImage, RGBImage, Band
from openspectra.openspectra_file import OpenSpectraFile
from openspectra.utils import OpenSpectraDataTypes, OpenSpectraProperties, Logger, LogHelper


class RegionOfInterest:

    def __init__(self, area:np.ma.MaskedArray, x_scale:float, y_scale:float,
            image_height:int, image_width:int):
        self.__id = str(time.time_ns())
        self.__name = self.__id
        self.__area = area
        self.__x_scale = x_scale
        self.__y_scale = y_scale
        self.__image_height = image_height
        self.__image_width = image_width

        # split the points back into x and y values
        self.__x_points = self.__area[:, 0]
        self.__y_points = self.__area[:, 1]

        # take only the points that were inside the polygon
        self.__x_points = self.__x_points[~self.__x_points.mask]
        self.__y_points = self.__y_points[~self.__y_points.mask]

        # calculate the points in the region if the image is scaled
        self.__adjusted_x_points = np.floor(self.__x_points * x_scale).astype(np.int16)
        self.__adjusted_y_points = np.floor(self.__y_points * y_scale).astype(np.int16)

    def id(self) -> str:
        return self.__id

    def x_points(self) -> np.ndarray:
        return self.__x_points

    def y_points(self) -> np.ndarray:
        return self.__y_points

    def adjusted_x_points(self) -> np.ndarray:
        return self.__adjusted_x_points

    def adjusted_y_points(self) -> np.ndarray:
        return self.__adjusted_y_points

    def image_height(self) -> int:
        return self.__image_height

    def image_width(self) -> int:
        return self.__image_width

    def name(self) -> str:
        return self.__name

    def set_name(self, name:str):
        self.__name = name


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
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit


class BandStatistics:

    def __init__(self, bands:np.ndarray):
        self.__bands = bands
        # TODO lazy initialize theese???
        self.__mean = bands.mean(0)
        # TODO is this correct?
        self.__min = bands.min(0)
        # TODO is this correct?
        self.__max = bands.max(0)
        self.__std = bands.std(0)
        self.__mean_plus = self.__mean + self.__std
        self.__mean_minus = self.__mean - self.__std

    def bands(self)-> np.ndarray:
        return self.__bands

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

    def __init__(self, __band_stats:BandStatistics, wavelengths:np.ndarray):
        self.__band_stats = __band_stats
        self.__wavelengths = wavelengths

    def mean(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.mean(),
            "Wavelength", "Brightness", "Band Stats", "b", legend="mean")

    def min(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.min(),
            "Wavelength", "Brightness", "Band Stats", "r", legend="min")

    def max(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.max(),
            "Wavelength", "Brightness", "Band Stats", "r", legend="max")

    def plus_one_std(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.plus_one_std(),
            "Wavelength", "Brightness", "Band Stats", "g", legend="std+")

    def minus_one_std(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.minus_one_std(),
            "Wavelength", "Brightness", "Band Stats", "g", legend="std-")


class OpenSpectraBandTools:
    """A class for working on OpenSpectra files"""

    __LOG:Logger = LogHelper.logger("OpenSpectraBandTools")

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def __del__(self):
        self.__file = None

    def band_statistics(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray]) -> BandStatistics:
        return BandStatistics(OpenSpectraBandTools.__bogus_noise_cleanup(self.__file.bands(lines, samples)))

    def statistics_plot(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray]) -> BandStaticsPlotData:
        band_stats = self.band_statistics(lines, samples)
        return BandStaticsPlotData(band_stats, self.__file.header().wavelengths())

    def spectral_plot(self, line:int, sample:int) -> LinePlotData:
        band = OpenSpectraBandTools.__bogus_noise_cleanup(self.__file.bands(line, sample))

        wavelengths = self.__file.header().wavelengths()
        # OpenSpectraBandTools.__LOG.debug("plotting spectra with min: {0}, max: {1}", band.min(), band.max())
        return LinePlotData(wavelengths, band, "Wavelength", "Brightness",
            "Spectra S-{0}, L-{1}".format(sample + 1, line + 1))

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


class OpenSpectraImageTools:
    """A class for creating Images from OpenSpectra files"""

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def __del__(self):
        self.__file = None

    def greyscale_image(self, band:int, label:str=None) -> GreyscaleImage:
        return GreyscaleImage(self.__file.raw_image(band), label)

    def rgb_image(self, red:int, green:int, blue:int,
            red_label:str=None, green_label:str=None, blue_label:str=None) -> RGBImage:
        # Access each band seperately so we get views of the data for efficiency
        return RGBImage(self.__file.raw_image(red), self.__file.raw_image(green),
            self.__file.raw_image(blue), red_label, green_label, blue_label)


class OpenSpectraHistogramTools:
    """A class for generating histogram data from Images"""

    def __init__(self, image:Image):
        self.__image = image
        if isinstance(self.__image, GreyscaleImage):
            self.__type = "greyscale"
        elif isinstance(self.__image, RGBImage):
            self.__type = "rgb"
        else:
            raise TypeError("Unknown image type")

    def __del__(self):
        self.__image = None

    def raw_histogram(self, band:Band=None) -> HistogramPlotData:
        """If band is included and the image is Greyscale it is ignores
        If image is RGB and band is missing an error is raised"""

        if self.__type == "rgb" and band is None:
            raise ValueError("band argument is required when image is RGB")

        raw_data = self.__image.raw_data(band)
        plot_data = OpenSpectraHistogramTools.__get_hist_data(raw_data)
        plot_data.x_label = "X-FixMe"
        plot_data.y_label = "Y-FixMe"
        plot_data.title = "Raw " + self.__image.label(band)
        plot_data.color = "r"
        plot_data.lower_limit = self.__image.low_cutoff(band)
        plot_data.upper_limit = self.__image.high_cutoff(band)
        return plot_data

    def adjusted_histogram(self, band:Band=None) -> HistogramPlotData:

        if self.__type == "rgb" and band is None:
            raise ValueError("band argument is required when image is RGB")

        image_data = self.__image.image_data(band)
        plot_data = OpenSpectraHistogramTools.__get_hist_data(image_data)
        plot_data.x_label = "X-FixMe"
        plot_data.y_label = "Y-FixMe"
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
