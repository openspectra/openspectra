#  Developed by Joseph M. Conti and Joseph W. Boardman on 4/30/19, 10:38 PM.
#  Last modified 4/30/19, 10:38 PM
#  Copyright (c) 2019. All rights reserved.
import itertools
import unittest

import numpy as np

from openspectra.openspecrtra_tools import RegionOfInterest
from openspectra.openspectra_file import OpenSpectraHeader


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