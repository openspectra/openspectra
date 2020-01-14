import unittest

import numpy as np

from openspectra.openspectra_file import OpenSpectraFileFactory


def scan_bands(file_name:str, lower_limit:float, upper_limit:float):
    os_file = OpenSpectraFileFactory.create_open_spectra_file(file_name)
    header = os_file.header()
    bbl = "bbl = {"
    for index in range(0, header.band_count()):
        image:np.ndarray = os_file.raw_image(index)

        min = np.min(image)
        max = np.max(image)
        bad_band = 1
        if np.isnan(min) or np.isnan(max) or np.isinf(min) or np.isinf(max) or min < lower_limit or max > upper_limit:
            bad_band = 0

        # print("{} {} {} {}".format(index, bad_band, np.min(image), np.max(image)))
        bbl += "{},".format(bad_band)

    bbl = bbl[:-1]
    bbl += "}"
    print(bbl)


if __name__ == '__main__':
    """A simple utility to scan float files for out of range values, 
    set lower and upper limits below.  Generates and prints out a bad band list, bbl, 
    that can be used in the file's header."""
    test_file = ""
    scan_bands(test_file, -2.0, 10.0)
