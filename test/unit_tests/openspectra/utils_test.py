import os
import unittest
from pathlib import Path

from openspectra.utils import OpenSpectraProperties


class OpenSpectraPropertiesTestCase(unittest.TestCase):

    def __check_defaults(self):
        float_bins = OpenSpectraProperties.get_property("FloatBins")
        self.assertIsNotNone(float_bins)
        self.assertTrue(isinstance(float_bins, int))
        self.assertTrue(float_bins > 0)

        threading_enabled = OpenSpectraProperties.get_property("ThreadingEnabled")
        self.assertIsNotNone(threading_enabled)
        self.assertTrue(isinstance(threading_enabled, bool))

        self.assertEqual(256, OpenSpectraProperties.get_property(None, 256))
        self.assertEqual("test", OpenSpectraProperties.get_property(None, "test"))
        self.assertEqual(256.54, OpenSpectraProperties.get_property(None, 256.54))
        self.assertEqual(True, OpenSpectraProperties.get_property(None, True))

    def test_default_properties_load(self):
        self.__check_defaults()

    def test_additional_properties_load(self):
        self.__check_defaults()

        path:str = os.path.abspath(os.path.dirname(__file__))
        file:str = os.path.join(path, "../resources/test.properties")
        self.assertIsNotNone(file)
        self.assertTrue(len(file) > 0)

        prop_file:Path = Path(file)
        self.assertTrue(prop_file.exists() and prop_file.is_file())

        OpenSpectraProperties.add_properties(file)
        self.__check_defaults()

        self.assertEqual(True, OpenSpectraProperties.get_property("TestBool", False))
        self.assertEqual(23.341, OpenSpectraProperties.get_property("TestFloat"), 5.5)
        self.assertEqual(1234, OpenSpectraProperties.get_property("TestInt"), 1)
        self.assertEqual("A test string", OpenSpectraProperties.get_property("TestStr"), "another string")