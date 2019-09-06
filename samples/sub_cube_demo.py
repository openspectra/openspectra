#  Developed by Joseph M. Conti and Joseph W. Boardman on 7/11/19, 7:56 PM.
#  Last modified 7/11/19, 7:47 PM
#  Copyright (c) 2019. All rights reserved.
import numpy as np


def test_cude_slicing():

    # A simpler example with 3 x 3 x 3 cube
    # r = np.arange(0, 27)
    # print(r)

    # Below we call axes x, y ,z in terms of index order
    # in the reshape command
    # cube = r.reshape(3, 3, 3)
    # print("cube: ", cube)

    # print("[y, z] ", cube[0, :, :])
    # print("[y, z][1, 2] ", cube[0, :, :][1, 2])
    # print("[x, z] ", cube[:, 0, :])
    # print("[x, z][2, 1] ", cube[:, 0, :][2, 1])
    # like an image
    # print("[x, y] ", cube[:, :, 0])
    # print("[x, y][2, 0] ", cube[:, :, 0][2, 0])
    # portion of an image
    # print("[x, y] ", cube[0:2, 0:2, 0])

    # image = cube[0, :, :]
    # print("image: ", image)
    # print("slice: ", image[0:2, 0:2])

    # same as
    # print("cube slice: ", cube[0, 0:2, 0:2])

    # sub_cube = cube[0:2, 0:2, 0:2]
    # print("sub-cube shape: ", sub_cube.shape)
    # print("sub-cube: ", sub_cube)

    # This is like a 3 x 3 image with 10 bands
    # and it simulates a BIP format because the images are
    # x (or axis 0) = lines, y (or axis 1) = samples and z (or axis 3) = bands
    r2 = np.arange(3 * 3 * 10)
    rect = r2.reshape(3, 3, 10)
    print("rect: ", rect)
    print("[y, z] ", rect[0, :, :])
    print("[x, z] ", rect[:, 0, :])

    # So this is like an image slice
    print("[x, y] ", rect[:, :, 0])

    print("sub-image slice: ", rect[0:2, 0:2, 0])

    double_image = rect[:, :, 0:2]
    print("2 images shape ", double_image.shape)
    print("2 images ", double_image)
    print("1st of 2 images ", double_image[:, :, 0])
    print("2nd of 2 images ", double_image[:, :, 1])

    # 2 trimmed down images
    sub_cube = rect[0:2, 0:2, 0:2]
    print("\nrect[0:2, 0:2, 0:2]")
    print("sub-cube: ", sub_cube)
    print("sub-cube image 1: ", sub_cube[:, :, 0])
    print("sub-cube image 2: ", sub_cube[:, :, 1])

    # Same as above
    sub_cube = rect[slice(0, 2, 1), slice(0, 2, 1), slice(0, 2, 1)]
    print("\nrect[slice(0, 2, 1), slice(0, 2, 1), slice(0, 2, 1)]")
    print("sub-cube: ", sub_cube)
    print("sub-cube image 1: ", sub_cube[:, :, 0])
    print("sub-cube image 2: ", sub_cube[:, :, 1])

    # Advanced indexing is triggered by use of the list here, others apply
    # and results in a copy rather than a view
    sub_cube = rect[0:2, 0:2, [0, 1]]
    print("\nrect[0:2, 0:2, [0, 1]]")
    print("sub-cube: ", sub_cube)
    print("sub-cube image 1: ", sub_cube[:, :, 0])
    print("sub-cube image 2: ", sub_cube[:, :, 1])

    # Can use this to select non-sequential bands for the sub-image!!!
    sub_cube_from_list = rect[0:2, 0:2, [0, 2, 4]]
    print("rect[0:2, 0:2, [0, 2, 4]]")
    print("sub_cube_from_list: ", sub_cube_from_list)
    print("sub_cube_from_list image 1: ", sub_cube_from_list[:, :, 0])
    print("sub_cube_from_list image 2: ", sub_cube_from_list[:, :, 1])
    print("sub_cube_from_list image 3: ", sub_cube_from_list[:, :, 2])

    # tuples work too
    sub_cube_from_tuple = rect[0:2, 0:2, (0, 2, 4)]
    print("sub_cube_from_tuple: ", sub_cube_from_tuple)
    print("sub_cube_from_tuple image 1: ", sub_cube_from_tuple[:, :, 0])
    print("sub_cube_from_tuple image 2: ", sub_cube_from_tuple[:, :, 1])
    print("sub_cube_from_tuple image 2: ", sub_cube_from_tuple[:, :, 2])

    rect[0, 0, 0] = 999999
    # print(rect)
    print(rect[0, 0, 0])
    # print(rect[:, :, 0])

    # But both were create with advanced indexing and therefore are copies
    print(sub_cube_from_list[0, 0, 0])
    print(sub_cube_from_tuple[0, 0, 0])
    # print("sub_cube_from_list ", sub_cube_from_list)
    # print("sub_cube_from_tuple ", sub_cube_from_tuple)


def format_change_demo():

    # This is like a 3 x 3 image with 10 bands
    # and it simulates a BIP format because the images are
    # x = lines, y = samples and z = bands
    r2 = np.arange(3 * 3 * 10)
    bip_cube = r2.reshape((3, 3, 10))
    # print("BIP cube ", bip_cube)

    # image slice
    bip_image = bip_cube[:, :, 0]
    print("BIP image [x, y] ", bip_image)

    # select a spectrum
    bip_spec = bip_cube[1, 1, :]
    print("BIP spectrum ", bip_spec)

    # Now lets turn it into a BIL format
    # move leave 0 axis 0, move 2 axis to 1, and 1 axis to 2
    bil_cube = bip_cube.transpose(0, 2, 1)
    # print("BIL cube ", bil_cube)

    # image slice
    bil_image = bil_cube[:, 0, :]
    print("BIL image [x, z] ", bil_image)

    # spectrum
    bil_spec = bil_cube[1, :, 1]
    print("BIL spectrum ", bil_spec)

    # And now a BSQ format
    bsq_cube = bil_cube.transpose(1, 0, 2)
    # print("BSQ cube ", bsq_cube)

    # image slice
    bsq_image = bsq_cube[0, :, :]
    print("BSQ image [y, z] ", bsq_image)

    # spectrum
    bsq_spec = bsq_cube[:, 1, 1]
    print("BSQ spectrum ", bsq_spec)

    assert np.array_equal(bip_image, bil_image)
    assert np.array_equal(bil_image, bsq_image)
    assert np.array_equal(bsq_image, bip_image)

    assert np.array_equal(bip_spec, bil_spec)
    assert np.array_equal(bil_spec, bsq_spec)
    assert np.array_equal(bsq_spec, bip_spec)


if __name__ == "__main__":
    """Demonstrates some of the concepts used for creating sub-cubes for more info
    about numpy slicing and indexing see https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html"""
    test_cude_slicing()
    format_change_demo()