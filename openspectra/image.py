from enum import Enum

import numpy as np
import numpy.ma as ma


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


def equalize_histogram(input_image: np.ndarray) -> np.ndarray:
    # first create a histogram of the original image and it's
    max_pixel = np.amax(input_image)
    hist, bins = np.histogram(input_image.flatten(),
        max_pixel + 2, [0, max_pixel + 1])

    # cumulative distribution function
    cdf = hist.cumsum()

    # TODO only used for plotting??
    # cdf_normalized = cdf * hist.max() / cdf.max()

    # create a masked version of cdf where 0 values are removed
    cdf_m = np.ma.masked_equal(cdf, 0)
    cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    # add the masked zero values back to the array
    cdf_adj = np.ma.filled(cdf_m, 0).astype('uint8')
    return cdf_adj

    # return cdf_adj[input_image]
    # cdf = ((cdf - cdf.min()) * 255 / (cdf.max() - cdf.min())).astype('uint8')
    # return cdf

    # TODO this apparently ignores the masking and produces a new ndarray the size of the underlying data
    # TODO not sure what it fills with.
    # return cdf[input_image]


class BandImageAdjuster(ImageAdjuster):

    def __init__(self, band:np.ndarray):
        self.__band = band
        self.__image_data = None
        self.__low_cutoff = 0
        self.__high_cutoff = 0
        self.adjust_by_percentage(2, 98)

    def __del__(self):
        self.__image_data = None
        self.__band = None

    # TODO this bugs me a bit but need it public so this class can be used in RGBImageAdjuster
    def adjusted_data(self) -> np.ndarray:
        return self.__image_data

    def adjust_by_percentage(self, lower, upper):
        self.__low_cutoff, self.__high_cutoff = np.percentile(
            self.__band, (lower, upper))
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
        self.__image_data = self.__band.copy()
        print("l_cut: {0}, h_cut: {1}".format(self.low_cutoff(), self.high_cutoff()))

        low_mask = self.__image_data.view(ma.MaskedArray)
        # TODO <= or <, looks like <=, with < I get strange dots on the image
        low_mask.mask = [self.__image_data <= self.__low_cutoff]

        high_mask = self.__image_data.view(ma.MaskedArray)
        # TODO >= or <, looks like >=, with < I get strange dots on the image
        high_mask.mask = [self.__image_data >= self.__high_cutoff]

        full_mask = low_mask & high_mask

        # 0 and 256 assumes 8-bit images, the pixel value limits
        A, B = 0, 256
        full_mask = ((full_mask - self.__low_cutoff) * ((B - A) / (self.__high_cutoff - self.__low_cutoff)) + A)

        low_mask[low_mask.mask] = 0
        high_mask[high_mask.mask] = 255

        self.__image_data[~full_mask.mask] = full_mask[~full_mask.mask]
        self.__image_data = self.__image_data.astype("uint8")

        # TODO pretty sure I don't need this
        # TODO can't find any step where doing the histogram equalization helps
        # cdf = equalize_histogram(self.__image_data)
        # self.__image_data = cdf[self.__image_data]

    # def __equalize_histogram(self):
    #     # first create a histogram of the original image and it's
    #     max_pixel = np.amax(self.__band)
    #     hist, bins = np.histogram(self.__band.flatten(),
    #         max_pixel + 1, [0, max_pixel + 1])
    #
    #     # cumulative distribution function
    #     cdf = hist.cumsum()
    #
    #     # TODO only used for plotting??
    #     # cdf_normalized = cdf * hist.max() / cdf.max()
    #
    #     # create a masked version of cdf where 0 values are removed
    #     cdf_m = np.ma.masked_equal(cdf, 0)
    #     cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    #     # add the masked zero values back to the array
    #     cdf_adj = np.ma.filled(cdf_m, 0).astype('uint8')
    #
    #     self.__image_data = cdf_adj[self.__band]


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

        np.set_printoptions(8, formatter={'int_kind': '{:02x}'.format})
        print(self.__data)
        print("shape: ", self.__data.shape)
        print("h: ", self.__data.shape[0])
        print("w: ", self.__data.shape[1])
        print("size: ", self.__data.size)
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

