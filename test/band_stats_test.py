import numpy as np

from openspectra.openspectra_file import OpenSpectraFile, OpenSpectraFileFactory


def band_stats_test():
    file_name = "/Users/jconti/dev/data/JoeSamples/cup95_eff_fixed"

    os_file: OpenSpectraFile = OpenSpectraFileFactory.create_open_spectra_file(file_name)

    bands = os_file.band(10, 10)
    print("Bands: ", bands)

    bands = os_file.band((10, 10), (10, 11))
    print("Bands: ", bands)
    print("Bands[0]: ", bands[0])
    print("Bands[1]: ", bands[1])

    # slice bands to get all values from same wavelength
    print("Bands[:, 0]: ", bands[:, 0])
    print("Bands[:, 1]: ", bands[:, 1])
    print("Bands[:, 2]: ", bands[:, 2])

    # mean of one wavelength
    print("Bands[:, 0].mean(): ", bands[:, 0].mean())
    print("Bands[:, 1].mean(): ", bands[:, 1].mean())
    print("Bands[:, 2].mean(): ", bands[:, 2].mean())

    # mean of all wavelengths at once
    print("np.mean(bands, 0): ", np.mean(bands, 0))

    # mean of all wavelengths at once the OO way
    mean = bands.mean(0)
    print("bands.mean(0): ", mean)

    print("min: ", bands.min(0))
    print("max: ", bands.max(0))

    std = bands.std(0)
    print("std: ", std)
    print("+: ", mean + std)
    print("-: ", mean - std)


if __name__ == '__main__':
    band_stats_test()
