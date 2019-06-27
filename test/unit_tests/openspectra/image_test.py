#  Developed by Joseph M. Conti and Joseph W. Boardman on 6/26/19, 12:21 AM.
#  Last modified 6/26/19, 12:21 AM
#  Copyright (c) 2019. All rights reserved.
import unittest

import numpy as np

from openspectra.image import BandDescriptor, BandImageAdjuster
from openspectra.openspectra_file import OpenSpectraFileFactory


class BandDescriptorTest(unittest.TestCase):

    def test_defaults(self):
        descriptor = BandDescriptor("file_name", "band_name", "wavelength_label")
        self.assertEqual(descriptor.file_name(), "file_name")
        self.assertEqual(descriptor.band_name(), "band_name")
        self.assertEqual(descriptor.band_label(), "band_name - wavelength_label")
        self.assertEqual(descriptor.wavelength_label(), "wavelength_label")
        self.assertEqual(descriptor.label(), "file_name - band_name - wavelength_label")
        self.assertEqual(descriptor.is_bad_band(), False)
        self.assertTrue(descriptor.data_ignore_value() is None)

    def test_optionals(self):
        descriptor = BandDescriptor("file_name", "band_name", "wavelength_label", True, -999)
        self.assertEqual(descriptor.is_bad_band(), True)
        self.assertEqual(descriptor.data_ignore_value(), -999)

        descriptor = BandDescriptor("file_name", "band_name", "wavelength_label", True, -999.0)
        self.assertEqual(descriptor.data_ignore_value(), -999.0)


class BandImageAdjusterTest(unittest.TestCase):
    def setUp(self) -> None:
        test_file = "test/unit_tests/resources/cup95_eff_fixed_offset_1k"
        # To run in IDE use this path
        # test_file = "../resources/cup95_eff_fixed_offset_1k"
        self.__os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)

    def test_ignore_value(self):
        test_band = 9
        header = self.__os_file.header()
        band_label = header.band_label(test_band)
        self.assertEqual(band_label, ("Band 181", "2.081000"))

        raw_image = self.__os_file.raw_image(test_band)
        self.assertIsNotNone(raw_image)

        band_adjuster = BandImageAdjuster(raw_image)
        adjust_image = band_adjuster.adjusted_data()
        self.assertIsNotNone(adjust_image)
        self.assertTrue(np.ma.isMaskedArray(adjust_image))
        self.assertEqual(adjust_image[181, 326], 255)

        band_adjuster = BandImageAdjuster(raw_image, 709)
        adjust_image = band_adjuster.adjusted_data()
        self.assertIsNotNone(adjust_image)
        self.assertTrue(np.ma.isMaskedArray(adjust_image))
        self.assertEqual(adjust_image[181, 326], 0)


class RGBImageAdjusterTest(unittest.TestCase):
    # TODO
    pass


class GreyscaleImageTest(unittest.TestCase):
    # TODO
    pass


class RGBImageTest(unittest.TestCase):
    # TODO
    pass