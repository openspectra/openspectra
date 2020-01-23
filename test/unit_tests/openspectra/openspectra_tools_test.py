#  Developed by Joseph M. Conti and Joseph W. Boardman on 4/30/19, 10:38 PM.
#  Last modified 4/30/19, 10:38 PM
#  Copyright (c) 2019. All rights reserved.
import io
import itertools
import os
import unittest
from typing import List

import numpy as np

from openspectra.image import BandDescriptor
from openspectra.openspectra_tools import RegionOfInterest, OpenSpectraBandTools, OpenSpectraRegionTools, CubeParams, \
    SubCubeTools
from openspectra.openspectra_file import OpenSpectraHeader, OpenSpectraFileFactory


class RegionOfInterestTest(unittest.TestCase):

    def setUp(self) -> None:
        # simulate creating the bounding rectangle that was selected
        x1 = 347
        x2 = 349
        y1 = 205
        y2 = 207
        x_range = np.arange(x1, x2 + 1)
        y_range = np.arange(y1, y2 + 1)
        self.__points = np.array(list(itertools.product(x_range, y_range)))

    def test_iterate_no_map(self):
        point_checked = False
        roi = RegionOfInterest(self.__points, 1.0, 1.0, 1000, 1000,
            BandDescriptor("file_name", "band_label", "wavelength_label"), "test")
        for r in roi:
            # print("x: {0}, y: {1}, x_coord: {2}, y_coord: {3}".format(
            #     r.x_point(), r.y_point(), r.x_coordinate(), r.y_coordinate()))
            if r.x_point() == 348 and r.y_point() == 206:
                self.assertIsNone(r.x_coordinate())
                self.assertIsNone(r.y_coordinate())
                point_checked = True

        self.assertTrue(point_checked)

    def test_iterate_map(self):
        point_checked = False
        map_info = OpenSpectraHeader.MapInfo(["UTM", "1.000", "1.000",
                    "50000.000", "4000000.000", "2.0000000000e+001", "2.0000000000e+001",
                    "4", "North", "WGS-84", "units=Meters"])

        roi = RegionOfInterest(self.__points, 1.0, 1.0, 1000, 1000,
            BandDescriptor("file_name", "band_label", "wavelength_label"), "test", map_info)
        for r in roi:
            # print("x: {0}, y: {1}, x_coord: {2}, y_coord: {3}".format(
            #     r.x_point(), r.y_point(), r.x_coordinate(), r.y_coordinate()))
            if r.x_point() == 348 and r.y_point() == 206:
                self.assertEqual(r.x_coordinate(), 56960.0)
                self.assertEqual(r.y_coordinate(), 3995880.0)
                point_checked = True

        self.assertTrue(point_checked)

    def test_iterate_with_rotation(self):
        point_checked = False
        map_info = OpenSpectraHeader.MapInfo(["UTM", "1.000", "1.000",
                    "50000.000", "4000000.000", "2.0000000000e+001", "2.0000000000e+001",
                    "4", "North", "WGS-84", "units=Meters", "rotation=30.00000000"])

        roi = RegionOfInterest(self.__points, 1.0, 1.0, 1000, 1000,
            BandDescriptor("file_name", "band_label", "wavelength_label"), "test", map_info)
        for r in roi:
            # print("x: {0}, y: {1}, x_coord: {2}, y_coord: {3}".format(
            #     r.x_point(), r.y_point(), r.x_coordinate(), r.y_coordinate()))
            if r.x_point() == 348 and r.y_point() == 206:
                self.assertEqual(r.x_coordinate(), 58087.53681033969)
                self.assertEqual(r.y_coordinate(), 3999911.9753364082)
                point_checked = True

        self.assertTrue(point_checked)


class OpenSpectraRegionToolsTest(unittest.TestCase):

    def setUp(self) -> None:
        # simulate creating the bounding rectangle that was selected
        x1 = 347
        x2 = 349
        y1 = 205
        y2 = 207
        x_range = np.arange(x1, x2 + 1)
        y_range = np.arange(y1, y2 + 1)
        self.__points = np.array(list(itertools.product(x_range, y_range)))

    def test_rotation(self):
        map_info_list = ["UTM", "1.000", "1.000",
            "50000.000", "4000000.000", "2.0000000000e+001", "2.0000000000e+001",
            "4", "North", "WGS-84", "units=Meters", "rotation=30.00000000"]
        map_info = OpenSpectraHeader.MapInfo(map_info_list)

        test_file = "test/unit_tests/resources/cup95_eff_fixed"
        os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)
        os_header = os_file.header()
        band_tools = OpenSpectraBandTools(os_file)

        roi = RegionOfInterest(self.__points, 1.0, 1.0, os_header.lines(), os_header.samples(),
            BandDescriptor("file_name", "band_label", "wavelength_label"), "region_name", map_info)

        region_tools = OpenSpectraRegionTools(roi, band_tools)
        output = io.StringIO()
        region_tools.save_region(text_stream=output, include_bands=True)

        lines = output.getvalue().split("\n")
        self.assertEqual(lines[0], "# name:region_name")
        self.assertEqual(lines[1], "# file name:file_name")
        self.assertEqual(lines[2], "# band name:band_label")
        self.assertEqual(lines[3], "# wavelength:wavelength_label")
        self.assertEqual(lines[4], "# image width:400")
        self.assertEqual(lines[5], "# image height:350")
        self.assertEqual(lines[6], "# projection:UTM 4 North WGS-84")
        self.assertEqual(lines[7], "# description:file_name - band_label - wavelength_label")
        self.assertEqual(lines[8], "# data:")
        self.assertEqual(lines[9], "sample,line,x_coordinate,y_coordinate,Band 172-1.990800,Band 173-2.000900,"
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

        self.assertEqual(lines[10],
            '348,206,58060.216302264,3999919.2958444837,305,307,318,323,324,324,322,321,318,316,319,315,314,308,305,302,301,295,292,291,293,294,291,290,290,287,289,285,280,279,281,274,269,272,272,274,270,273,267,266,250,251,241,236,228,221,203,195,170,161')
        self.assertEqual(lines[11],
            '348,207,58070.216302264,3999901.9753364082,313,318,318,325,332,332,334,332,333,334,331,333,328,328,322,317,314,310,308,305,306,298,300,300,298,299,296,291,293,291,291,288,283,286,287,286,281,276,274,274,265,250,246,242,233,228,203,204,172,148')
        self.assertEqual(lines[12],
            '348,208,58080.216302264,3999884.6548283324,310,311,306,321,325,330,325,329,327,329,328,328,320,318,315,312,309,308,303,302,302,300,300,294,294,295,294,289,290,286,286,284,281,279,281,285,276,270,274,273,261,253,248,241,229,218,205,194,182,162')
        self.assertEqual(lines[13],
            '349,206,58077.53681033969,3999929.2958444837,332,336,343,346,352,358,360,358,354,359,357,352,353,348,346,336,334,330,331,326,328,324,320,319,319,320,317,317,315,313,311,310,309,304,305,302,303,296,299,290,278,281,265,254,250,240,229,204,198,163')
        self.assertEqual(lines[14],
            '349,207,58087.53681033969,3999911.9753364082,336,338,342,354,360,364,360,363,362,361,364,359,358,350,350,345,338,336,335,331,330,333,325,324,322,323,323,324,321,321,320,316,317,311,310,311,309,312,305,298,290,289,279,265,259,240,231,225,205,182')
        self.assertEqual(lines[15],
            '349,208,58097.53681033969,3999894.6548283324,327,330,345,348,349,353,355,355,357,355,354,353,350,345,344,336,333,330,329,326,325,325,320,319,318,317,315,316,315,314,311,310,308,303,305,307,302,305,297,290,285,278,264,264,253,242,229,219,198,169')
        self.assertEqual(lines[16],
            '350,206,58094.85731841538,3999939.2958444837,333,339,342,342,353,356,354,352,354,356,353,356,347,344,341,336,331,327,323,320,320,321,316,319,317,314,316,311,313,308,305,306,299,297,297,302,306,303,292,287,278,271,270,257,252,232,221,218,193,172')
        self.assertEqual(lines[17],
            '350,207,58104.85731841538,3999921.9753364082,325,325,331,337,343,351,351,347,349,350,351,350,347,343,337,331,331,326,319,321,317,319,314,313,312,312,312,310,308,305,302,303,299,295,301,299,299,291,287,282,274,265,263,253,244,243,215,207,197,172')
        self.assertEqual(lines[18],
            '350,208,58114.85731841538,3999904.6548283324,306,303,295,312,323,332,328,328,329,333,332,332,331,328,321,319,316,311,307,305,305,305,300,298,297,298,297,294,293,288,289,287,288,282,286,283,280,278,276,269,266,259,250,234,233,229,203,200,177,136')

        output.close()

    def test_save_single_band(self):
        map_info_list = ["UTM", "1.000", "1.000",
            "50000.000", "4000000.000", "2.0000000000e+001", "2.0000000000e+001",
            "4", "North", "WGS-84", "units=Meters"]
        map_info = OpenSpectraHeader.MapInfo(map_info_list)

        test_file = "test/unit_tests/resources/cup95_eff_fixed"
        os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)
        os_header = os_file.header()
        band_tools = OpenSpectraBandTools(os_file)

        roi = RegionOfInterest(self.__points, 1.0, 1.0, os_header.lines(), os_header.samples(),
            BandDescriptor("file_name", "band_label", "wavelength_label"), "region_name", map_info)

        region_tools = OpenSpectraRegionTools(roi, band_tools)
        output = io.StringIO()
        region_tools.save_region(text_stream=output, include_bands=True)

        lines = output.getvalue().split("\n")
        self.assertEqual(lines[0], "# name:region_name")
        self.assertEqual(lines[1], "# file name:file_name")
        self.assertEqual(lines[2], "# band name:band_label")
        self.assertEqual(lines[3], "# wavelength:wavelength_label")
        self.assertEqual(lines[4], "# image width:400")
        self.assertEqual(lines[5], "# image height:350")
        self.assertEqual(lines[6], "# projection:UTM 4 North WGS-84")
        self.assertEqual(lines[7], "# description:file_name - band_label - wavelength_label")
        self.assertEqual(lines[8], "# data:")
        self.assertEqual(lines[9], "sample,line,x_coordinate,y_coordinate,Band 172-1.990800,Band 173-2.000900,"
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

        x_expected = 348
        y_expected = 206
        x_coord_expected = 56940.0
        y_coord_expected = 3995900.0
        for index in range(10, len(lines) - 1):
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

            if y_expected == 208:
                y_expected = 206
                x_expected += 1
            else:
                y_expected += 1

            if y_coord_expected == 3995860.0:
                y_coord_expected = 3995900.0
                x_coord_expected += 20.0
            else:
                y_coord_expected -= 20.0

        output.close()

    # TODO finish
    def test_save_rgb(self):
        pass


class OpenSpectraBandToolsTest(unittest.TestCase):

    def setUp(self) -> None:
        test_file = "test/unit_tests/resources/cup95_eff_fixed_offset_1k"
        self.__test_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)
        self.__band_tools = OpenSpectraBandTools(self.__test_file)

    def test_bad_bands(self):
        """Test that the bad bands filter gets applied correctly"""
        bands = self.__band_tools.bands(10, 10)
        band_data = bands.bands()

        self.assertTrue(np.ma.isMaskedArray(band_data))
        self.assertTrue(np.array_equal(band_data.mask, np.array([[
            False, False, False, False, False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, False, False, False, False, False, False,
            False, False, True, True, True, True, True, False, False, False, False, False,
            False, False]])))

        raw_bands = self.__test_file.bands(10, 10)

        for index in range(0, band_data.shape[1]):
            if index in (38, 39, 40, 41, 42):
                self.assertTrue(band_data[0, index] is np.ma.masked)
            else:
                self.assertTrue(band_data[0, index] is not np.ma.masked)
                self.assertEqual(band_data[0, index], raw_bands[0, index])

    def test_ignore_value(self):
        """Test that both bad bands and ignore value get applied properly"""
        bands = self.__band_tools.bands(181, 326)
        band_data = bands.bands()

        self.assertTrue(np.ma.isMaskedArray(band_data))
        self.assertTrue(np.array_equal(band_data.mask, np.array([[
            False, False, False, False, False, False, False, False, False, True, False, False,
            False, False, False, False, False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, False, False, False, False, False, False,
            False, False, True, True, True, True, True, False, False, False, False, False,
            False, False]])))

        raw_bands = self.__test_file.bands(181, 326)
        for index in range(0, band_data.shape[1]):
            if index in (9, 38, 39, 40, 41, 42):
                self.assertTrue(band_data[0, index] is np.ma.masked)
            else:
                self.assertTrue(band_data[0, index] is not np.ma.masked)
                self.assertEqual(band_data[0, index], raw_bands[0, index])


class SubCubeToolsTest(unittest.TestCase):

    def setUp(self) -> None:
        self.__test_file = "test/unit_tests/resources/cup95_eff_fixed"
        self.__source_os_file = OpenSpectraFileFactory.create_open_spectra_file(self.__test_file)
        self.__clean_up_list:List[str] = list()

    def tearDown(self) -> None:
        for file_name in self.__clean_up_list:
            if os.path.isfile(file_name):
                os.remove(file_name)
            if os.path.isfile(file_name + ".hdr"):
                os.remove(file_name + ".hdr")

    def testSubCubeData(self):
        source_header = self.__source_os_file.header()
        sub_cube_params = CubeParams(source_header.interleave(), (0, 200), (0, 200), (0, 10))
        sub_cube_tool = SubCubeTools(self.__source_os_file, sub_cube_params)
        sub_cube_tool.create_sub_cube()

        sub_cube_file = self.__test_file + "_sub_test"
        self.__clean_up_list.append(sub_cube_file)
        sub_cube_tool.save(sub_cube_file)

        os_sub_cube = OpenSpectraFileFactory.create_open_spectra_file(sub_cube_file)
        sc_band = os_sub_cube.bands(10, 10)
        self.assertEqual(10, sc_band.size)
        self.assertEqual((1, 10), sc_band.shape)

        source_band = self.__source_os_file.bands(10, 10)
        self.assertTrue(np.array_equal(source_band[:, 0:10], sc_band))

        sc_raw_image = os_sub_cube.raw_image(5)
        self.assertEqual((200, 200), sc_raw_image.shape)

        source_raw_image = self.__source_os_file.raw_image(5)
        self.assertTrue(np.array_equal(source_raw_image[0:200, 0:200], sc_raw_image))

        lines = (99, 212)
        samples = (148, 251)
        bands = (7, 13)
        sub_cube_params = CubeParams(source_header.interleave(), lines, samples, bands)
        sub_cube_tool = SubCubeTools(self.__source_os_file, sub_cube_params)
        sub_cube_tool.create_sub_cube()
        sub_cube_tool.save(sub_cube_file)

        os_sub_cube = OpenSpectraFileFactory.create_open_spectra_file(sub_cube_file)
        sc_band = os_sub_cube.bands(10, 10)
        source_band = self.__source_os_file.bands(99 + 10, 148 + 10)
        self.assertTrue(np.array_equal(source_band[:, 7:13], sc_band))

    def testInterleaveConversion(self):
        self.assertEqual(OpenSpectraHeader.BIL_INTERLEAVE, self.__source_os_file.header().interleave())

        # First create a smaller copy of the original bil sample file so the tests will run a bit faster
        lines = (0, 50)
        samples = (0, 50)
        bands = (0, 10)

        bil_sc_tools = SubCubeTools(self.__source_os_file)
        bil_sc_tools.set_lines(lines)
        bil_sc_tools.set_samples(samples)
        bil_sc_tools.set_bands(bands)
        bil_sc_tools.create_sub_cube()

        bil_file_name = self.__test_file + "_bil_test"
        self.__clean_up_list.append(bil_file_name)
        bil_sc_tools.save(bil_file_name)
        bil_file = OpenSpectraFileFactory.create_open_spectra_file(bil_file_name)
        self.assertEqual(OpenSpectraHeader.BIL_INTERLEAVE, bil_file.header().interleave())

        # BIL to BIP
        bil_sc_tools.set_interleave(OpenSpectraHeader.BIP_INTERLEAVE)
        bil_sc_tools.create_sub_cube()
        bil_bip_file_name = self.__test_file + "_bil_bip_test"
        self.__clean_up_list.append(bil_bip_file_name)
        bil_sc_tools.save(bil_bip_file_name)

        bip_file = OpenSpectraFileFactory.create_open_spectra_file(bil_bip_file_name)
        self.assertEqual(bip_file.header().interleave(), OpenSpectraHeader.BIP_INTERLEAVE)
        self.assertTrue(np.array_equal(bil_file.bands(35, 21), bip_file.bands(35, 21)))
        self.assertTrue(np.array_equal(bil_file.raw_image(8), bip_file.raw_image(8)))

        # BIL to BSQ
        bil_sc_tools.set_interleave(OpenSpectraHeader.BSQ_INTERLEAVE)
        bil_sc_tools.create_sub_cube()
        bil_bsq_file_name = self.__test_file + "_bil_bsq_test"
        self.__clean_up_list.append(bil_bsq_file_name)
        bil_sc_tools.save(bil_bsq_file_name)

        bsq_file = OpenSpectraFileFactory.create_open_spectra_file(bil_bsq_file_name)
        self.assertEqual(bsq_file.header().interleave(), OpenSpectraHeader.BSQ_INTERLEAVE)
        self.assertTrue(np.array_equal(bil_file.bands(35, 21), bsq_file.bands(35, 21)))
        self.assertTrue(np.array_equal(bil_file.raw_image(8), bsq_file.raw_image(8)))

        bip_sc_tools = SubCubeTools(bip_file)
        bip_sc_tools.set_lines(lines)
        bip_sc_tools.set_samples(samples)
        bip_sc_tools.set_bands(bands)

        # BIP to BSQ
        bip_sc_tools.set_interleave(OpenSpectraHeader.BSQ_INTERLEAVE)
        bip_bsq_file_name = self.__test_file + "_bip_bsq_test"
        self.__clean_up_list.append(bip_bsq_file_name)
        bip_sc_tools.create_sub_cube()
        bip_sc_tools.save(bip_bsq_file_name)

        bip_bsq_file = OpenSpectraFileFactory.create_open_spectra_file(bip_bsq_file_name)
        self.assertEqual(bip_bsq_file.header().interleave(), OpenSpectraHeader.BSQ_INTERLEAVE)
        self.assertTrue(np.array_equal(bil_file.bands(35, 21), bip_bsq_file.bands(35, 21)))
        self.assertTrue(np.array_equal(bil_file.raw_image(8), bip_bsq_file.raw_image(8)))

        # BIP to BIL
        bip_sc_tools.set_interleave(OpenSpectraHeader.BIL_INTERLEAVE)
        bip_bil_file_name = self.__test_file + "_bip_bil_test"
        self.__clean_up_list.append(bip_bil_file_name)
        bip_sc_tools.create_sub_cube()
        bip_sc_tools.save(bip_bil_file_name)

        bip_bil_file = OpenSpectraFileFactory.create_open_spectra_file(bip_bil_file_name)
        self.assertEqual(bip_bil_file.header().interleave(), OpenSpectraHeader.BIL_INTERLEAVE)
        self.assertTrue(np.array_equal(bil_file.bands(35, 21), bip_bil_file.bands(35, 21)))
        self.assertTrue(np.array_equal(bil_file.raw_image(8), bip_bil_file.raw_image(8)))

        bsq_sc_tools = SubCubeTools(bsq_file)
        bsq_sc_tools.set_lines(lines)
        bsq_sc_tools.set_samples(samples)
        bsq_sc_tools.set_bands(bands)

        # BSQ to BIL
        bsq_sc_tools.set_interleave(OpenSpectraHeader.BIL_INTERLEAVE)
        bsq_bil_file_name = self.__test_file + "_bsq_bil_test"
        self.__clean_up_list.append(bsq_bil_file_name)
        bsq_sc_tools.create_sub_cube()
        bsq_sc_tools.save(bsq_bil_file_name)

        bsq_bil_file = OpenSpectraFileFactory.create_open_spectra_file(bsq_bil_file_name)
        self.assertEqual(bsq_bil_file.header().interleave(), OpenSpectraHeader.BIL_INTERLEAVE)
        self.assertTrue(np.array_equal(bil_file.bands(35, 21), bsq_bil_file.bands(35, 21)))
        self.assertTrue(np.array_equal(bil_file.raw_image(8), bsq_bil_file.raw_image(8)))

        # BSQ to BIP
        bsq_sc_tools.set_interleave(OpenSpectraHeader.BIP_INTERLEAVE)
        bsq_bip_file_name = self.__test_file + "_bsq_bip_test"
        self.__clean_up_list.append(bsq_bip_file_name)
        bsq_sc_tools.create_sub_cube()
        bsq_sc_tools.save(bsq_bip_file_name)

        bsq_bip_file = OpenSpectraFileFactory.create_open_spectra_file(bsq_bip_file_name)
        self.assertEqual(bsq_bip_file.header().interleave(), OpenSpectraHeader.BIP_INTERLEAVE)
        self.assertTrue(np.array_equal(bil_file.bands(35, 21), bsq_bip_file.bands(35, 21)))
        self.assertTrue(np.array_equal(bil_file.raw_image(8), bsq_bip_file.raw_image(8)))
