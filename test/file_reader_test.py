import sys
import time
import os
from pathlib import Path
import numpy as np
from PIL import Image
import openspectra.image as img

class FileReader:

    def __init__(self):
        # "/Users/jconti/dev/data/JoeSamples/cup95_eff_fixed"
        # self.__lines, self.__bands, self.__samples = 350, 50, 400
        self.__data_type = np.int16

        # "/Users/jconti/dev/data/JoeSamples/ang20160928t135411_rfl_v1nx_nonortho"
        self.__lines, self.__bands, self.__samples = 6500, 425, 598
        self.__data_type = np.float32

        expected_size = self.__lines * self.__bands * self.__samples
        print("lines: {0}, bands: {1}, samples: {2}, expected array size {3}".
            format(self.__lines, self.__bands, self.__samples, expected_size))

    def loadTest1(self, file_name):
        if self.__open_file(file_name):
            print("Running test1...")
            # TODO so do I map the whole file then pull images and beands from that?

            start_time = time.process_time()
            # TODO so I'm still not sure if this is loading the whole file or just mappoing it
            file:np.memmap = np.memmap(self.__path, dtype=self.__data_type, mode='r', shape=(self.__lines, self.__bands, self.__samples))
            end_time = time.process_time()
            print("Loaded file array size: {0}, shape: {1}, in {2} ms".
                format(file.size, file.shape, (end_time - start_time) * 1000))
            print("File memory size is: {0} MB".format(sys.getsizeof(file) / 1000000))

            image_band = 3
            start_time = time.process_time()
            image_data = file[:, image_band, :]
            end_time = time.process_time()
            print("Loaded image array size: {0}, shape: {1}, in {2} ms".
                format(image_data.size, image_data.shape, (end_time - start_time) * 1000))
            print("image_data memory size is: {0} bytes".format(sys.getsizeof(image_data)))

            # TODO Adjustment takes a long time
            start_time = time.process_time()
            image_data = self.__adjust(image_data)
            end_time = time.process_time()
            print("Image adjustment time: {0} ms".format((end_time - start_time) * 1000))
            print("image_data memory size is: {0} MB".format(sys.getsizeof(image_data) / 1000000))

            start_time = time.process_time()
            image = Image.fromarray(image_data)
            end_time1 = time.process_time()
            image.show()
            end_time2 = time.process_time()
            print("Image format: {0}, mode: {1}, image time: {2} ms, show time: {3} ms".format(
                image.format, image.mode, (end_time1 - start_time) * 1000, (end_time2 - end_time1) * 1000))
            print("PIL image memory size is: {0} bytes".format(sys.getsizeof(image)))

            # TODO OK so this doesn't show up adjusted as I thought it might
            # image_data2 = file[:, image_band, :]
            # image2 = Image.fromarray(image_data2)
            # image2.show()

            # del image_data

            del file
            print("Test1 complete...")

            # TODO Or do I load images and bands directly??

            # start_time = time.process_time()
            # TODO loading 10x10x10 is actually taking longer than the whole file
            # file = np.memmap(self.__path, dtype=self.__data_type, mode='r', shape=(10, 10, 10))
            # end_time = time.process_time()
            # print("Loaded file size: {0}, shape: {1}, in {2} ms".format(file.size, file.shape, (end_time - start_time) * 1000))
            # del file

    def loadTest2(self, file_name):
        if self.__open_file(file_name):
            print("Running test2...")

            start_time = time.process_time()
            # TODO so I'm still not sure if this is loading the whole file or just mappoing it
            file:np.memmap = np.memmap(self.__path, dtype=self.__data_type, mode='r', shape=(self.__lines, self.__bands, self.__samples))
            end_time = time.process_time()
            print("Loaded file size: {0}, shape: {1}, in {2} ms".format(file.size, file.shape, (end_time - start_time) * 1000))
            print("File size is: {0}".format(sys.getsizeof(file)))

            image_band = 3
            start_time = time.process_time()
            image_data = file[:, image_band, :]
            end_time = time.process_time()
            print("Loaded image size: {0}, shape: {1}, in {2} ms".format(image_data.size, image_data.shape, (end_time - start_time) * 1000))

            # TODO not sure if copying is necessary or not, if not it seems manipulating the data is
            # TODO is changing the file data but as long as we don't flush should be OK
            # TODO see what happens if we look at the same location again
            # Copy the image to a new array
            start_time = time.process_time()
            pixels = np.copy(image_data)
            end_time = time.process_time()
            print("Image data copy time {0} ms".format((end_time - start_time) * 1000))
            print("image_data size is: {0}".format(sys.getsizeof(image_data)))
            print("pixels size is: {0}".format(sys.getsizeof(pixels)))

            # TODO Adjustment takes a long time
            start_time = time.process_time()
            pixels = self.__adjust(pixels)
            end_time = time.process_time()
            print("Image adjustment time: {0}".format((end_time - start_time) * 1000))
            print("image_data size is: {0}".format(sys.getsizeof(image_data)))
            print("pixels size is: {0}".format(sys.getsizeof(pixels)))

            start_time = time.process_time()
            image = Image.fromarray(pixels)
            end_time1 = time.process_time()
            image.show()
            end_time2 = time.process_time()
            print("Image format: {0}, mode: {1}, image time: {2}, show time: {3}".format(
                image.format, image.mode, (end_time1 - start_time) * 1000, (end_time2 - end_time1) * 1000))
            print("image_data size is: {0}".format(sys.getsizeof(image_data)))
            print("pixels size is: {0}".format(sys.getsizeof(pixels)))
            print("image size is: {0}".format(sys.getsizeof(image)))

            del pixels
            del file
            print("Test2 complete...")

    def loadTest3(self, file_name):
        if self.__open_file(file_name):
            print("Running test3...")

            start_time = time.process_time()
            # TODO so I'm still not sure if this is loading the whole file or just mappoing it
            file:np.memmap = np.memmap(self.__path, dtype=self.__data_type, mode='r', shape=(self.__lines, self.__bands, self.__samples))
            end_time = time.process_time()
            print("Loaded file size: {0}, shape: {1}, in {2} ms".format(file.size, file.shape, (end_time - start_time) * 1000))
            print("File size is: {0}".format(sys.getsizeof(file)))

            start_time = time.process_time()
            data = np.copy(file)
            end_time = time.process_time()
            print("Full array copied in: {0} ms".format((end_time - start_time) * 1000))
            print("File size is: {0}".format(sys.getsizeof(file)))
            print("Data size is: {0}".format(sys.getsizeof(data)))

            del file

            print("Copy of data size: {0}, shape: {1}".format(data.size, data.shape))
            print("Test3 complete...")

    def __open_file(self, file_name):
        self.__path = Path(file_name)
        print("File: {0} exits: {1}, size: {2} MB".format(
            self.__path.name, self.__path.exists(), os.path.getsize(self.__path) / 1000000))
        return self.__path.exists() and self.__path.is_file()

    def __adjust(self, image):
        return img.adjust_image(image)


if __name__ == '__main__':
    # file_name = "/Users/jconti/dev/data/JoeSamples/cup95_eff_fixed"
    file_name = "/Users/jconti/dev/data/JoeSamples/ang20160928t135411_rfl_v1nx_nonortho"

    file_reader = FileReader()
    file_reader.loadTest1(file_name)
    # file_reader.loadTest2(file_name)
    # file_reader.loadTest3(file_name)