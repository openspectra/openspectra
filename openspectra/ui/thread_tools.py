from PyQt5.QtCore import QThreadPool, QRunnable, QMetaType, pyqtSignal, QObject

from openspectra.image import BandDescriptor, GreyscaleImage, RGBImage, Image
from openspectra.openspecrtra_tools import OpenSpectraImageTools
from openspectra.openspectra_file import OpenSpectraFile
from openspectra.utils import Logger, LogHelper


class GreyscaleImageTask(QRunnable):

    __LOG:Logger = LogHelper.logger("GreyscaleImageTask")

    grey_image_created = pyqtSignal(GreyscaleImage)

    def __init__(self, image_tools:OpenSpectraImageTools, band:int,
            band_descriptor:BandDescriptor, call_back):
        super().__init__()
        self.__image_tools = image_tools
        self.__band = band
        self.__band_descriptor = band_descriptor
        self.__call_back = call_back

    def run(self):
        GreyscaleImageTask.__LOG.debug("Task creating image...")
        image = self.__image_tools.greyscale_image(self.__band, self.__band_descriptor)
        GreyscaleImageTask.__LOG.debug("Task calling call back...")
        self.__call_back(image)


class RGBImageTask(QRunnable):

    rgb_image_created = pyqtSignal(RGBImage)

    def __init__(self, image_tools:OpenSpectraImageTools, red:int, green:int, blue:int,
            red_descriptor:BandDescriptor, green_descriptor:BandDescriptor,
            blue_descriptor:BandDescriptor, call_back):
        super().__init__()
        self.__image_tools = image_tools
        self.__red = red
        self.__green = green
        self.__blue = blue
        self.__red_descriptor = red_descriptor
        self.__green_descriptor = green_descriptor
        self.__blue_descriptor = blue_descriptor
        self.__call_back = call_back

    def run(self):
        image = self.__image_tools.rgb_image(self.__red, self.__green, self.__blue,
            self.__red_descriptor, self.__green_descriptor, self.__blue_descriptor)
        self.__call_back(image)


class ThreadedImageTools(QObject):
    """A wrapper for OpenSpectraImageTools that allows Images to be created
    from data in a separate thread in a QT application.  This allows the UI to keep
    functioning when processing large data sets into an image.  For example
    generating an rgb image from a large, in terms of lines and samples, data file"""

    image_created = pyqtSignal(Image)

    def __init__(self, file:OpenSpectraFile):
        super().__init__()
        self.__image_tools = OpenSpectraImageTools(file)
        self.__thread_pool = QThreadPool.globalInstance()

    def greyscale_image(self, band:int, band_descriptor:BandDescriptor):
        task = GreyscaleImageTask(self.__image_tools, band, band_descriptor, self.__handle_image_complete)
        task.setAutoDelete(True)
        self.__thread_pool.start(task)

    def rgb_image(self, red:int, green:int, blue:int,
            red_descriptor:BandDescriptor, green_descriptor:BandDescriptor,
            blue_descriptor:BandDescriptor):
        task = RGBImageTask(self.__image_tools, red, green, blue,
            red_descriptor, green_descriptor, blue_descriptor, self.__handle_image_complete)
        task.setAutoDelete(True)
        self.__thread_pool.start(task)

    def __handle_image_complete(self, image:Image):
        self.image_created.emit(image)
