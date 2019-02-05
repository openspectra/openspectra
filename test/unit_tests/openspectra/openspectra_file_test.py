#  Developed by Joseph M. Conti and Joseph W. Boardman on 2/2/19 6:12 PM.
#  Last modified 2/2/19 6:12 PM
#  Copyright (c) 2019. All rights reserved.
import unittest

from openspectra.openspectra_file import OpenSpectraHeader


class OpenSpectraHeaderTest(unittest.TestCase):

    def test_file_parse_sample_one(self):
        with self.assertLogs("openSpectra.OpenSpectraHeader", level='INFO') as log:
            test_file = "test/unit_tests/resources/cup95_eff_fixed.hdr"
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
            os_header = OpenSpectraHeader(test_file)
            self.assertIsNotNone(os_header)
            os_header.load()
            self.assertEqual(os_header.samples(), 598)

            # TODO, much more to test

        for message in log.output:
            self.assertFalse(message.startswith("WARNING"))
