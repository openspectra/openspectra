#  Developed by Joseph M. Conti and Joseph W. Boardman on 4/30/19, 7:14 PM.
#  Last modified 4/30/19, 7:14 PM
#  Copyright (c) 2019. All rights reserved.
import itertools
from math import radians, cos, sin

import numpy as np

from image import BandDescriptor
from openspecrtra_tools import RegionOfInterest


def point_splitting_demo():
    # first simulate creating the bounding rectangle that was selected
    x1 = y1 = 0
    x2 = y2 = 3
    x_range = np.arange(x1, x2 + 1)
    y_range = np.arange(y1, y2 + 1)
    points = np.array(list(itertools.product(x_range, y_range)))
    print("point's shape: {0}, size: {1}\npoints:\n{2}".format(
        points.shape, points.size, points))

    x_points = points[:, 0]
    print("x points[:, 0] shape: {0}\npoints:\n{1}".format(x_points.shape, x_points))
    print("x_points[4]: {0}".format(x_points[4]))
    print("x_points[4]: {0}".format( points[:, 0][4]))


def zoomed_in_region_demo():
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
    print("scaled points shape: {0}\nscaled points: {1}".format(scaled_points.shape, scaled_points))

    # See docs for other interesting return options for np.unique
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.unique.html
    scaled_points = np.unique(scaled_points, axis=0)
    print("unique scaled points shape: {0}\nscaled points: {1}".format(scaled_points.shape, scaled_points))


def zoomed_out_region_demo():
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


def coords_demo():
    x_points = np.array([0, 1, 2, 3])
    x_ref_pixel:float = 1.00
    x_pixel_size:float = 20.00
    x0_coord:float = 50000.000

    print((x_points - (x_ref_pixel - 1)))

    x_coords = (x_points - (x_ref_pixel - 1)) * x_pixel_size + x0_coord
    print(x_coords)

    y_points = np.array([0, 1, 2, 3])
    y_ref_pixel: float = 1.00
    y_pixel_size: float = 20.00
    y0_coord: float = 50000.000

    print(y0_coord - (y_points - (y_ref_pixel - 1)) * y_pixel_size)


def rotation_calc_demo():
    x_y = np.array([1,1])
    # print(x_y.shape)
    x_y.reshape(1, 2)
    # print(x_y.shape)
    # print(x_y)

    a = np.array([1, 2, 1, 2]).reshape(2, 2)
    b = np.array([1, 1, 2, 2]).reshape(2, 2)
    print("a: {0}".format(a))
    print("b: {0}".format(b))
    # print("product: {0}".format(x_y * a))

    print("a dot product: {0}".format(a.dot(x_y)))
    print("b dot product: {0}".format(b.dot(x_y)))

    x1 = y1 = 1
    x2 = y2 = 2
    x_range = np.arange(x1, x2 + 1)
    y_range = np.arange(y1, y2 + 1)
    points = np.array(list(itertools.product(x_range, y_range)))

    # need to transpose the list of points before we can apply the
    # matrix operations so the dimensions are correct.
    points = points.T
    print("shape: {0}, points: {1}".format(points.shape, points))

    # Then we can transpose back to have in the shape we expected
    print("a.dot: {0}".format(a.dot(points).T))
    print("b.dot: {0}".format(b.dot(points).T))

    # x_points = points[:, 0].reshape(1, 4)
    # y_points = points[:, 1]
    # print("points[:, 0]: {0}".format(x_points))
    # print("points[:, 1]: {0}".format(y_points))


def points_shape():

    x1 = y1 = 1
    x2 = y2 = 2
    x_range = np.arange(x1, x2 + 1)
    y_range = np.arange(y1, y2 + 1)
    p_a = np.array(list(itertools.product(x_range, y_range)))
    p_b = np.array(list(itertools.product(x_range, y_range))).T

    print("p_a: {0}".format(p_a))
    print("p_b: {0}".format(p_b))


def trig_demo():

    angle = radians(90.0)
    print(cos(angle))
    print(round(cos(angle), 5))

    print(sin(angle))
    print(round(sin(angle), 5))

    p = np.array([1, 1]).reshape(2, 1)
    print(p)
    a = np.array([1, 2])
    print(a)
    print(p * a)
    print(a.dot(p))


def rescale_demo():
    x1 = y1 = 0
    x2 = y2 = 20
    x_range = np.arange(x1, x2 + 1)
    y_range = np.arange(y1, y2 + 1)
    points = np.array(list(itertools.product(x_range, y_range)))
    print("point's shape: {0}\npoints:\n{1}".format(points.shape, points))

    region = RegionOfInterest(points, 1.0, 1.0, 400, 400,
        BandDescriptor("file_name", "band_name", "wavelength_label"))

    x = region.x_points()
    y = region.y_points()
    # print(x)
    # print(y)

    # scale them individually
    zoom_factor = 2.5
    x_scaled = np.floor(x / zoom_factor).astype(np.int16)
    y_scaled = np.floor(y / zoom_factor).astype(np.int16)

    # recombine to a list of pairs
    # scaled_points = np.array([x_scaled, y_scaled]).T
    scaled_points = np.column_stack((x_scaled, y_scaled))
    print("scaled points shape: {0}, {1}".format(scaled_points.shape, scaled_points))

    # we needed them recombined so we could get the unique pairs
    scaled_points = np.unique(scaled_points, axis=0)
    print("scaled points shape: {0}, {1}".format(scaled_points.shape, scaled_points))


if __name__ == "__main__":
    point_splitting_demo()
    zoomed_in_region_demo()
    zoomed_out_region_demo()
    coords_demo()
    rotation_calc_demo()
    points_shape()
    trig_demo()
    rescale_demo()