#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import logging
from enum import Enum
from typing import Union, Dict

import numpy as np

from openspectra.utils import LogHelper, OpenSpectraDataTypes, OpenSpectraProperties, Logger
from openspectra.openspectra_file import LinearImageStretch, ValueStretch, PercentageStretch


class Band(Enum):
    GREY = None
    RED = 1
    GREEN = 2
    BLUE = 3


class RGBLimits:

    def __init__(self, red:Union[int, float], green:Union[int, float], blue:Union[int, float]):
        self.__red:Union[int, float] = red
        self.__green:Union[int, float] = green
        self.__blue:Union[int, float] = blue

    def red(self) -> Union[int, float]:
        return self.__red

    def green(self) -> Union[int, float]:
        return self.__green

    def blue(self) -> Union[int, float]:
        return self.__blue


class ImageAdjuster:

    def adjust_by_percentage(self, lower:Union[int, float], upper:Union[int, float], band:Band):
        pass

    def adjust_by_value(self, lower:Union[int, float], upper:Union[int, float], band:Band):
        pass

    def adjust(self):
        pass

    def reset_stretch(self, band:Band):
        pass

    def low_cutoff(self, band:Band) -> Union[Union[int, float], RGBLimits]:
        pass

    def set_low_cutoff(self, limit:Union[int, float], band:Band):
        pass

    def high_cutoff(self, band:Band) -> Union[Union[int, float], RGBLimits]:
        pass

    def set_high_cutoff(self, limit:Union[int, float], band:Band):
        pass

    def is_updated(self, band:Band) -> bool:
        pass


class BandImageAdjuster(ImageAdjuster):

    __LOG:Logger = LogHelper.logger("BandImageAdjuster")

    def __init__(self, band:np.ndarray, data_ignore_value:Union[int, float]=None,
            default_stretch:LinearImageStretch=None):

        self.__band = band
        self.__data_ignore_vale = data_ignore_value
        self.__type = self.__band.dtype
        self.__image_data = None
        self.__low_cutoff = 0
        self.__high_cutoff = 0

        # Do the initial stretch
        self.__default_stretch = default_stretch
        self.__do_default_stretch()
        self.adjust()

        BandImageAdjuster.__LOG.debug("type: {0}", self.__type)
        BandImageAdjuster.__LOG.debug("min: {0}, max: {1}", self.__band.min(), self.__band.max())

    def __do_default_stretch(self):
        if self.__default_stretch is not None:
            if isinstance(self.__default_stretch, PercentageStretch):
                percentage = self.__default_stretch.percentage()
                self.adjust_by_percentage(percentage, 100 - percentage)
            elif isinstance(self.__default_stretch, ValueStretch):
                self.set_low_cutoff(self.__default_stretch.low())
                self.set_high_cutoff(self.__default_stretch.high())
            else:
                BandImageAdjuster.__LOG.warning(
                    "Received unknown type {0} of image stretch, defaulting to 2%".
                        format(type(self.__default_stretch)))
                self.adjust_by_percentage(2, 98)
        else:
            self.adjust_by_percentage(2, 98)

        self.__updated = True

    def adjusted_data(self) -> np.ndarray:
        return self.__image_data

    def reset_stretch(self, band:Band=None):
        """band is ignore here if passed"""
        self.__do_default_stretch()

    def adjust_by_percentage(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """band is ignore here if passed"""
        if self.__type in OpenSpectraDataTypes.Ints:
            self.__low_cutoff, self.__high_cutoff = np.percentile(self.__band, (lower, upper))
            self.__updated = True
        elif self.__type in OpenSpectraDataTypes.Floats:
            self.__calculate_float_cutoffs(lower, upper)
            self.__updated = True
        else:
            raise TypeError("Image data type {0} not supported".format(self.__type))

    def adjust_by_value(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """band is ignore here if passed"""
        self.__low_cutoff = lower
        self.__high_cutoff = upper
        self.__updated = True

    def low_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        """band is ignore here if passed"""
        return self.__low_cutoff

    def set_low_cutoff(self, limit, band:Band=None):
        """band is ignore here if passed"""
        self.__low_cutoff = limit
        self.__updated = True

    def high_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        """band is ignore here if passed"""
        return self.__high_cutoff

    def set_high_cutoff(self, limit, band:Band=None):
        """band is ignore here if passed"""
        self.__high_cutoff = limit
        self.__updated = True

    def adjust(self):
        if self.__updated:
            BandImageAdjuster.__LOG.debug("low cutoff: {0}, high cutoff: {1}, data ignore value: {2}",
                self.low_cutoff(), self.high_cutoff(), self.__data_ignore_vale)

            if self.low_cutoff() != self.high_cutoff():
                ignore_mask = None
                if self.__data_ignore_vale is not None:
                    ignore_mask = np.ma.getmask(np.ma.masked_equal(self.__band, self.__data_ignore_vale))
                    # BandImageAdjuster.__LOG.debug("Created ignore value mask: {0}".format(ignore_mask))

                # <= or <, looks like <=, with < there are strange dots on the image
                low_mask = np.ma.getmask(np.ma.masked_where(self.__band <= self.__low_cutoff, self.__band, False))

                # >= or <, looks like >=, with < I there are dots on the image
                high_mask = np.ma.getmask(np.ma.masked_where(self.__band >= self.__high_cutoff, self.__band, False))

                full_mask = low_mask | high_mask
                masked_band = np.ma.masked_where(full_mask, self.__band, True)

                # 0 and 256 assumes 8-bit images, the pixel value limits
                # TODO why didn't 255 work?
                A, B = 0, 256
                masked_band = ((masked_band - self.__low_cutoff) * ((B - A) / (self.__high_cutoff - self.__low_cutoff)) + A)

                # Set the low and high masked values to white and black
                masked_band[low_mask] = 0
                masked_band[high_mask] = 255

                # Set ignored values to black
                if ignore_mask is not None and np.ma.is_mask(ignore_mask):
                    # BandImageAdjuster.__LOG.debug("Applied ignore value mask: {0}".format(ignore_mask))
                    masked_band[ignore_mask] = 0
            else:
                masked_band = np.ma.masked_not_equal(self.__band, 0)
                masked_band[masked_band.mask] = 0

            self.__image_data = masked_band.astype("uint8")
            self.__updated = False

    def is_updated(self, band:Band=None) -> bool:
        """Returns true if the image parameters have been updated but adjust()
        has not been called.  The band parameter is ignored here"""
        return self.__updated

    def __calculate_float_cutoffs(self, lower:Union[int, float], upper:Union[int, float]):
        nbins = OpenSpectraProperties.FloatBins
        min = self.__band.min()
        max = self.__band.max()

        # scale to generate histogram data
        hist_scaled = np.floor((self.__band - min)/(max - min) * (nbins - 1))
        scaled_low_cut, scaled_high_cut = np.percentile(hist_scaled, (lower, upper))

        self.__low_cutoff = (scaled_low_cut / (nbins - 1) * (max - min)) + min
        self.__high_cutoff = (scaled_high_cut / (nbins - 1) * (max - min)) + min


class RGBImageAdjuster(ImageAdjuster):

    def __init__(self, red: np.ndarray, green: np.ndarray, blue: np.ndarray,
            red_default_stretch:LinearImageStretch=None, green_default_stretch:LinearImageStretch=None,
            blue_default_stretch:LinearImageStretch=None, data_ignore_value:Union[int, float]=None):
        self.__adjusted_bands = {Band.RED: BandImageAdjuster(red, data_ignore_value, red_default_stretch),
                                 Band.GREEN: BandImageAdjuster(green, data_ignore_value, green_default_stretch),
                                 Band.BLUE: BandImageAdjuster(blue, data_ignore_value, blue_default_stretch)}

    def _adjusted_data(self, band:Band) -> np.ndarray:
        return self.__adjusted_bands[band].adjusted_data()

    def adjust_by_percentage(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is not None:
            self.__adjusted_bands[band].adjust_by_percentage(lower, upper)
        else:
            self.__adjusted_bands[Band.RED].adjust_by_percentage(lower, upper)
            self.__adjusted_bands[Band.GREEN].adjust_by_percentage(lower, upper)
            self.__adjusted_bands[Band.BLUE].adjust_by_percentage(lower, upper)

    def adjust_by_value(self, lower:Union[int, float], upper:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is None:
            self.__adjusted_bands[Band.RED].adjust_by_value(lower, upper)
            self.__adjusted_bands[Band.GREEN].adjust_by_value(lower, upper)
            self.__adjusted_bands[Band.BLUE].adjust_by_value(lower, upper)
        else:
            self.__adjusted_bands[band].adjust_by_value(lower, upper)

    def reset_stretch(self, band:Band=None):
        """If band is None reset stretch for all three bands, otherwise
        reset only the given band"""
        if band is None:
            self.__adjusted_bands[Band.RED].reset_stretch()
            self.__adjusted_bands[Band.GREEN].reset_stretch()
            self.__adjusted_bands[Band.BLUE].reset_stretch()
        else:
            self.__adjusted_bands[band].reset_stretch()

    def adjust(self):
        """Adjust all three bands, if the band is not out of date
        no adjustment calculation will be made"""
        self.__adjusted_bands[Band.RED].adjust()
        self.__adjusted_bands[Band.GREEN].adjust()
        self.__adjusted_bands[Band.BLUE].adjust()

    def low_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        if band is None:
            return RGBLimits(self.__adjusted_bands[Band.RED].low_cutoff(),
                    self.__adjusted_bands[Band.GREEN].low_cutoff(),
                    self.__adjusted_bands[Band.BLUE].low_cutoff())
        else:
            return self.__adjusted_bands[band].low_cutoff()

    def set_low_cutoff(self, limit:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is None:
            self.__adjusted_bands[Band.RED].set_low_cutoff(limit)
            self.__adjusted_bands[Band.GREEN].set_low_cutoff(limit)
            self.__adjusted_bands[Band.BLUE].set_low_cutoff(limit)
        else:
            self.__adjusted_bands[band].set_low_cutoff(limit)

    def high_cutoff(self, band:Band=None) -> Union[Union[int, float], RGBLimits]:
        if band is None:
            return RGBLimits(self.__adjusted_bands[Band.RED].high_cutoff(),
                    self.__adjusted_bands[Band.GREEN].high_cutoff(),
                    self.__adjusted_bands[Band.BLUE].high_cutoff())
        else:
            return self.__adjusted_bands[band].high_cutoff()

    def set_high_cutoff(self, limit:Union[int, float], band:Band=None):
        """If band is None apply new limits to all three bands, otherwise
        apply it to only the given band"""
        if band is None:
            self.__adjusted_bands[Band.RED].set_high_cutoff(limit)
            self.__adjusted_bands[Band.GREEN].set_high_cutoff(limit)
            self.__adjusted_bands[Band.BLUE].set_high_cutoff(limit)
        else:
            self.__adjusted_bands[band].set_high_cutoff(limit)

    def is_updated(self, band:Band=None) -> bool:
        """Returns True if any of the bands or the passed band have had
        their parameters updated but the band has not had adjust() called"""
        if band is not None:
            self.__adjusted_bands[band].is_updated()
        else:
            return self.__adjusted_bands[Band.RED].is_updated() or \
                self.__adjusted_bands[Band.GREEN].is_updated() or \
                self.__adjusted_bands[Band.BLUE].is_updated()


class BandDescriptor:

    def __init__(self, file_name:str, band_name:str, wavelength_label:str,
            bad_band:bool=False, data_ignore_value:Union[int, float]=None,
            default_stretch:LinearImageStretch=None):
        self.__file_name = file_name
        self.__band_name = band_name
        self.__wavelength_label = wavelength_label
        self.__band_label = self.__band_name + " - " + self.__wavelength_label
        self.__label = self.__file_name + " - " + \
            self.__band_name + " - " + self.__wavelength_label
        self.__is_bad = bad_band
        self.__data_ignore_value = data_ignore_value
        self.__default_stretch = default_stretch

    def file_name(self) -> str:
        return self.__file_name

    def band_name(self) -> str:
        return self.__band_name

    def band_label(self) -> str:
        return self.__band_label

    def wavelength_label(self) -> str:
        return self.__wavelength_label

    def label(self) -> str:
        return self.__label

    def is_bad_band(self) -> bool:
        return self.__is_bad

    def data_ignore_value(self) -> Union[int, float]:
        return self.__data_ignore_value

    def default_stretch(self) -> LinearImageStretch:
        return self.__default_stretch


# TODO need to think through how much data we're holding here, clean up, views?
class Image(ImageAdjuster):

    def image_data(self, band:Band) -> np.ndarray:
        pass

    def raw_data(self, band:Band) -> np.ndarray:
        pass

    def image_shape(self) -> (int, int):
        pass

    def bytes_per_line(self) -> int:
        pass

    def label(self, band:Band) -> str:
        pass

    def descriptor(self) -> BandDescriptor:
        pass


class GreyscaleImage(Image, BandImageAdjuster):
    """An 8-bit 8-bit grayscale image"""

    def __init__(self, band:np.ndarray, band_descriptor:BandDescriptor):
        super().__init__(band, band_descriptor.data_ignore_value(), band_descriptor.default_stretch())
        self.__band = band
        self.__band_descriptor = band_descriptor

    def adjusted_data(self) -> np.ndarray:
        """Do not call this method, it's an unfortunate consequence of needing
        it to be public on BandImageAdjuster for use by RGBImageAdjuster"""
        raise NotImplementedError("Do not call GreyscaleImage.adjusted_data(), use GreyscaleImage.image_data() instead")

    def image_data(self, band:Band=None) -> np.ndarray:
        """band is ignored here if passed"""
        if self.is_updated():
            self.adjust()
        return super().adjusted_data()

    # TODO Warning returns view of the original data?!
    def raw_data(self, band:Band=None) -> np.ndarray:
        """band is ignored here if passed"""
        return self.__band

    def image_shape(self) -> (int, int):
        return self.image_data().shape

    def bytes_per_line(self) -> int:
        return self.image_data().shape[1]

    def label(self, band:Band=None) -> str:
        """band is ignored here if passed"""
        return self.__band_descriptor.label()

    def descriptor(self) -> BandDescriptor:
        return self.__band_descriptor


# this is definately not thread safe
class RGBImage(Image, RGBImageAdjuster):
    """A 32-bit RGB image using format (0xffRRGGBB)"""

    __LOG:Logger = LogHelper.logger("RGBImage")

    __HIGH_BYTE = 255 * 256 * 256 * 256
    __RED_SHIFT = 256 * 256
    __GREEN_SHIFT = 256

    def __init__(self, red:np.ndarray, green:np.ndarray, blue:np.ndarray,
            red_descriptor:BandDescriptor, green_descriptor:BandDescriptor, blue_descriptor:BandDescriptor):
        if not ((red.size == green.size == blue.size) and
                (red.shape == green.shape == blue.shape)):
            raise ValueError("All bands must have the same size and shape")
        super().__init__(red, green, blue, red_descriptor.default_stretch(), green_descriptor.default_stretch(),
            blue_descriptor.default_stretch(), red_descriptor.data_ignore_value())

        self.__descriptors = {Band.RED: red_descriptor,
                         Band.GREEN: green_descriptor,
                         Band.BLUE: blue_descriptor}

        self.__labels = {Band.RED: red_descriptor.band_label(),
                         Band.GREEN: green_descriptor.band_label(),
                         Band.BLUE: blue_descriptor.band_label()}
        self.__label:str = ""
        if red_descriptor is not None: self.__label += red_descriptor.band_label() + " "
        if green_descriptor is not None: self.__label += green_descriptor.band_label() + " "
        if blue_descriptor is not None: self.__label += blue_descriptor.band_label()
        if self.__label is not None: self.__label = self.__label.strip()

        self.__bands = {Band.RED: red, Band.GREEN: green, Band.BLUE: blue}
        self.__high_bytes = np.full(red.shape, RGBImage.__HIGH_BYTE, np.uint32)

        self.__calculate_image()

        if RGBImage.__LOG.isEnabledFor(logging.DEBUG):
            np.set_printoptions(8, formatter={'int_kind': '{:02x}'.format})
            RGBImage.__LOG.debug("{0}", self.__image_data)
            RGBImage.__LOG.debug("height: {0}", self.__image_data.shape[0])
            RGBImage.__LOG.debug("width: {0}", self.__image_data.shape[1])
            RGBImage.__LOG.debug("size: {0}", self.__image_data.size)
            np.set_printoptions()

    def adjust(self):
        if super().is_updated():
            super().adjust()
            self.__calculate_image()

    def image_data(self, band:Band=None) -> np.ndarray:
        """If band is None returns all three bands as a single image data set
        If band is supplied returns the adjusted image data for that band"""
        if super().is_updated():
            super().adjust()
            self.__calculate_image()

        if band is not None:
            return self._adjusted_data(band)
        else:
            return self.__image_data

    # TODO Warning returns view of the original data?!
    def raw_data(self, band:Band) -> np.ndarray:
        # TODO so this returns a view that could allow the user to alter the underlying data
        # TODO Although I'm not sure what that would do in the case of a memmap??
        return self.__bands[band]

    def image_shape(self) -> (int, int):
        return self.__image_data.shape

    def bytes_per_line(self) -> int:
        return self.__image_data.shape[1] * 4

    def descriptor(self, band:Band=None) -> Union[BandDescriptor, Dict[Band, BandDescriptor]]:
        if band is None:
            return self.__descriptors.copy()
        else:
            return self.__descriptors[band]

    def label(self, band:Band=None) -> str:
        if band is None:
            return self.__label
        else:
            return self.__labels[band]

    def __calculate_image(self):
        self.__image_data = self.__high_bytes + \
                            self._adjusted_data(Band.RED).astype(np.uint32) * RGBImage.__RED_SHIFT + \
                            self._adjusted_data(Band.GREEN).astype(np.uint32) * RGBImage.__GREEN_SHIFT + \
                            self._adjusted_data(Band.BLUE).astype(np.uint32)
