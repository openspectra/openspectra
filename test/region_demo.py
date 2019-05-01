#  Developed by Joseph M. Conti and Joseph W. Boardman on 4/30/19, 7:14 PM.
#  Last modified 4/30/19, 7:14 PM
#  Copyright (c) 2019. All rights reserved.
import itertools

import numpy as np


def zoomed_in_region_test():
    """Simulate scaling a region selected on a zoomed in image and scaling it
    to where it would fall in the same image at 1 to 1"""

    # first simulate creating the bounding rectangle that was selected
    x1 = y1 = 0
    x2 = y2 = 20
    x_range = np.arange(x1, x2 + 1)
    y_range = np.arange(y1, y2 + 1)
    points = np.array(list(itertools.product(x_range, y_range)))
    print("point's shape: {0}\npoints:\n{1}".format(points.shape, points))

    # simulate scaling a set of pixels selected from a zoomed in image
    # to what would be needed for a 1 to 1 image
    zoom_factor = 2.5
    scaled_points = np.floor(points / zoom_factor).astype(np.int16)
    print("scaled points: {0}".format(scaled_points))

    # See docs for other interesting return options for np.unique
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.unique.html
    scaled_points = np.unique(scaled_points, axis=0)
    print("unique scaled points shape: {0}\nscaled points: {1}".format(scaled_points.shape, scaled_points))


def zoomed_out_region_test():
    """Simulate scaling a region selected on a zoomed out image and scaling it
        to where it would fall in the same image at 1 to 1"""

    # first simulate creating the bounding rectangle that was selected
    x1 = y1 = 0
    x2 = y2 = 20
    x_range = np.arange(x1, x2 + 1)
    y_range = np.arange(y1, y2 + 1)
    points = np.array(list(itertools.product(x_range, y_range)))
    print("point's shape: {0}\npoints:\n{1}".format(points.shape, points))

    shape = points.shape
    print("Shape: {0}, dims: {1}".format(shape, len(shape)))

    # simulate scaling a set of pixels selected from a zoomed out image
    # to what would be needed for a 1 to 1 image
    zoom_factor = 0.5
    scaled_points = np.floor(points / zoom_factor).astype(np.int16)

    # Now we an area but there are gaps in the pixels but we
    # do have the outer bounds of the area to be covered
    print("scaled points: {0}".format(scaled_points))


if __name__ == "__main__":
    zoomed_in_region_test()
    zoomed_out_region_test()
