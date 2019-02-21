#  Developed by Joseph M. Conti and Joseph W. Boardman on 2/10/19 6:45 PM.
#  Last modified 2/10/19 6:41 PM
#  Copyright (c) 2019. All rights reserved.
import unittest

import numpy as np
from numpy import ma


class NumpyTest(unittest.TestCase):
    """This is not really a unit test, really just demonstrats how
    some numpy features work"""

    def test1(self):
        # demonstrates that slices produces views
        cube = np.arange(27)
        # print(cube)
        cube = cube.reshape(3, 3, 3)
        # print("cube: ", cube)
        self.assertEqual(cube[1, 1, 1], 13)

        # math on an array produces a new array
        cube2 = cube * 10
        self.assertEqual(cube2[1, 1, 1], 130)
        # print("cube2: ", cube2)

        slice1 = cube[:, 1, :]
        # print("slice1: ", slice1)
        # print("slice1.shape: ", slice1.shape)
        self.assertEqual(slice1.shape, (3, 3))
        self.assertEqual(slice1[1, 1], 13)

        # update the cude and the slice should too
        cube[1, 1, 1] = 100
        # print("cube: ", cube)
        # print("slice1: ", slice1)

        self.assertEqual(cube[1, 1, 1], 100)
        # slice is view so it see the update
        self.assertEqual(slice1[1, 1], 100)

        # slice1 not affected
        # print("cube2: ", cube2)
        self.assertEqual(cube2[1, 1, 1], 130)

    def test2(self):
        # slicing with arrays as index creates copy
        cube = np.arange(27)
        # print(cube)
        cube = cube.reshape(3, 3, 3)
        self.assertEqual(cube[1, 1, 1], 13)
        # print("cube: ", cube)

        index = np.array([1])
        slice1 = cube[:, index, :]
        # Note shape is different than for plain int index
        self.assertEqual(slice1.shape, (3, 1, 3))
        self.assertEqual(slice1[1, 0, 1], 13)
        # print("slice1: ", slice1)
        # print("slice1.shape: ", slice1.shape)

        cube[1, 1, 1] = 100
        self.assertEqual(cube[1, 1, 1], 100)
        self.assertEqual(slice1[1, 0, 1], 13)
        # print("cube: ", cube)
        # print("slice1: ", slice1)


    def test3(self):
        # slicing with tuples as index creates copy
        cube = np.arange(27)
        # print(cube)
        cube = cube.reshape(3, 3, 3)
        self.assertEqual(cube[1, 1, 1], 13)
        # print("cube: ", cube)

        index = (0, 1)
        slice1 = cube[:, index, :]
        # print("slice1: ", slice1)
        # print("slice1.shape: ", slice1.shape)
        self.assertEqual(slice1.shape, (3, 2, 3))
        self.assertEqual(slice1[1, 1, 1], 13)

        cube[1, 1, 1] = 100
        # print("cube: ", cube)
        # print("slice1: ", slice1)
        self.assertEqual(cube[1, 1, 1], 100)
        self.assertEqual(slice1[1, 1, 1], 13)

    def test4(self):
        # slicing with lists as index creates copy
        cube = np.arange(27)
        # print(cube)
        cube = cube.reshape(3, 3, 3)
        self.assertEqual(cube[1, 1, 1], 13)
        # print("cube: ", cube)

        index = [0, 1]
        slice1 = cube[:, index, :]
        # print("slice1: ", slice1)
        # print("slice1.shape: ", slice1.shape)
        self.assertEqual(slice1.shape, (3, 2, 3))
        self.assertEqual(slice1[1, 1, 1], 13)

        cube[1, 1, 1] = 100
        # print("cube: ", cube)
        # print("slice1: ", slice1)
        self.assertEqual(cube[1, 1, 1], 100)
        self.assertEqual(slice1[1, 1, 1], 13)

    def test5(self):
        # attempting re-combine slices results in a copy
        # numpy arrays need to be contiguous in memory so must be copied
        cube = np.arange(27)
        # print(cube)
        cube = cube.reshape(3, 3, 3)
        self.assertEqual(cube[1, 1, 1], 13)
        # print("cube: ", cube)

        slice1 = cube[:, 1, :]
        # print("slice1: ", slice1)
        self.assertEqual(slice1[1, 1], 13)

        slice2 = cube[:, 2, :]
        # print("slice2: ", slice2)
        self.assertEqual(slice2[1, 1], 16)

        slices = np.array([slice1, slice2])
        # print("slices: ", slices)
        # print("slices[0]: ", slices[0])
        # print("slices[1]: ", slices[1])

        cube[1, 1, 1] = 100
        cube[1, 2, 1] = 200
        # print("cube: ", cube)
        # print("slice1: ", slice1)
        # print("slice2: ", slice2)
        self.assertEqual(slice1[1, 1], 100)
        self.assertEqual(slice2[1, 1], 200)

        # print("slices[0]: ", slices[0])
        # print("slices[1]: ", slices[1])
        self.assertEqual(slices[0][1, 1], 13)
        self.assertEqual(slices[1][1, 1], 16)

    def test6(self):
        print("test5...")
        red = np.array([1, 1, 1])
        green = np.array([2, 2, 2])
        blue = np.array([3, 3, 3])
        # view = np.array([red.view(), green.view(), blue.view()])
        combined = np.array([red, green, blue])
        # print(combined)

        blue += 1
        # print(blue)
        self.assertTrue(np.array_equal(blue, np.array([4, 4, 4])))
        self.assertTrue(np.array_equal(combined[2], np.array([3, 3, 3])))
        # print(combined)

    def test7(self):
        # print("test3")
        scale: float = 1 / 1.333
        data = np.arange(999, 1010, dtype=np.int16)
        # print(data)
        data = data * scale
        # print(data)
        data = np.floor(data).astype(np.int16)
        self.assertEqual(data[0], 749)
        # print(data)

    # def test8(self):
    #     img = np.arange(9)
    #     print(img)
    #
    #     img.resize(3, 3)
    #     # print(img)
    #     self.assertTrue(np.array_equal(img,
    #         np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]])))
    #     # print(img[(0, 1)])
    #
    #     # None of these work
    #     # index = np.array([[0, 0], [1, 1], [2, 2]])
    #     # index = np.array((0, 0))
    #     # index = [(0, 0), (1, 1)]
    #     # index = np.array([(0, 0), (1, 1)])
    #     # index = list([(0, 0), (1, 1)])
    #     # index = (0, 1), (1, 1), (2, 2)
    #
    #     # this is list of x values, list of y values so 1st pair is 0,0
    #     # index = (0, 1, 2), (0, 2, 1) # works
    #     # index = [(0, 1, 2), (0, 2, 1)] # works
    #     # index = [[0, 1, 2], [0, 2, 1]] # works
    #     # index = np.array([(0, 1, 2), (0, 2, 1)]) # nope
    #     # index = [np.array([0, 1, 2]), np.array([0, 2, 1])] # works
    #
    #     x = ma.array([0, 1, 2])
    #     y = ma.array([0, 2, 1])
    #     x[1] = ma.masked
    #     y[1] = ma.masked
    #
    #     x1 = x[~x.mask]
    #     y1 = y[~y.mask]
    #     # index = [x1, y1]
    #
    #     # print("index: ", index)
    #     print(img[x1, y1])
