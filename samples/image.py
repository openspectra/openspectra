#  Developed by Joseph M. Conti and Joseph W. Boardman on 2/22/19 6:16 PM.
#  Last modified 2/22/19 6:16 PM
#  Copyright (c) 2019. All rights reserved.
import os
from pathlib import Path

import numpy as np
from PIL import Image

from openspectra.image import Image as OSImage
from openspectra.openspecrtra_tools import OpenSpectraImageTools
from openspectra.openspectra_file import OpenSpectraFileFactory, OpenSpectraFile, OpenSpectraHeader
from samples import project_path


def image_sample():
    # Specify the file we want to open, note project_path is defined
    # in this package's __init__.py file to make things a bit easier
    file_name = str(project_path) + "/test/unit_tests/resources/cup95_eff_fixed"

    # Use the OpenSpectraFileFactory to create an OpenSpectraFile from
    # from a data file on disk.  Note the data file's header is expected to
    # be in the same directory as the data file and have the same
    # base name with the extension .hdr
    os_file:OpenSpectraFile = OpenSpectraFileFactory.create_open_spectra_file(file_name)

    # You can get the raw data for any image in the file by calling raw_image and
    # passing the band you want.  In this context the band is just an index into
    # the data cube.  Indexing starts at 0 and goes to number of bands - 1
    # Be sure to read the doc in OpenSpectraFile regarding what is returned here
    # It's safe to do math on the array returned as the results will be a new
    # array that is the result of the operation but take care not the change the
    # values in the array itself
    band:int = 1
    raw_image:np.ndarray = os_file.raw_image(band)

    # Uncomment to see what it looks like
    # print("raw image", raw_image)

    # Math on the raw image data returns a new array of data
    my_new_data = raw_image * 5

    # Uncomment to see what is looks like
    # print("raw image * 5", my_new_data)

    # To find out information about the the band at each index and the total
    # number of bands in the data you need to check the header which
    # you can get from the os_file
    os_header:OpenSpectraHeader = os_file.header()

    # The header will give you the total number of bands.  So the maximum
    # valid index that can be used to retrieve raw_data or an image (see below)
    # is band_count - 1
    band_count = os_header.band_count()
    print("band count {0}".format(band_count))

    # You can get all the band names and labels
    # Band labels is a list of all band name with their wavelength
    band_labels = os_header.band_labels()

    # Uncomment to see what they look like
    # print("band labels", band_labels)

    # Band names is a list with just the band names
    band_names = os_header.band_names()

    # Uncomment to see what they look like
    # print("band names", band_names)

    # Or we can get the label (or name) of just the single band we want
    band_label = os_header.band_label(band)
    print("band name {0}, wavelenght {1}".format(band_label[0], band_label[1]))

    # Instead of operating on the image data directly, if want and image
    # from the file we can use OpenSpectraImageTools.  Create to tools object
    # by passing it our os_file
    image_tools:OpenSpectraImageTools = OpenSpectraImageTools(os_file)

    # We can create an OpenSpectra Image object by pass the OpenSpectraImageTools
    # our band of interest
    grey_os_image:OSImage = image_tools.greyscale_image(band)

    # From the OpenSpectra Image object we can obtain adjusted image data
    # suitable for display.  One easy way to show that image is using Python's
    # Pillow module
    greyscale_image = Image.fromarray(grey_os_image.image_data())

    # This should open the image in a system default viewer
    greyscale_image.show("Greyscale Image")

    # We can also create an RGB image using three bands from the data file.
    # And we can provide labels for the bands when we create the image that
    # can be used when we display it
    red_band = 1
    green_band = 10
    blue_band = 20

    # Make sure all of our band choices are in range.
    assert blue_band < band_count

    # Create the image using the band indexes and provide the corresponding
    # band names to identify the bands in the image
    rgb_os_image = image_tools.rgb_image(red_band, green_band, blue_band,
        os_header.band_name(red_band), os_header.band_name(green_band),
        os_header.band_name(blue_band))
    # Create the Pillow image
    rgb_image = Image.fromarray(rgb_os_image.image_data(), "RGBA")
    # Now we can show the image using the band name label in the title
    # Note the default system viewer may not display the title
    rgb_image.show("RGB Image from {0}".format(rgb_os_image.label()))


if __name__ == "__main__":
    """To run this sample from the command line first cd to the OpenSpectra project
    directory and use the following command:
    python -m samples.image_test"""
    image_sample()
