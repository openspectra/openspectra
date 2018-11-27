import openspectra.image as img
import openspectra.openspectra_file as osf
from openspectra.openspectra_file import OpenSpectraFile
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt


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

    img_eq = img.equalize_histogram(image_data)
    image_eq = Image.fromarray(img_eq)
    image_eq.show()

    plt.hist(img_eq.flatten(),
        np.amax(img_eq) - np.amin(img_eq),
        [np.amin(img_eq), np.amax(img_eq)],
        color='g')
    plt.xlim([0, np.amax(img_eq)])
    plt.show()

    img_adj = img.stretch_contrast(img_eq, 2, 98)

    image_adj = Image.fromarray(img_adj)
    image_adj.show()

    plt.hist(img_adj.flatten(),
        np.amax(img_adj) - np.amin(img_adj),
        [np.amin(img_adj), np.amax(img_adj)],
        color='b')

    plt.xlim([0, np.amax(img_adj)])
    plt.show()