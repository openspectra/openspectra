import numpy as np
from numpy import ma

if __name__ == "__main__":

    data = np.arange(1, 10)
    print(data)

    low_mask = data.view(ma.MaskedArray)
    low_mask.mask = [data < 3]
    print("low_mask: ", low_mask)
    print("data: ", data)

    high_mask = data.view(ma.MaskedArray)
    high_mask.mask = [data > 7]
    print("high_mask: ", high_mask)
    print("data: ", data)

    full_mask = low_mask & high_mask
    print("full_mask: ", full_mask)
    print("data: ", data)

    # data = full_mask * 3
    full_mask = full_mask * 3
    print("\nfull_mask * 3: ", full_mask)
    print("data: ", data)

    low_mask[low_mask.mask] = 0
    print("\n0 low_mask: ", low_mask)
    print("full_mask: ", full_mask)
    print("data: ", data)

    high_mask[high_mask.mask] = 255
    print("\n255 high_mask: ", high_mask)
    print("full_mask: ", full_mask)
    print("data: ", data)

    data[~full_mask.mask] = full_mask[~full_mask.mask]
    print("data: ", data)
