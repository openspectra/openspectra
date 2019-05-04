#  Developed by Joseph M. Conti and Joseph W. Boardman on 4/30/19, 10:38 PM.
#  Last modified 4/30/19, 10:38 PM
#  Copyright (c) 2019. All rights reserved.
import io
import itertools
import unittest

import numpy as np

from openspectra.openspecrtra_tools import RegionOfInterest, OpenSpectraBandTools, OpenSpectraRegionTools
from openspectra.openspectra_file import OpenSpectraHeader, OpenSpectraFileFactory


# TODO finish
class RegionOfInterestTest(unittest.TestCase):

    def setUp(self) -> None:
        # simulate creating the bounding rectangle that was selected
        x1 = y1 = 0
        x2 = y2 = 3
        x_range = np.arange(x1, x2 + 1)
        y_range = np.arange(y1, y2 + 1)
        self.__points = np.array(list(itertools.product(x_range, y_range)))
        self.__map_info = OpenSpectraHeader.MapInfo(["UTM", "1.000", "1.000",
            "50000.000", "4000000.000", "2.0000000000e+001", "2.0000000000e+001",
            "4", "North", "WGS-84", "units=Meters", "rotation=29.00000000"])

    def test_iterate_no_map(self):
        roi = RegionOfInterest(self.__points, 1.0, 1.0, 1000, 1000, "test", "test")
        for r in roi:
            print("x: {0}, y: {1}, x_coord: {2}, y_coord: {3}".format(
                r.x_point(), r.y_point(), r.x_coordinate(), r.y_coordinate()))

    def test_iterate_map(self):
        roi = RegionOfInterest(self.__points, 1.0, 1.0, 1000, 1000, "test", "test", self.__map_info)
        for r in roi:
            print("x: {0}, y: {1}, x_coord: {2}, y_coord: {3}".format(
                r.x_point(), r.y_point(), r.x_coordinate(), r.y_coordinate()))


class OpenSpectraRegionToolsTest(unittest.TestCase):

    def setUp(self) -> None:
        # simulate creating the bounding rectangle that was selected
        x1 = y1 = 0
        x2 = y2 = 3
        x_range = np.arange(x1, x2 + 1)
        y_range = np.arange(y1, y2 + 1)
        self.__points = np.array(list(itertools.product(x_range, y_range)))
        self.__map_info = OpenSpectraHeader.MapInfo(["UTM", "1.000", "1.000",
            "50000.000", "4000000.000", "2.0000000000e+001", "2.0000000000e+001",
            "4", "North", "WGS-84", "units=Meters", "rotation=29.00000000"])

    def test_save(self):
        test_file = "test/unit_tests/resources/cup95_eff_fixed"
        # test_file = "../resources/cup95_eff_fixed"
        os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)
        os_header = os_file.header()
        band_tools = OpenSpectraBandTools(os_file)

        roi = RegionOfInterest(self.__points, 1.0, 1.0, os_header.lines(), os_header.samples(),
            "image_name", "region_name", self.__map_info)

        region_tools = OpenSpectraRegionTools(roi, band_tools)
        output = io.StringIO()
        region_tools.save_region(text_stream=output, include_bands=True)

        lines = output.getvalue().split("\n")
        self.assertEqual(lines[0], "name:region_name")
        self.assertEqual(lines[1], "description:image_name")
        self.assertEqual(lines[2], "image width:400")
        self.assertEqual(lines[3], "image height:350")
        self.assertEqual(lines[4], "projection:UTM 4 North WGS-84")
        self.assertEqual(lines[5], "data:")
        self.assertEqual(lines[6], "sample,line,x_coordinate,y_coordinate,Band 172-1.990800,Band 173-2.000900,"
                                   "Band 174-2.010900,Band 175-2.020900,Band 176-2.030900,Band 177-2.040900,"
                                   "Band 178-2.050900,Band 179-2.060900,Band 180-2.071000,Band 181-2.081000,"
                                   "Band 182-2.091000,Band 183-2.101000,Band 184-2.111000,Band 185-2.121000,"
                                   "Band 186-2.130900,Band 187-2.140900,Band 188-2.150900,Band 189-2.160900,"
                                   "Band 190-2.170900,Band 191-2.180900,Band 192-2.190800,Band 193-2.200800,"
                                   "Band 194-2.210800,Band 195-2.220800,Band 196-2.230700,Band 197-2.240700,"
                                   "Band 198-2.250600,Band 199-2.260600,Band 200-2.270600,Band 201-2.280500,"
                                   "Band 202-2.290400,Band 203-2.300400,Band 204-2.310400,Band 205-2.320300,"
                                   "Band 206-2.330200,Band 207-2.340200,Band 208-2.350100,Band 209-2.360000,"
                                   "Band 210-2.370000,Band 211-2.379900,Band 212-2.389800,Band 213-2.399700,"
                                   "Band 214-2.409600,Band 215-2.419600,Band 216-2.429500,Band 217-2.439400,"
                                   "Band 218-2.449300,Band 219-2.459200,Band 220-2.469100,Band 221-2.479000")

        x_expected = y_expected = 1
        x_coord_expected = 50000.0
        y_coord_expected = 4000000.0
        for index in range(7, len(lines) - 1):
            line = lines[index].split(",")
            x_val = int(line[0])
            self.assertEqual(x_val, x_expected)
            y_val = int(line[1])
            self.assertEqual(y_val, y_expected)
            self.assertEqual(float(line[2]), x_coord_expected)
            self.assertEqual(float(line[3]), y_coord_expected)
            band_values = np.array([int(item) for item in line[4:len(line)]])
            expected_band_values = os_file.bands(y_val, x_val)
            np.array_equal(expected_band_values, band_values)

            if y_expected == 4:
                y_expected = 1
                x_expected += 1
            else:
                y_expected += 1

            if y_coord_expected == 3999940.0:
                y_coord_expected = 4000000.0
                x_coord_expected += 20.0
            else:
                y_coord_expected -= 20.0

        output.close()
