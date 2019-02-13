#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import math

import numpy as np
from numpy import ma
from matplotlib import pyplot as plt

from openspectra.openspectra_file import OpenSpectraFileFactory


def test_float_bands():
    file_name = "/Users/jconti/dev/data/JoeSamples/ang20160928t135411_rfl_v1nx_nonortho"
    osf = OpenSpectraFileFactory.create_open_spectra_file(file_name)

    # band_count = osf.header().band_count()
    # print("band num,min,max,mean,avg,std")
    # for band_index in range(0, band_count):
        # band = osf.raw_band(band_index)
        # if band.min() == np.nan or band.max() == np.nan or band.min() == np.inf or band.max() == np.inf or band.std() > 1.0:
        # print("{0},{1},{2},{3},{4},{5}".format(
                # band_index, band.min(), band.max(), band.mean(), np.average(band), band.std()))

    # TODO fwhm numbers in the header file maybe to help eval or fix up this noisy data? https://en.wikipedia.org/wiki/Full_width_at_half_maximum
    # band 292 apppears to be all noise
    # band_index = 292
    # band_index = 1
    # 202 has some inf and nan, masked_invalid gets them both
    band_index = 202
    band = osf.raw_image(band_index)
    print("raw band size: {0}".format(band.size))
    min = band.min()
    print(math.isnan(min))
    print("band num: {0}, min: {1}, max: {2}, mean: {3}, avg: {4}, std: {5}".format(
            band_index, band.min(), band.max(), band.mean(), np.average(band), band.std()))

    fixed_band = ma.masked_invalid(band)
    print("invalid masked size: {0}".format(fixed_band[~fixed_band.mask].size))
    print("band num: {0}, min: {1}, max: {2}, mean: {3}, avg: {4}, std: {5}".format(
            band_index, fixed_band.min(), fixed_band.max(), fixed_band.mean(), np.average(fixed_band), fixed_band.std()))

    # Eorror when plotting,
    # / Users / jconti /.virtualenvs / OpenSpectra / lib / python3.6 / site - packages / numpy / lib / function_base.py: 780: RuntimeWarning: invalid value encountered in greater_equal keep = (tmp_a >= first_edge)
    # / Users / jconti /.virtualenvs / OpenSpectra / lib / python3.6 / site - packages / numpy / lib / function_base.py: 781: RuntimeWarning: invalid value encountered in less_equal keep &= (tmp_a <= last_edge)
    # plt.hist(fixed_band.flatten(), 1024, (fixed_band.min(), fixed_band.max()))
    # plt.show()

    # fixed_band = ma.masked_outside(fixed_band, -1, 5)
    # fixed_band = ma.masked_outside(fixed_band, -1, 1)
    # fixed_band = ma.masked_outside(fixed_band, -0.25, 0.25)
    # fixed_band = ma.masked_outside(fixed_band, -0.01, 0.01)
    # fixed_band = ma.masked_outside(fixed_band, -1000000, 7000000)
    # print("-1, 5 masked size: {0}".format(fixed_band[~fixed_band.mask].size))
    # print("band num: {0}, min: {1}, max: {2}, mean: {3}, avg: {4}, std: {5}".format(
    #         band_index, fixed_band.min(), fixed_band.max(), fixed_band.mean(), np.average(fixed_band), fixed_band.std()))

    # plt.hist(fixed_band.flatten(), 1024)
    # plt.show()


if __name__ == "__main__":
    test_float_bands()
