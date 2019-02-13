#  Developed by Joseph M. Conti and Joseph W. Boardman on 2/2/19 6:12 PM.
#  Last modified 2/2/19 6:12 PM
#  Copyright (c) 2019. All rights reserved.
import unittest

import numpy as np

from openspectra.openspectra_file import OpenSpectraHeader, OpenSpectraFileFactory


class OpenSpectraHeaderTest(unittest.TestCase):

    def test_file_parse_sample_one(self):
        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/cup95_eff_fixed.hdr"
            # To run in IDE use this path
            # test_file = "../resources/cup95_eff_fixed.hdr"
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            self.assertEqual(os_header.samples(), 400)

            # TODO, much more to test

        for message in log.output:
            self.assertFalse(message.startswith("WARNING"))

    def test_file_parse_sample_two(self):
        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/cup95_eff_fixed_mod.hdr"
            # To run in IDE use this path
            # test_file = "../resources/cup95_eff_fixed_mod.hdr"
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            # print(os_header.dump())
            self.assertEqual(os_header.samples(), 400)

            # TODO, much more to test

        for message in log.output:
            self.assertFalse(message.startswith("WARNING"), "Expected failure, header support is incomplete")

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


