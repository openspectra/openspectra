import numpy as np


if __name__ == '__main__':

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
