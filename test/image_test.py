import openspectra.image as img
import openspectra.openspectra_file as osf
from openspectra.openspectra_file import OpenSpectraFile
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt


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


def image_processor_test():
    file_name = "/Users/jconti/dev/data/JoeSamples/cup95_eff_fixed"

    open_spectra_file: OpenSpectraFile = osf.create_open_spectra_file(file_name)

    image_data = open_spectra_file.greyscale_image(10).raw_data()
    min = np.amin(image_data)
    max = np.amax(image_data)
    print("min {0}, max {1}, diff {2}".format(min, max, max - min))

    plt.hist(image_data.flatten(),
        np.amax(image_data) - np.amin(image_data),
        [np.amin(image_data), np.amax(image_data)],
        color='r')
    plt.xlim([0, np.amax(image_data)])
    plt.show()

    # img_eq = equalize_histogram(image_data)
    # image_eq = Image.fromarray(img_eq)
    # image_eq.show()

    # plt.hist(img_eq.flatten(),
    #     np.amax(img_eq) - np.amin(img_eq),
    #     [np.amin(img_eq), np.amax(img_eq)],
    #     color='g')
    # plt.xlim([0, np.amax(img_eq)])
    # plt.show()

    # img_adj = img.stretch_contrast(img_eq, 2, 98)
    # image_adj = Image.fromarray(img_adj)
    # image_adj.show()

    # plt.hist(img_adj.flatten(),
    #     np.amax(img_adj) - np.amin(img_adj),
    #     [np.amin(img_adj), np.amax(img_adj)],
    #     color='b')

    # plt.xlim([0, np.amax(img_adj)])
    # plt.show()

# TODO most of this doesn't work anymore, get rid of it?
if __name__ == "__main__":
    image_processor_test()