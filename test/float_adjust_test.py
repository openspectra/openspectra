#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import numpy as np
from matplotlib import pyplot as plt
from numpy import ma

from openspecrtra_tools import OpenSpectraImageTools
from openspectra.openspectra_file import OpenSpectraFileFactory
from openspectra.utils import OpenSpectraProperties


def test_float_adj():

    file_name = "/Users/jconti/dev/data/JoeSamples/ang20160928t135411_rfl_v1nx_nonortho"
    osf = OpenSpectraFileFactory.create_open_spectra_file(file_name)
    image_tools = OpenSpectraImageTools(osf)

    gs_image = image_tools.greyscale_image(1)
    float_data = gs_image.raw_data()
    print(float_data)

    # define number of bins
    nbins = OpenSpectraProperties.get_property("FloatBins", 512)

    plt.hist(float_data.flatten(), nbins,
        [float_data.min(), float_data.max()])
    plt.show()

    min = float_data.min()
    max = float_data.max()
    print(min, max)

    # scale to generate histogram data
    hist_scaled = np.floor((float_data - min)/(max - min) * (nbins - 1))
    print(hist_scaled)
    print(hist_scaled.min(), hist_scaled.max())

    plt.hist(hist_scaled.flatten(), nbins,
        [hist_scaled.min(), hist_scaled.max()])
    plt.show()

    scaled_low_cut, scaled_high_cut = np.percentile(hist_scaled, (2, 98))
    print(scaled_low_cut, scaled_high_cut)

    low_cut = (scaled_low_cut / (nbins - 1) * (max - min)) + min
    high_cut = (scaled_high_cut / (nbins - 1) * (max - min)) + min

    print(low_cut, high_cut)

    image_data = float_data.copy()
    low_mask = image_data.view(ma.MaskedArray)
    low_mask.mask = [image_data <= low_cut]

    high_mask = image_data.view(ma.MaskedArray)
    high_mask.mask = [image_data >= high_cut]

    print(low_mask)
    print(high_mask)

    low_mask[low_mask.mask] = 0
    high_mask[high_mask.mask] = 255

    print(low_mask)
    print(high_mask)


if __name__ == "__main__":
    test_float_adj()