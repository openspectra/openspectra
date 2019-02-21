#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import openspectra.openspectra_file as osf
from openspectra.openspectra_file import OpenSpectraFile
import numpy as np
# from PIL import Image
from matplotlib import pyplot as plt

# TODO decide is this need to be kept around
if __name__ == "__main__":
    pass
    # file_name = "/Users/jconti/dev/data/JoeSamples/cup95_eff_fixed"
    # open_spectra_file:OpenSpectraFile = osf.create_open_spectra_file(file_name)
    #
    # image_data = open_spectra_file.raw_image(10)
    # min = np.amin(image_data)
    # max = np.amax(image_data)
    # print("min {0}, max {1}, diff {2}".format(min, max, max - min))
    #
    # a = 0
    # b = 255
    # p2, p98 = np.percentile(image_data, (2, 98))
    #
    # print(p2, p98)
    #
    # img_adj = ((image_data - p2) * ((b - a) / (p98 - p2)) + a).astype("uint8")
    # min = np.amin(img_adj)
    # max = np.amax(img_adj)
    # print("min {0}, max {1}, diff {2}".format(min, max, max - min))
    #
    # image = Image.fromarray(img_adj)
    # image.show()
    #
    # plt.hist(img_adj.flatten(),
    #     np.amax(img_adj) - np.amin(img_adj),
    #     [np.amin(img_adj), np.amax(img_adj)],
    #     color='b')
    #
    # plt.xlim([0, np.amax(img_adj)])
    # plt.show()