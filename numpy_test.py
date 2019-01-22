#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import numpy as np
from numpy import ma

def test3():
    scale:float = 1 / 1.333
    data = np.arange(999, 1010, dtype=np.int16)
    print(data)
    data = data * scale
    print(data)
    # data = np.floor(data, dtype=np.int16)
    data = np.floor(data).astype(np.int16)
    # data = np.fix(data)
    print(data)


def test2():
    img = np.arange(9)
    print(img)

    img.resize(3, 3)
    print(img)

    print(img[(0, 1)])

    # None of these work
    # index = np.array([[0, 0], [1, 1], [2, 2]])
    # index = np.array((0, 0))
    # index = [(0, 0), (1, 1)]
    # index = np.array([(0, 0), (1, 1)])
    # index = list([(0, 0), (1, 1)])
    # index = (0, 1), (1, 1), (2, 2)

    # this is list of x values, list of y values so 1st pair is 0,0
    # index = (0, 1, 2), (0, 2, 1) # works
    # index = [(0, 1, 2), (0, 2, 1)] # works
    # index = [[0, 1, 2], [0, 2, 1]] # works
    # index = np.array([(0, 1, 2), (0, 2, 1)]) # nope
    # index = [np.array([0, 1, 2]), np.array([0, 2, 1])] # works

    x = ma.array([0, 1, 2])
    y = ma.array([0, 2, 1])
    x[1] = ma.masked
    y[1] = ma.masked

    x1 = x[~x.mask]
    y1 = y[~y.mask]
    # index = [x1, y1]

    # print("index: ", index)
    print(img[x1, y1])


def test1():
    sq = np.arange(4)
    print(sq)

    sq = sq.reshape(2, 2)
    print(sq)
    print(sq[0, 0])
    print(sq[0, 1])
    print(sq[1, 0])
    print(sq[1, 1])

    cube = np.arange(27)
    print(cube)

    cube = cube.reshape(3, 3, 3)
    print(cube)

    print("cube[0]\n", str(cube[0]))
    print("cube[1]\n", str(cube[1]))
    print("cube[2]\n", str(cube[2]))

    print(cube[0, 0, 0])
    print(cube[1, 0, 0])
    print(cube[2, 0, 0])

    print(cube[:, :, 0])
    print(cube[:, :, 1])
    print(cube[:, :, 2])

    print(cube[0, 0, 0])
    print(cube[0, 0, 1])
    print(cube[0, 0, 2])

    print(cube[0, 1, 0])
    print(cube[0, 1, 1])
    print(cube[0, 1, 2])

    print(cube[0, 2, 0])
    print(cube[0, 2, 1])
    print(cube[0, 2, 2])

    print(cube[1, 0, 0])
    print(cube[1, 0, 1])
    print(cube[1, 0, 2])

    print(cube[1, 1, 0])
    print(cube[1, 1, 1])
    print(cube[1, 1, 2])

    print(cube[1, 2, 0])
    print(cube[1, 2, 1])
    print(cube[1, 2, 2])

    print(cube[2, 0, 0])
    print(cube[2, 0, 1])
    print(cube[2, 0, 2])

    print(cube[2, 1, 0])
    print(cube[2, 1, 1])
    print(cube[2, 1, 2])

    print(cube[2, 2, 0])
    print(cube[2, 2, 1])
    print(cube[2, 2, 2])

    print(cube[0, :, :])
    print(cube[1, :, :])
    print(cube[2, :, :])

    empty = np.empty((3, 3, 3))
    print("Empty:", empty)

    zero = np.zeros((3, 3, 3))
    print("Zero:", zero)


if __name__ == '__main__':

    test3()
