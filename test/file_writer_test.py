#  Developed by Joseph M. Conti and Joseph W. Boardman on 7/10/19, 12:05 AM.
#  Last modified 7/10/19, 12:05 AM
#  Copyright (c) 2019. All rights reserved.
import time

import numpy as np

from openspectra.openspectra_file import OpenSpectraFileFactory


def write_sub_cube_slice():
    test_file = "unit_tests/resources/cup95_eff_fixed"
    # test_file = "../resources/cup95_eff_fixed"
    os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)

    start_time = time.process_time()

    # TODO intent was cube would be zero based but slice treats the end param as position - 1
    # TODO although this is the python/numpy way so stick with it?
    sub_cube = os_file.cube((0, 350), (0, 400), (0, 50)).astype(np.int16)
    # print("sub-cube.shape: ", sub_cube.shape)
    # print("sub-cube: ", sub_cube)

    flat_iterator = sub_cube.flat
    with open("./resources/test_out_cube1", "wb") as out_file:
        for item in flat_iterator:
            out_file.write(item)

        out_file.flush()

    end_time = time.process_time()
    print("Total time with slice: {0}".format(end_time - start_time))


def write_sub_cube_list():
    test_file = "unit_tests/resources/cup95_eff_fixed"
    # test_file = "../resources/cup95_eff_fixed"
    os_file = OpenSpectraFileFactory.create_open_spectra_file(test_file)

    start_time = time.process_time()

    # TODO intent was cube would be zero based but slice treats the end param as position - 1
    # TODO although this is the python/numpy way so stick with it?
    bands = list(range(50))
    sub_cube = os_file.cube((0, 350), (0, 400), bands).astype(np.int16)
    # print("sub-cube.shape: ", sub_cube.shape)
    # print("sub-cube: ", sub_cube)

    flat_iterator = sub_cube.flat
    with open("./resources/test_out_cube2", "wb") as out_file:
        for item in flat_iterator:
            out_file.write(item)

        out_file.flush()

    end_time = time.process_time()
    print("Total time with list: {0}".format(end_time - start_time))


if __name__ == "__main__":
    write_sub_cube_slice()
    write_sub_cube_list()