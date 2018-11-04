import numpy as np

from openspectra.image import Image
from openspectra.openspectra_file import OpenSpectraFile


class PlotData:
    def __init__(self, xdata, ydata, xlabel, ylabel, title,
            color="b", linestyle="-"):
        self.xdata = xdata
        self.ydata = ydata
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.color = color
        self.linestyle = linestyle


class LinePlotData(PlotData):

    def __init__(self, xdata, ydata, xlabel, ylabel, title,
            color="b", linestyle="-"):
        super().__init__(xdata, ydata, xlabel, ylabel, title, color, linestyle)


class HistogramPlotData(PlotData):

    def __init__(self, xdata, ydata, xlabel, ylabel, title, color="b",
            linestyle="-", lower_limit=None, upper_limit=None):
        super().__init__(xdata, ydata, xlabel, ylabel, title, color, linestyle)
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit


class BandStatistics:

    def __init__(self, bands:np.ndarray):
        self.__bands = bands
        # TODO lazy initialize theese???
        self.__mean = bands.mean(0)
        self.__min = bands.min(0)
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


class OpenSpectraBandTools:
    '''A class for working on OS files'''

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def band_statistics(self, lines:tuple, samples:tuple) -> BandStatistics:
        return BandStatistics(self.__file.band(lines, samples))

    def statistics_plot(self, lines:tuple, samples:tuple) -> [LinePlotData]:
        pass

    def spectral_plot(self, line:int, sample:int) -> LinePlotData:
        band = self.__file.band(line, sample)
        wavelengths = self.__file.header().wavelengths()
        return LinePlotData(wavelengths, band, "Wavelength", "Brightness",
            "Spectra S-{0}, L-{1}".format(sample + 1, line + 1))


class OpenSpectraImageTools:

    def __init__(self, image:Image):
        self.__image = image
        self.__label = None

    def raw_histogram(self) -> HistogramPlotData:
        raw_data = self.__image.raw_data()
        return HistogramPlotData(
            np.arange(raw_data.min(), raw_data.max() + 1, 1),
            raw_data.flatten(), "X-FixMe", "Y-FixMe", "Raw " + self.__label,
            "r", lower_limit=self.__image.low_cutoff(),
            upper_limit=self.__image.high_cutoff())

    def adjusted_histogram(self) -> HistogramPlotData:
        image_data = self.__image.image_data()
        return HistogramPlotData(
            np.arange(image_data.min(), image_data.max() + 1, 1),
            image_data.flatten(), "X-FixMe", "Y-FixMe", "Adjusted " + self.__label)

    def label(self):
        return self.__label

    def set_label(self, label):
        self.__label = label