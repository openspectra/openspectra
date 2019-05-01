#  Developed by Joseph M. Conti and Joseph W. Boardman on 2/2/19 6:12 PM.
#  Last modified 2/2/19 6:12 PM
#  Copyright (c) 2019. All rights reserved.
import unittest
from typing import List, Tuple

import numpy as np

from openspectra.openspectra_file import OpenSpectraHeader, OpenSpectraFileFactory


class OpenSpectraHeaderTest(unittest.TestCase):

    def test_file_parse_sample_one(self):
        expected_wavelengths:List[float] = \
            [1.990800, 2.000900, 2.010900, 2.020900, 2.030900, 2.040900, 2.050900,
                2.060900, 2.071000, 2.081000, 2.091000, 2.101000, 2.111000, 2.121000,
                2.130900, 2.140900, 2.150900, 2.160900, 2.170900, 2.180900, 2.190800,
                2.200800, 2.210800, 2.220800, 2.230700, 2.240700, 2.250600, 2.260600,
                2.270600, 2.280500, 2.290400, 2.300400, 2.310400, 2.320300, 2.330200,
                2.340200, 2.350100, 2.360000, 2.370000, 2.379900, 2.389800, 2.399700,
                2.409600, 2.419600, 2.429500, 2.439400, 2.449300, 2.459200, 2.469100,
                2.479000]

        expected_bbl = [False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False,
                        False, False, False, False, False, False, False, False, False,
                        False, False, True, True, True, True, True, False, False, False,
                        False, False, False, False]

        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/sample_header_1.hdr"
            # To run in IDE use this path
            # test_file = "../resources/sample_header_1hdr"
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            self.assertEqual(os_header.samples(), 400)
            self.assertEqual(os_header.lines(), 350)
            band_count:int = os_header.band_count()
            self.assertEqual(band_count, 50)
            self.assertEqual(os_header.data_type(), np.int16)
            self.assertEqual(os_header.interleave(), OpenSpectraHeader.BIL_INTERLEAVE)
            self.assertEqual(os_header.header_offset(), 0)
            self.assertEqual(os_header.wavelength_units(), "Micrometers")
            self.assertEqual(os_header.sensor_type(), "Unknown")
            self.assertEqual(os_header.file_type(), "ENVI Standard")
            self.assertEqual(os_header.description(),
                "1995 AVIRIS \"Effort\" Corrected ATREM [Thu Apr 25 00:52:03 1996] [Thu Mar  2912:49:46 2012]")
            self.assertEqual(os_header.data_ignore_value(), -9999)
            self.assertEqual(os_header.default_stretch()[0], 0.0)
            self.assertEqual(os_header.default_stretch()[1], 1000.0)

            bbl = os_header.bad_band_list()
            self.assertEqual(len(bbl), band_count)
            self.assertEqual(bbl, expected_bbl)

            # TODO
            # byte order = 0
            # coordinate system string = {PROJCS["UTM_Zone_12N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-111.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]}

            band_names:list = os_header.band_names()
            self.assertEqual(len(band_names), band_count)

            band_labels:List[Tuple[str, str]] = os_header.band_labels()

            index = 0
            band_num = 172
            for band_name in band_names:
                expected_name = "Band " + str(band_num)
                self.assertEqual(band_name, expected_name)
                self.assertEqual(os_header.band_name(index), expected_name)
                self.assertEqual(band_labels[index][0], expected_name)
                band_num += 1
                index += 1
            self.assertEqual(band_num, 222)

            wavelengths = os_header.wavelengths()
            self.assertEqual(wavelengths.size, band_count)
            for index in range(0, band_count):
                self.assertEqual(wavelengths[index], expected_wavelengths[index])
                self.assertEqual(band_labels[index][1], "{0:1.6f}".format(expected_wavelengths[index]))

            map_info:OpenSpectraHeader.MapInfo = os_header.map_info()
            self.assertIsNotNone(map_info)
            self.assertEqual(map_info.projection_name(), "UTM")
            self.assertEqual(map_info.x_reference_pixel(), 1.0)
            self.assertEqual(map_info.y_reference_pixel(), 1.0)
            self.assertEqual(map_info.x_zero_coordinate(), 50000.0)
            self.assertEqual(map_info.y_zero_coordinate(), 4000000.0)
            self.assertEqual(map_info.x_pixel_size(), 2.0000000000e+001)
            self.assertEqual(map_info.y_pixel_size(), 2.0000000000e+001)
            self.assertEqual(map_info.projection_zone(), 12)
            self.assertEqual(map_info.projection_area(), "North")
            self.assertEqual(map_info.datum(), "WGS-84")
            self.assertEqual(map_info.units(), "Meters")
            self.assertIsNone(map_info.rotation())

        # for message in log.output:
        #     self.assertFalse(message.startswith("WARNING"))

    def test_file_parse_sample_two(self):
        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/sample_header_2.hdr"
            # To run in IDE use this path
            # test_file = "../resources/sample_header_2.hdr"
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            # print(os_header.dump())
            self.assertEqual(os_header.samples(), 400)
            self.assertEqual(os_header.lines(), 350)
            self.assertEqual(os_header.band_count(), 50)
            self.assertEqual(os_header.data_type(), np.int16)

            # TODO the rest?  just what is different?

            self.assertEqual(os_header.default_stretch(), 5.0)

            map_info:OpenSpectraHeader.MapInfo = os_header.map_info()
            self.assertIsNotNone(map_info)
            self.assertEqual(map_info.projection_name(), "UTM")
            self.assertEqual(map_info.x_reference_pixel(), 1.0)
            self.assertEqual(map_info.y_reference_pixel(), 1.0)
            self.assertEqual(map_info.x_zero_coordinate(), 50000.0)
            self.assertEqual(map_info.y_zero_coordinate(), 4000000.0)
            self.assertEqual(map_info.x_pixel_size(), 2.0000000000e+001)
            self.assertEqual(map_info.y_pixel_size(), 2.0000000000e+001)
            self.assertEqual(map_info.projection_zone(), 12)
            self.assertEqual(map_info.projection_area(), "North")
            self.assertEqual(map_info.datum(), "WGS-84")
            self.assertEqual(map_info.units(), "Meters")
            self.assertEqual(map_info.rotation(), 30.0)

        # for message in log.output:
        #     self.assertFalse(message.startswith("WARNING"), "Expected failure, header support is incomplete")

    def test_file_parse_sample_three(self):
        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/ang20160928t135411_rfl_v1nx_nonortho.hdr"
            # To run in IDE use this path
            # test_file = "../resources/ang20160928t135411_rfl_v1nx_nonortho.hdr"
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            self.assertEqual(os_header.samples(), 598)

            # TODO, much more to test

        for message in log.output:
            self.assertFalse(message.startswith("WARNING"))


class OpenSpectraFileTest(unittest.TestCase):

    def test_os_file_slice(self):
        test_file = "test/unit_tests/resources/cup95_eff_fixed"
        # test_file = "../resources/cup95_eff_fixed"
        os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)

        # confirm how image retrieval works with single index
        # and tuples
        image1 = os_file.raw_image(1)
        image2 = os_file.raw_image(2)
        image3 = os_file.raw_image(3)

        image4 = os_file.raw_image((1, 2, 3))

        self.assertTrue(np.array_equal(image1, image4[:, 0, :]))
        self.assertFalse(np.array_equal(image1, image4[:, 1, :]))
        self.assertFalse(np.array_equal(image1, image4[:, 2, :]))

        self.assertTrue(np.array_equal(image2, image4[:, 1, :]))
        self.assertFalse(np.array_equal(image2, image4[:, 0, :]))
        self.assertFalse(np.array_equal(image2, image4[:, 2, :]))

        self.assertTrue(np.array_equal(image3, image4[:, 2, :]))
        self.assertFalse(np.array_equal(image3, image4[:, 0, :]))
        self.assertFalse(np.array_equal(image3, image4[:, 1, :]))

        # change to order of indexes in the tuple
        image4 = os_file.raw_image((2, 3, 1))
        self.assertTrue(np.array_equal(image2, image4[:, 0, :]))
        self.assertTrue(np.array_equal(image3, image4[:, 1, :]))
        self.assertTrue(np.array_equal(image1, image4[:, 2, :]))

        # slices create copies
        self.assertTrue(image4 is image4)
        self.assertTrue(np.array_equal(image4, image4))
        self.assertFalse(image4[:, 0, :] is image4[:, 0, :])
        self.assertTrue(np.array_equal(image4[:, 0, :], image4[:, 0, :]))

        # self.assertTrue(image4[0:1:1] is image4[0:1:1])

        # calls to os_file.raw_band produce copies of the data
        image5 = os_file.raw_image(1)
        self.assertTrue(np.array_equal(image1, image5))
        self.assertFalse(image1 is image5)

        # inspecting image1 and image6 with the debugger shows
        # both image's data property are the same.
        # But calling image.data returns a copy
        image6 = image1
        self.assertTrue(np.array_equal(image6, image1))
        self.assertTrue(image6 is image1)
        data6 = image6.data
        data1 = image1.data
        self.assertFalse(data6 is data1)

        # math on arrays produce a new array
        image6 = image6 * 10
        self.assertFalse(np.array_equal(image6, image1))
        self.assertFalse(image6 is image1)


