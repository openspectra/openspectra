import openspectra.openspectra_file as ef
from openspectra.openspectra_file import OpenSpectraFile
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt


if __name__ == "__main__":
    file_name = "/Users/jconti/dev/data/JoeSamples/cup95_eff_fixed"
    # file_name = "/Users/jconti/dev/data/JoeSamples/ang20160928t135411_rfl_v1nx_nonortho"

    open_spectra_file:OpenSpectraFile = ef.create_open_spectra_file(file_name)

    image_data = open_spectra_file.greyscale_image(10).raw_data()
    min = np.amin(image_data)
    max = np.amax(image_data)
    print("min {0}, max {1}, diff {2}".format(min, max, max - min))

    a = 0
    b = 255
    p2, p98 = np.percentile(image_data, (2, 98))

    print(p2, p98)

    img_adj = ((image_data - p2) * ((b - a) / (p98 - p2)) + a).astype("uint8")
    min = np.amin(img_adj)
    max = np.amax(img_adj)
    print("min {0}, max {1}, diff {2}".format(min, max, max - min))

    image = Image.fromarray(img_adj)
    image.show()

    plt.hist(img_adj.flatten(),
        np.amax(img_adj) - np.amin(img_adj),
        [np.amin(img_adj), np.amax(img_adj)],
        color='b')

    plt.xlim([0, np.amax(img_adj)])
    plt.show()