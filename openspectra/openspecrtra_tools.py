import numpy as np

# TODO divide in subclasses
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


class OpenSpectraTools:
    '''A class for working on OS files'''

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def band_statistics(self, lines, samples) -> BandStatistics:
        return BandStatistics(self.__file.band(lines, samples))


class OpenSpectraPlotTools:

    def __init__(self, file:OpenSpectraFile):
        self.__file = file
        self.__band_statistics = BandStatistics(file)

    def statistics_plot(self, lines, samples) -> [LinePlotData]:
        pass

    def spectral_plot(self, line, sample) -> LinePlotData:
        pass

    def raw_histogram(self) -> HistogramPlotData:
        pass

    def adjusted_histogram(self) -> HistogramPlotData:
        pass