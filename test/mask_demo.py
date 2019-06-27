#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
import itertools
from math import floor

import numpy as np
from numpy import ma


def replace_values_demo():
    """demonstrates how we use masking to filter the high and low values in the
    stretching algorithm used to comvert the raw image data into a displayable
    image"""
    data = np.arange(1.0, 10.0)
    print("data start: ", data)

    low_masked = np.ma.masked_where(data < 3, data, False)
    low_mask = np.ma.getmask(low_masked)
    print("low_masked: ", low_masked)
    print("low_mask: ", low_mask)
    print("data: ", data)

    high_masked = np.ma.masked_where(data > 7, data, False)
    high_mask = np.ma.getmask(high_masked)
    print("high_masked: ", high_masked)
    print("high_mask: ", high_mask)
    print("data: ", data)

    full_mask = low_mask | high_mask
    print("full_mask: ", full_mask)

    data_masked = np.ma.masked_where(full_mask, data)
    print("data_masked: ", data_masked)
    # size gives total number of elements in the array ignoring masking
    print("data_masked size: ", data_masked.size)
    # count() gives number of unmasked elements
    print("data_masked count: ", data_masked.count())

    data_masked = data_masked * 3
    print(data_masked)

    data_masked[low_mask] = 0
    data_masked[high_mask] = 255
    print("data_adj: ", data_masked)


def list_masking_test():
    """Demonstrates how we collect the points for a region of interest"""

    # first simulate creating the bounding rectangle that was selected
    x1 = y1 = 0
    x2 = y2 = 5
    x_range = ma.arange(x1, x2 + 1)
    y_range = ma.arange(y1, y2 + 1)
    points = ma.array(list(itertools.product(x_range, y_range)))
    print("point's shape: {0}\npoints:\n{1}".format(points.shape, points))

    # simulate where we check if the point is in the selected polygon
    # and mask it if not
    for i in range(len(points)):
        # print(points[i])
        pair = points[i]
        if pair[0] == 3 or pair[0] == 4 or pair[1] == 3 or pair[1] == 4:
            points[i] = ma.masked

    print("points: {0}".format(points))
    # print("points.mask: {0}".format(points.mask))
    print("points.count: {0}".format(points.count()))
    print("points.count: {0}".format(floor(points.count() / 2)))

    # now extract the non-masked points and reshape it onto a list of pairs
    plain_points = points[~points.mask].reshape(floor(points.count() / 2), 2)
    print("plain point's shape: {0}\npoints:\n{1}".format(plain_points.shape, plain_points))

    # but they are not considered equal because they have different shapes
    print("Equal? {0}".format(np.array_equal(plain_points, points)))

    # now replace the masked values with -1, this is just to help us
    # check we have the same set of points in both arrays below
    points[points.mask] = -1
    # print("filled points: {0}".format(points))

    is_equal = True
    plain_index = 0
    for pair in points:
        # print("pair: {0}, {1}".format(pair[0], pair[1]))
        if pair[0] != -1:
            # print("unmasked pair: {0}, {1}".format(pair, plain_points[plain_index]))
            is_equal = np.array_equal(pair, plain_points[plain_index])
            plain_index += 1
            if not is_equal:
                print("arrays were not equal")
                break

    if is_equal:
        print("arrays were equal")


def mask_from_list():
    """Take a bad band list and apply it as a mask to a list of band values"""
    bad_band_list = ["0", "1", "1", "0", "1"]
    print(bad_band_list)

    # remember that "1" means the band is good, "0" means it's bad so
    # don't forget to flip the mask
    bad_band_list = [not bool(int(item)) for item in bad_band_list]
    print(bad_band_list)

    band_values = np.ma.array([1, 2, 3, 4, 5])
    print(band_values)
    band_values.mask = bad_band_list
    print(band_values)


def append_mask_from_list():
    """Take a bad band list and apply it as a mask to a list of band values"""
    bad_band_list = ["0", "1", "1", "0", "1"]
    print(bad_band_list)

    # remember that "1" means the band is good, "0" means it's bad so
    # don't forget to flip the mask
    bad_band_list = [not bool(int(item)) for item in bad_band_list]
    print(bad_band_list)

    band_values = np.ma.array([1, 2, 3, 4, 5])
    band_values = ma.masked_equal(band_values, 3)
    print(band_values.mask)

    band_values.mask = band_values.mask | bad_band_list
    print(band_values.mask)
    print(band_values)


def conditional_masking():
    test_array = np.arange(10)
    print(test_array)

    masked_array = ma.masked_equal(test_array, 10)
    # When the mask function doesn't match any values it's set to False
    print(masked_array.mask, masked_array)

    masked_array = ma.masked_equal(test_array, 5)
    print(masked_array.mask, masked_array)


if __name__ == "__main__":
    replace_values_demo()
    list_masking_test()
    mask_from_list()
    append_mask_from_list()
    conditional_masking()