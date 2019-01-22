#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import openspectra.openspectra_file as osf
from openspectra.openspectra_file import OpenSpectraFile
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image


def adjust_orig(cdf:np.ndarray) -> np.ndarray:
    # create a masked version of cdf where 0 values are removed
    cdf_m = np.ma.masked_equal(cdf, 0)
    cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    # add the masked zero values back to the array
    return np.ma.filled(cdf_m, 0).astype('uint8')


# TODO so this porbably is incorrect, the end clipping is contrast stretching??
def adjust_new(cdf:np.ndarray) -> np.ndarray:
    # TODO still have to figure out how to compute these limits for real
    # TODO maybe not the right place to do the end clipping
    cdf_m = np.ma.masked_outside(cdf, np.amin(cdf) + 5000, np.amax(cdf) - 5000)
    cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    mid = np.floor_divide(cdf.size, 2)
    return np.concatenate((np.ma.filled(cdf_m[:mid], 0),
                           np.ma.filled(cdf_m[mid:], 255))).astype('uint8')


# derived from https://docs.opencv.org/3.1.0/d5/daf/tutorial_py_histogram_equalization.html
if __name__ == '__main__':
    file_name = "/Users/jconti/dev/data/JoeSamples/cup95_eff_fixed"
    # file_name = "/Users/jconti/dev/data/JoeSamples/ang20160928t135411_rfl_v1nx_nonortho"

    open_spectra_file:OpenSpectraFile = osf.create_open_spectra_file(file_name)

    image_data = open_spectra_file.greyscale_image(10).raw_data()
    min = np.amin(image_data)
    max = np.amax(image_data)
    print("min {0}, max {1}, diff {2}".format(min, max, max - min))

    # first create a histogram of the original image and it's
    # cumulative distribution function
    hist, bins = np.histogram(image_data.flatten(),
        max + 1 - 0, [0, max + 1])

    cdf = hist.cumsum()
    cdf_normalized = cdf * hist.max() / cdf.max()

    # plt.plot(cdf, color='g')
    plt.plot(cdf_normalized, color='b')

    plt.hist(image_data.flatten(),
        np.amax(image_data) - np.amin(image_data),
        [np.amin(image_data), np.amax(image_data)],
        color='r')

    # now actually manipulate the image
    cdf = adjust_orig(cdf)
    # cdf = adjust_new(cdf)
    plt.plot(cdf, color='g')

    plt.xlim([0, np.amax(image_data)])
    # plt.legend(('cdf, normalized cdf', 'histogram'), loc='upper left')
    plt.legend(("normalized cdf", "scaled cdf", "histogram"), loc="upper left")
    plt.show()

    # Now do the adjustment
    # TODO this somehow transforms each input pixel, image_data, to an output
    # TODO pixel in img2??
    img2 = cdf[image_data]

    # now recalculate the the graph output for the adjusted image
    hist_adj, bins_adj = np.histogram(img2.flatten(), np.amax(img2),
        [0, np.amax(img2) + 1])

    cdf_new = hist_adj.cumsum()
    cdf_normalized = cdf_new * hist_adj.max() / cdf_new.max()
    plt.plot(cdf_normalized, color='r')

    plt.hist(img2.flatten(),
        np.amax(img2) - np.amin(img2),
        [np.amin(img2), np.amax(img2)],
        color='b')

    plt.xlim([0, np.amax(img2)])
    plt.show()

    image = Image.fromarray(img2)
    image.show()
