import itertools

import numpy as np
from numpy import ma

from PyQt5.QtCore import QPoint

if __name__ == "__main__":
    r1 = np.arange(0, 2)
    r2 = np.arange(10, 25)
    # print(list(itertools.product(r1, r2)))
    points = ma.array(list(itertools.product(r1, r2)))
    print(points)

    # for x, y in points:
    #     print("x, y ", x, y)
        # if x < 4 and y > 7:

    print(len(points))
    val_range = range(len(points))
    print(val_range)
    for i in val_range:
        # print("i, point: ", i, points[i][0], points[i][1])
        if points[i][0] <= 4 and points[i][1] >= 17:
            points[i] = ma.masked

    print(points)

    x = points[:, 0]
    y = points[:, 1]
    # print(x)
    # print(y)

    x = x[~x.mask]
    y = y[~y.mask]

    print(x)
    print(y)
    print(len(x) == len(y))
    # good_points = points[~points.mask]

    # print(good_points)

    # points = ma.array(list(itertools.product(r1, r2)))
    # points = np.array(np.meshgrid(r1, r2))
    # print(points)

    # px, py = np.array(np.meshgrid(r1, r2))
    # print("px: ", px, "py: ", py)

    # points = points.reshape(-2, 2)
    # print(points)

    # for point in points:
    #     point.mask = point[0] < 3 and point[1] < 3
    #     print(points)

    # mask = np.full(points.shape[0], False, dtype=bool)
    # for i in range(points.shape[0] - 1):
    #     mask[i] = True if (points[i][0] <= 3 and points[i][1] <= 3) else False
    #
    # points.mask = mask
    # print(mask)
    # print(points)
    #
    # x_range = ma.arange(125, 135)
    # print("x_range: ", x_range)
    # vals = range((x_range.size))
    # print("indexes: ", vals)
    # for x_index in vals:
    #     val =  x_range[x_index]
    #     print("index: ", x_index, "val: ", val)
    #     print(QPoint(val, 1))