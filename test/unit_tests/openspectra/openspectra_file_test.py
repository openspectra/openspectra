#  Developed by Joseph M. Conti and Joseph W. Boardman on 2/2/19 6:12 PM.
#  Last modified 2/2/19 6:12 PM
#  Copyright (c) 2019. All rights reserved.
import math
import os
import unittest
from typing import List, Tuple

import numpy as np

from openspectra.openspectra_file import OpenSpectraHeader, OpenSpectraFileFactory, PercentageStretch, \
    LinearImageStretch, \
    ValueStretch, OpenSpectraHeaderError, MutableOpenSpectraHeader


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
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            self.assertEqual(os_header.byte_order(), 0)
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
                "\n  1995 AVIRIS \"Effort\" Corrected ATREM [Thu Apr 25 00:52:03 1996] [Thu Mar\n  2912:49:46 2012]")
            self.assertEqual(os_header.data_ignore_value(), -9999)
            self.assertEqual(os_header.coordinate_system_string(),
                "PROJCS[\"UTM_Zone_12N\",GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\",SPHEROID[\"WGS_1984\",6378137.0,298.257223563]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"False_Easting\",500000.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",-111.0],PARAMETER[\"Scale_Factor\",0.9996],PARAMETER[\"Latitude_Of_Origin\",0.0],UNIT[\"Meter\",1.0]]")
            default_stretch:LinearImageStretch = os_header.default_stretch()
            self.assertTrue(isinstance(default_stretch, ValueStretch))
            self.assertEqual(default_stretch.low(), 0.0)
            self.assertEqual(default_stretch.high(), 1000.0)

            bbl = os_header.bad_band_list()
            self.assertEqual(len(bbl), band_count)
            self.assertEqual(bbl, expected_bbl)

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
            self.assertIsNone(map_info.rotation_deg())

        # for message in log.output:
        #     self.assertFalse(message.startswith("WARNING"))

    def test_file_parse_sample_two(self):
        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/sample_header_2.hdr"
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            # print(os_header.dump())
            self.assertEqual(os_header.samples(), 400)
            self.assertEqual(os_header.lines(), 350)
            self.assertEqual(os_header.band_count(), 50)
            self.assertEqual(os_header.data_type(), np.int16)

            # TODO the rest?  just what is different?

            default_stretch = os_header.default_stretch()
            self.assertTrue(isinstance(default_stretch, PercentageStretch))
            self.assertEqual(default_stretch.percentage(), 5.0)

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
            self.assertEqual(map_info.rotation(), math.radians(30.0))
            self.assertEqual(map_info.rotation_deg(), 30.0)

        # for message in log.output:
        #     self.assertFalse(message.startswith("WARNING"), "Expected failure, header support is incomplete")

    def test_file_parse_sample_three(self):
        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/ang20160928t135411_rfl_v1nx_nonortho.hdr"
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            self.assertEqual(os_header.samples(), 598)

            # TODO, much more to test

        for message in log.output:
            self.assertFalse(message.startswith("WARNING"))

    def test_map_info_string_no_rotation(self):
        test_file = "test/unit_tests/resources/sample_header_1.hdr"
        header = OpenSpectraHeader(test_file)
        header.load()
        expected_str = "{UTM, 1.000, 1.000, 50000.000, 4000000.000, 2.0000000000e+001, 2.0000000000e+001, 12, North, WGS-84, units=Meters}"
        self.assertEqual(expected_str, str(header.map_info()))

    def test_map_info_string(self):
        test_file = "test/unit_tests/resources/sample_header_2.hdr"
        header = OpenSpectraHeader(test_file)
        header.load()
        expected_str = "{UTM, 1.000, 1.000, 50000.000, 4000000.000, 2.0000000000e+001, 2.0000000000e+001, 12, North, WGS-84, units=Meters, rotation=30.00000000}"
        self.assertEqual(expected_str, str(header.map_info()))


class MapInfoTest(unittest.TestCase):

    def setUp(self) -> None:
        test_file1 = "test/unit_tests/resources/sample_header_1.hdr"
        self.__header1 = OpenSpectraHeader(test_file1)
        self.__header1.load()

        test_file2 = "test/unit_tests/resources/sample_header_2.hdr"
        self.__header2 = OpenSpectraHeader(test_file2)
        self.__header2.load()

    def test_calculate_single_pixels(self):
        # TODO test needs work doesn't actaully verify the calculation is correct!
        coords_int = self.__header1.map_info().calculate_coordinates(5, 5)
        # print("calculated coords: {}, {}".format(coords_int[0], coords_int[1]))

        coords_float = self.__header1.map_info().calculate_coordinates(5.0, 5.0)
        # print("calculated coords: {}, {}".format(coords_float[0], coords_float[1]))
        self.assertEqual(coords_int[0], coords_float[0])
        self.assertEqual(coords_int[1], coords_float[1])

        coords_int = self.__header2.map_info().calculate_coordinates(5, 5)
        # print("calculated coords: {}, {}".format(coords_int[0], coords_int[1]))

        coords_float = self.__header2.map_info().calculate_coordinates(5.0, 5.0)
        # print("calculated coords: {}, {}".format(coords_float[0], coords_float[1]))
        self.assertEqual(coords_int[0], coords_float[0])
        self.assertEqual(coords_int[1], coords_float[1])


class OpenSpectraFileTest(unittest.TestCase):

    def test_os_file_slice(self):
        test_file = "test/unit_tests/resources/cup95_eff_fixed"
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

    def test_bands(self):
        """Verify the bands returned."""
        test_file = "test/unit_tests/resources/cup95_eff_fixed"
        os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)
        os_header = os_file.header()

        # TODO single pair returns different shape = (num bands, ) array
        #  from more than 1 pair whid return shape = (num points, num bands)
        band1 = os_file.bands(0, 0)
        print(band1.shape, len(band1.shape))

        # band1_mod = band1.reshape(1, band1.size)
        # print(band1_mod.shape, len(band1_mod.shape), band1_mod)

        self.assertEqual(band1.shape[0], 1)
        self.assertEqual(band1.shape[1], os_header.band_count())

        band2 = os_file.bands(1, 1)
        self.assertEqual(band2.shape[0], 1)
        self.assertEqual(band2.shape[1], os_header.band_count())

        band3 = os_file.bands((0, 1, 2), (0, 1, 2))
        print(band3.shape)
        self.assertEqual(band3.shape[0], 3)
        self.assertEqual(band3.shape[1], os_header.band_count())

        self.assertFalse(np.array_equal(band1, band2))
        # Verify the set of bands returns is oriented as expected
        self.assertTrue(np.array_equal(band3[0, :], band1[0, :]))
        self.assertTrue(np.array_equal(band3[1, :], band2[0, :]))

    def test_offset_mapped_model(self):
        """Verify the byte offset feature works with the mapped model"""
        test_file = "test/unit_tests/resources/cup95_eff_fixed"
        os_file_base = OpenSpectraFileFactory.create_open_spectra_file(test_file, OpenSpectraFileFactory.MAPPED_MODEL)
        self.assertEqual(os_file_base.header().header_offset(), 0)

        test_file = "test/unit_tests/resources/cup95_eff_fixed_offset_1k"
        os_file_offset = OpenSpectraFileFactory.create_open_spectra_file(test_file, OpenSpectraFileFactory.MAPPED_MODEL)
        self.assertEqual(os_file_offset.header().header_offset(), 1024)

        bands_base = os_file_base.bands(10, 10)
        bands_offset = os_file_offset.bands(10, 10)
        self.assertTrue(np.array_equal(bands_base, bands_offset))

        image_base = os_file_base.raw_image(10)
        image_offset = os_file_offset.raw_image(10)
        self.assertTrue(np.array_equal(image_base, image_offset))

    def test_offset_memory_model(self):
        """Verify the byte offset feature works with the memory model"""
        test_file = "test/unit_tests/resources/cup95_eff_fixed"
        os_file_base = OpenSpectraFileFactory.create_open_spectra_file(test_file, OpenSpectraFileFactory.MEMORY_MODEL)
        self.assertEqual(os_file_base.header().header_offset(), 0)

        test_file = "test/unit_tests/resources/cup95_eff_fixed_offset_1k"
        os_file_offset = OpenSpectraFileFactory.create_open_spectra_file(test_file, OpenSpectraFileFactory.MEMORY_MODEL)
        self.assertEqual(os_file_offset.header().header_offset(), 1024)

        bands_base = os_file_base.bands(10, 10)
        bands_offset = os_file_offset.bands(10, 10)
        self.assertTrue(np.array_equal(bands_base, bands_offset))

        image_base = os_file_base.raw_image(10)
        image_offset = os_file_offset.raw_image(10)
        self.assertTrue(np.array_equal(image_base, image_offset))

# TODO validate OpenSpectraFileFactory switches work...


class MutableOpenSpectraHeaderTest(unittest.TestCase):

    def setUp(self) -> None:
        test_file1 = "test/unit_tests/resources/sample_header_1.hdr"
        self.__source_header1 = OpenSpectraHeader(test_file1)
        self.__source_header1.load()

        test_file2 = "test/unit_tests/resources/sample_header_2.hdr"
        self.__source_header2 = OpenSpectraHeader(test_file2)
        self.__source_header2.load()

        # this one has no map_info
        test_file3 = "test/unit_tests/resources/cup95_eff_fixed.hdr"
        self.__source_header3 = OpenSpectraHeader(test_file3)
        self.__source_header3.load()

        test_file4 = "test/unit_tests/resources/ang20160928t135411_rfl_v1nx_nonortho.hdr"
        self.__source_header4 = OpenSpectraHeader(test_file4)
        self.__source_header4.load()

        self.__clean_up_list = list()

    def tearDown(self) -> None:
        for file_name in self.__clean_up_list:
            if os.path.isfile(file_name):
                os.remove(file_name)

    def test_deep_copy(self):
        orig_byte_order = self.__source_header1.byte_order()
        orig_lines = self.__source_header1.lines()
        orig_samples = self.__source_header1.samples()
        orig_interleave = self.__source_header1.interleave()
        orig_band_count = self.__source_header1.band_count()
        orig_band_names = self.__source_header1.band_names()
        orig_wavelengths = self.__source_header1.wavelengths()
        orig_bad_bands = self.__source_header1.bad_band_list()
        orig_map_info = self.__source_header1.map_info()

        mutable_header = MutableOpenSpectraHeader(os_header=self.__source_header1)
        self.assertEqual(orig_byte_order, mutable_header.byte_order())
        self.assertEqual(orig_lines, mutable_header.lines())
        self.assertEqual(orig_samples, mutable_header.samples())
        self.assertEqual(orig_interleave, mutable_header.interleave())
        self.assertEqual(orig_band_count, mutable_header.band_count())
        self.assertListEqual(orig_band_names, mutable_header.band_names())
        self.assertTrue(np.array_equal(orig_wavelengths, mutable_header.wavelengths()))
        self.assertListEqual(orig_bad_bands, mutable_header.bad_band_list())
        self.assertMapInfoEqual(orig_map_info, mutable_header.map_info())

        new_lines = 100
        self.assertNotEqual(orig_lines, new_lines)
        mutable_header.set_lines(new_lines)
        self.assertEqual(new_lines, mutable_header.lines())
        self.assertEqual(orig_lines, self.__source_header1.lines())

        new_samples = 100
        self.assertNotEqual(orig_samples, new_samples)
        mutable_header.set_samples(new_samples)
        self.assertEqual(new_samples, mutable_header.samples())
        self.assertEqual(orig_samples, self.__source_header1.samples())

        new_interleave = OpenSpectraHeader.BSQ_INTERLEAVE
        self.assertNotEqual(orig_interleave, new_interleave)
        mutable_header.set_interleave(new_interleave)
        self.assertEqual(new_interleave, mutable_header.interleave())
        self.assertEqual(orig_interleave, self.__source_header1.interleave())

        self.assertEqual(50, orig_band_count)
        band_slice = slice(5, 32)
        new_band_names = orig_band_names[band_slice]
        new_band_count = len(new_band_names)
        new_wavelengths = orig_wavelengths[band_slice]
        new_bad_bands = orig_bad_bands[band_slice]

        self.assertEqual(27, new_band_count)
        self.assertEqual(new_band_count, len(new_band_names))
        self.assertEqual(new_band_count, len(new_wavelengths))
        self.assertEqual(new_band_count, len(new_bad_bands))

        mutable_header.set_bands(new_band_count, new_band_names, new_wavelengths, new_bad_bands)
        self.assertListEqual(new_band_names, mutable_header.band_names())
        self.assertListEqual(orig_band_names, self.__source_header1.band_names())

        self.assertTrue(np.array_equal(new_wavelengths, mutable_header.wavelengths()))
        self.assertTrue(np.array_equal(orig_wavelengths, self.__source_header1.wavelengths()))

        self.assertListEqual(new_bad_bands, mutable_header.bad_band_list())
        self.assertListEqual(orig_bad_bands, self.__source_header1.bad_band_list())

        self.assertMapInfoEqual(orig_map_info, mutable_header.map_info())

    def test_no_map_info(self):
        self.assertIsNone(self.__source_header3.map_info())
        mutable_header = MutableOpenSpectraHeader(os_header=self.__source_header3)
        self.assertIsNone(mutable_header.map_info())

    def test_map_info(self):
        orig_map_info = self.__source_header2.map_info()
        self.assertEqual(1.0, orig_map_info.x_reference_pixel())
        self.assertEqual(50000.0, orig_map_info.x_zero_coordinate())
        self.assertEqual(1.0, orig_map_info.y_reference_pixel())
        self.assertEqual(4000000.0, orig_map_info.y_zero_coordinate())

        mutable_header = MutableOpenSpectraHeader(os_header=self.__source_header2)
        self.assertMapInfoEqual(orig_map_info, mutable_header.map_info())

        self.assertNotEqual(3.0, orig_map_info.x_reference_pixel())
        self.assertNotEqual(55000.0, orig_map_info.x_zero_coordinate())
        mutable_header.set_x_reference(3.0, 55000.0)
        self.assertMapInfoOtherEqual(orig_map_info, mutable_header.map_info())
        self.assertEqual(3.0, mutable_header.map_info().x_reference_pixel())
        self.assertEqual(55000.0, mutable_header.map_info().x_zero_coordinate())
        self.assertEqual(orig_map_info.y_reference_pixel(), mutable_header.map_info().y_reference_pixel())
        self.assertEqual(orig_map_info.y_zero_coordinate(), mutable_header.map_info().y_zero_coordinate())

        self.assertNotEqual(4.0, orig_map_info.y_reference_pixel())
        self.assertNotEqual(4007000.0, orig_map_info.y_zero_coordinate())
        mutable_header.set_y_reference(4.0, 4007000.0)
        self.assertMapInfoOtherEqual(orig_map_info, mutable_header.map_info())
        self.assertEqual(3.0, mutable_header.map_info().x_reference_pixel())
        self.assertEqual(55000.0, mutable_header.map_info().x_zero_coordinate())
        self.assertEqual(4.0, mutable_header.map_info().y_reference_pixel())
        self.assertEqual(4007000.0, mutable_header.map_info().y_zero_coordinate())

        self.assertEqual(1.0, orig_map_info.x_reference_pixel())
        self.assertEqual(50000.0, orig_map_info.x_zero_coordinate())
        self.assertEqual(1.0, orig_map_info.y_reference_pixel())
        self.assertEqual(4000000.0, orig_map_info.y_zero_coordinate())

    def test_load(self):
        # Just making sure MutableOpenSpectraHeader.load() doesn't blow up
        mutable_header = MutableOpenSpectraHeader(os_header=self.__source_header1)
        mutable_header.load()

    def test_save1(self):
        mutable_header = MutableOpenSpectraHeader(os_header=self.__source_header1)
        test_file_name = "test/unit_tests/resources/sample_header_1_copy"
        mutable_header.save(test_file_name)
        header_copy = OpenSpectraHeader(test_file_name + ".hdr")
        header_copy.load()
        self.assertHeadersMatch(self.__source_header1, header_copy)
        self.__clean_up_list.append(test_file_name + ".hdr")

    def test_save2(self):
        mutable_header = MutableOpenSpectraHeader(os_header=self.__source_header4)
        test_file_name = "test/unit_tests/resources/ang20160928t135411_rfl_v1nx_nonortho_copy"
        mutable_header.save(test_file_name)
        header_copy = OpenSpectraHeader(test_file_name + ".hdr")
        header_copy.load()
        self.assertHeadersMatch(self.__source_header4, header_copy)
        self.__clean_up_list.append(test_file_name + ".hdr")

    def assertHeadersMatch(self, first:OpenSpectraHeader, second:OpenSpectraHeader):
        self.assertEqual(first.description(), second.description())
        self.assertEqual(first.samples(), second.samples())
        self.assertEqual(first.lines(), second.lines())
        self.assertEqual(first.band_count(), second.band_count())
        self.assertEqual(first.header_offset(), second.header_offset())
        self.assertEqual(first.file_type(), second.file_type())
        self.assertEqual(first.data_type(), second.data_type())
        self.assertEqual(first.interleave(), second.interleave())
        self.assertEqual(first.sensor_type(), second.sensor_type())
        self.assertEqual(first.byte_order(), second.byte_order())
        self.assertEqual(first.wavelength_units(), second.wavelength_units())
        self.assertEqual(first.reflectance_scale_factor(), second.reflectance_scale_factor())
        self.assertMapInfoEqual(first.map_info(), second.map_info())
        self.assertEqual(first.coordinate_system_string(), second.coordinate_system_string())
        self.assertStretchEqual(first.default_stretch(), second.default_stretch())

        if first.band_names() is None:
            self.assertIsNone(second.band_names())
        else:
            self.assertListEqual(first.band_names(), second.band_names())
        self.assertTrue(np.array_equal(first.wavelengths(), second.wavelengths()))

        if first.bad_band_list() is None:
            self.assertIsNone(second.bad_band_list())
        else:
            self.assertListEqual(first.bad_band_list(), second.bad_band_list())

        self.assertUnsupportedPropsMatch(first, second)

    def assertUnsupportedPropsMatch(self, first:OpenSpectraHeader, second:OpenSpectraHeader):
        self.assertEqual(len(first.unsupported_props()), len(second.unsupported_props()))
        self.assertSetEqual(set(first.unsupported_props().keys()), set(second.unsupported_props().keys()))
        for key, value in first.unsupported_props().items():
            if isinstance(value, list):
                if len(value) == first.band_count():
                    self.assertEqual(second.band_count(), len(value))
                else:
                    self.assertListEqual(list(first.unsupported_props().values()),
                        list(second.unsupported_props().values()))
            else:
                self.assertEqual(first.unsupported_props().get(key), value)

    def assertStretchEqual(self, first:LinearImageStretch, second:LinearImageStretch):
        if first is None:
            self.assertIsNone(second)
        elif isinstance(first, PercentageStretch) and isinstance(second, PercentageStretch):
            self.assertEqual(first.percentage(), second.percentage())
            with self.assertRaises(NotImplementedError):
                first.low()
            with self.assertRaises(NotImplementedError):
                first.high()
        elif isinstance(first, ValueStretch) and isinstance(second, ValueStretch):
            self.assertEqual(first.low(), second.low())
            self.assertEqual(first.high(), second.high())
            with self.assertRaises(NotImplementedError):
                first.percentage()
        else:
            self.fail("assertStretchEqual expects both values to have the same type")

    def assertMapInfoEqual(self, first:OpenSpectraHeader.MapInfo, second:OpenSpectraHeader.MapInfo):
        if first is None:
            self.assertIsNone(second)
        else:
            self.assertEqual(first.projection_name(), second.projection_name())
            self.assertEqual(first.x_reference_pixel(), second.x_reference_pixel())
            self.assertEqual(first.y_reference_pixel(), second.y_reference_pixel())
            self.assertEqual(first.x_zero_coordinate(), second.x_zero_coordinate())
            self.assertEqual(first.y_zero_coordinate(), second.y_zero_coordinate())
            self.assertEqual(first.x_pixel_size(), second.x_pixel_size())
            self.assertEqual(first.projection_zone(), second.projection_zone())
            self.assertEqual(first.projection_area(), second.projection_area())
            self.assertEqual(first.datum(), second.datum())
            self.assertEqual(first.units(), second.units())
            self.assertEqual(first.rotation(), second.rotation())
            self.assertEqual(first.rotation_deg(), second.rotation_deg())

    def assertMapInfoOtherEqual(self, first:OpenSpectraHeader.MapInfo, second:OpenSpectraHeader.MapInfo):
        if first is None:
            self.assertIsNone(second)
        else:
            self.assertEqual(first.projection_name(), second.projection_name())
            self.assertEqual(first.y_pixel_size(), second.y_pixel_size())
            self.assertEqual(first.projection_zone(), second.projection_zone())
            self.assertEqual(first.projection_area(), second.projection_area())
            self.assertEqual(first.datum(), second.datum())
            self.assertEqual(first.units(), second.units())
            self.assertEqual(first.rotation(), second.rotation())
            self.assertEqual(first.rotation_deg(), second.rotation_deg())


class ImageStretchTest(unittest.TestCase):

    def test_percentage(self):
        stretch = LinearImageStretch.create_default_stretch("5.0% linear")
        self.assertTrue(isinstance(stretch, PercentageStretch))
        self.assertEqual(stretch.percentage(), 5.0)

        with self.assertRaises(NotImplementedError):
            stretch.low()

        with self.assertRaises(NotImplementedError):
            stretch.high()

    def test_value(self):
        stretch = LinearImageStretch.create_default_stretch("0.000000 1000.000000 linear")
        self.assertTrue(isinstance(stretch, ValueStretch))
        self.assertEqual(stretch.low(), 0.0)
        self.assertEqual(stretch.high(), 1000.0)

        with self.assertRaises(NotImplementedError):
            stretch.percentage()

    def test_fail(self):
        with self.assertRaises(OpenSpectraHeaderError):
            LinearImageStretch.create_default_stretch("127.0 10.0 gaussian")

    def test_base_class(self):
        with self.assertRaises(TypeError):
            test = LinearImageStretch()