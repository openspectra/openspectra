import logging
from enum import Enum

import numpy as np

from openspectra.utils import LogHelper, OpenSpectraDataTypes, OpenSpectraProperties, Logger


class ImageAdjuster:

    def adjust_by_percentage(self, lower, upper):
        pass

    def adjust_by_value(self, lower, upper):
        pass

    def adjust(self):
        pass

    def low_cutoff(self):
        pass

    def set_low_cutoff(self, limit):
        pass

    def high_cutoff(self):
        pass

    def set_high_cutoff(self, limit):
        pass


class BandImageAdjuster(ImageAdjuster):

    __LOG:Logger = LogHelper.logger("BandImageAdjuster")

    def __init__(self, band:np.ndarray):
        self.__band = band
        self.__type = self.__band.dtype
        self.__image_data = None
        self.__low_cutoff = 0
        self.__high_cutoff = 0
        self.adjust_by_percentage(2, 98)
        BandImageAdjuster.__LOG.debug("type: {0}", self.__type)
        BandImageAdjuster.__LOG.debug("min: {0}, max: {1}", self.__band.min(), self.__band.max())

    def __del__(self):
        self.__image_data = None
        self.__band = None

    # TODO this bugs me a bit but need it public so this class can be used in RGBImageAdjuster
    def adjusted_data(self) -> np.ndarray:
        return self.__image_data

    def adjust_by_percentage(self, lower, upper):
        if self.__type in OpenSpectraDataTypes.Ints:
            self.__low_cutoff, self.__high_cutoff = np.percentile(self.__band, (lower, upper))
        elif self.__type in OpenSpectraDataTypes.Floats:
            self.__calcualte_float_cutoffs(lower, upper)
        else:
            raise TypeError("Image data type {0} not supported".format(self.__type))

        self.adjust()

    def adjust_by_value(self, lower, upper):
        self.__low_cutoff = lower
        self.__high_cutoff = upper
        self.adjust()

    def low_cutoff(self):
        return self.__low_cutoff

    def set_low_cutoff(self, limit):
        self.__low_cutoff = limit

    def high_cutoff(self):
        return self.__high_cutoff

    def set_high_cutoff(self, limit):
        self.__high_cutoff = limit

    def adjust(self):
        BandImageAdjuster.__LOG.debug("low cutoff: {0}, high cutoff: {1}", self.low_cutoff(), self.high_cutoff())

        # TODO <= or <, looks like <=, with < I get strange dots on the image
        low_mask = np.ma.getmask(np.ma.masked_where(self.__band <= self.__low_cutoff, self.__band, False))

        # TODO >= or <, looks like >=, with < I get strange dots on the image
        high_mask = np.ma.getmask(np.ma.masked_where(self.__band >= self.__high_cutoff, self.__band, False))

        full_mask = low_mask | high_mask
        masked_band = np.ma.masked_where(full_mask, self.__band, True)

        # 0 and 256 assumes 8-bit images, the pixel value limits
        # TODO why didn't 255 work?
        A, B = 0, 256
        masked_band = ((masked_band - self.__low_cutoff) * ((B - A) / (self.__high_cutoff - self.__low_cutoff)) + A)

        masked_band[low_mask] = 0
        masked_band[high_mask] = 255

        self.__image_data = masked_band.astype("uint8")

    def __calcualte_float_cutoffs(self, lower, upper):
        nbins = OpenSpectraProperties.FloatBins
        min = self.__band.min()
        max = self.__band.max()

        # scale to generate histogram data
        hist_scaled = np.floor((self.__band - min)/(max - min) * (nbins - 1))
        scaled_low_cut, scaled_high_cut = np.percentile(hist_scaled, (lower, upper))

        self.__low_cutoff = (scaled_low_cut / (nbins - 1) * (max - min)) + min
        self.__high_cutoff = (scaled_high_cut / (nbins - 1) * (max - min)) + min


class Band(Enum):
    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


class RGBImageAdjuster(ImageAdjuster):

    def __init__(self, red: np.ndarray, green: np.ndarray, blue: np.ndarray):
        self.__adjusted_bands = {Band.RED: BandImageAdjuster(red),
                                 Band.GREEN: BandImageAdjuster(green),
                                 Band.BLUE: BandImageAdjuster(blue)}
        self.__updated = False

    def __del__(self):
        del self.__adjusted_bands

    def _updated(self) -> bool:
        return self.__updated

    def _set_updated(self, val:bool):
        self.__updated = val

    def _adjusted_data(self, band:Band) -> np.ndarray:
        return self.__adjusted_bands[band].adjusted_data()

    def adjust_by_percentage(self, lower, upper, band:Band=None):
        if band is not None:
            self.__adjusted_bands[band].adjust_by_percentage(lower, upper)
        else:
            self.__adjusted_bands[Band.RED].adjust_by_percentage(lower, upper)
            self.__adjusted_bands[Band.GREEN].adjust_by_percentage(lower, upper)
            self.__adjusted_bands[Band.BLUE].adjust_by_percentage(lower, upper)

        self.__updated = True

    def adjust_by_value(self, band:Band, lower, upper):
        if band is not None:
            self.__adjusted_bands[band].adjust_by_value(lower, upper)
        else:
            self.__adjusted_bands[Band.RED].adjust_by_value(lower, upper)
            self.__adjusted_bands[Band.GREEN].adjust_by_value(lower, upper)
            self.__adjusted_bands[Band.BLUE].adjust_by_value(lower, upper)

        self.__updated = True

    def adjust(self):
        # TODO
        pass

    def low_cutoff(self):
        return (self.__adjusted_bands[Band.RED].low_cutoff(),
                self.__adjusted_bands[Band.GREEN].low_cutoff(),
                self.__adjusted_bands[Band.Band.BLUE].low_cutoff())

    def set_low_cutoff(self, limit):
        # TODO
        pass

    def high_cutoff(self):
        return (self.__adjusted_bands[Band.RED].high_cutoff(),
                self.__adjusted_bands[Band.GREEN].high_cutoff(),
                self.__adjusted_bands[Band.Band.BLUE].high_cutoff())

    def set_high_cutoff(self, limit):
        # TODO
        pass


# TODO need to think through how much data we're holding here, clean up, views?
class Image(ImageAdjuster):

    def image_data(self) -> np.ndarray:
        pass

    def raw_data(self, band:Band) -> np.ndarray:
        pass

    def image_shape(self) -> (int, int):
        pass

    def bytes_per_line(self) -> int:
        pass


class GreyscaleImage(Image, BandImageAdjuster):
    """An 8-bit 8-bit grayscale image"""
    def __init__(self, band:np.ndarray):
        super().__init__(band)
        self.__band = band

    def __del__(self):
        super().__del__()
        self.__band = None

    def image_data(self) -> np.ndarray:
        return super().adjusted_data()

    def raw_data(self, band:Band=None) -> np.ndarray:
        return self.__band

    def image_shape(self) -> (int, int):
        return self.image_data().shape

    def bytes_per_line(self) -> int:
        return self.image_data().shape[1]


# TODO this is definately not thread safe
class RGBImage(Image, RGBImageAdjuster):
    """A 32-bit RGB image using format (0xffRRGGBB)"""

    __LOG:Logger = LogHelper.logger("RGBImage")

    __HIGH_BYTE = 255 * 256 * 256 * 256
    __RED_SHIFT = 256 * 256
    __GREEN_SHIFT = 256

    def __init__(self, red: np.ndarray, green: np.ndarray, blue: np.ndarray):
        # TODO exceptions in constructors??
        if not ((red.size == green.size == blue.size) and
                (red.shape == green.shape == blue.shape)):
            raise ValueError("All bands must have the same size and shape")

        super().__init__(red, green, blue)
        self.__bands = {Band.RED: red, Band.GREEN: green, Band.BLUE: blue}
        self.__high_bytes = np.full(red.shape, RGBImage.__HIGH_BYTE, np.uint32)

        self.__calculate_image()

        if RGBImage.__LOG.isEnabledFor(logging.DEBUG):
            np.set_printoptions(8, formatter={'int_kind': '{:02x}'.format})
            RGBImage.__LOG.debug("{0}", self.__data)
            RGBImage.__LOG.debug("height: {0}", self.__data.shape[0])
            RGBImage.__LOG.debug("width: {0}", self.__data.shape[1])
            RGBImage.__LOG.debug("size: {0}", self.__data.size)
            np.set_printoptions()

    def __del__(self):
        super().__del__()
        self.__data = None
        self.__high_bytes = None
        del self.__bands

    def image_data(self) -> np.ndarray:
        if super()._updated():
            self.__calculate_image()
        return self.__data

    def raw_data(self, band:Band) -> np.ndarray:
        return self.__bands[band]

    def image_shape(self) -> (int, int):
        return self.__data.shape

    def bytes_per_line(self) -> int:
        return self.__data.shape[1] * 4

    def __calculate_image(self):
        self.__data = self.__high_bytes + \
                      super()._adjusted_data(Band.RED).astype(np.uint32) * RGBImage.__RED_SHIFT + \
                      super()._adjusted_data(Band.GREEN).astype(np.uint32) * RGBImage.__GREEN_SHIFT + \
                      super()._adjusted_data(Band.BLUE).astype(np.uint32)
        super()._set_updated(False)

