from typing import Union

import numpy as np

from PyQt5.QtCore import pyqtSlot, QObject, QRect, pyqtSignal, QChildEvent
from PyQt5.QtGui import QGuiApplication, QScreen, QImage
from PyQt5.QtWidgets import QTreeWidgetItem

from openspectra.image import Image, GreyscaleImage, RGBImage
from openspectra.ui.bandlist import BandList, RGBSelectedBands
from openspectra.openspectra_file import OpenSpectraFile, OpenSpectraHeader
from openspectra.ui.imagedisplay import ImageDisplayWindow, AdjustedMouseEvent, AreaSelectedEvent
from openspectra.ui.plotdisplay import PlotData, LinePlotDisplayWindow, HistogramDisplayWindow, LimitChangeEvent


class WindowManager(QObject):

    def __init__(self, band_list:BandList):
        super(WindowManager, self).__init__(None)
        screen:QScreen = QGuiApplication.primaryScreen()
        self.__screen_geometery:QRect = screen.geometry()

        # TODO debug only
        print("Screen h,w", self.__screen_geometery.height(), ",", self.__screen_geometery.width())

        self.__file_sets = dict()
        self.__band_list = band_list
        self.__band_list.bandSelected.connect(self.__handle_band_select)
        self.__band_list.rgbSelected.connect(self.__handle_rgb_select)

    def __del__(self):
        self.__file_sets = None
        self.__band_list = None
        self.__screen_geometery = None

    def add_file(self, file:OpenSpectraFile):
        file_widget = self.__band_list.add_file(file)
        file_name = file_widget.text(0)

        if file_name in self.__file_sets:
            # TODO file names must be unique, handle dups somehow, no need to reopen really
            # TODO Just throw a up a dialog box saying it's already open?
            return

        file_set = FileManager(file, file_widget)
        self.__file_sets[file_name] = file_set

        # TODO remove this and below
        file.header().dump()

    def get_file(self, index=0) -> OpenSpectraFile:
        return self.__file_sets[index]

    @pyqtSlot(QTreeWidgetItem)
    def __handle_band_select(self, item:QTreeWidgetItem):
        parent_item = item.parent()
        file_name = parent_item.text(0)
        if file_name in self.__file_sets:
            file_set = self.__file_sets[file_name]
            file_set.add_grey_window_set(
                parent_item.indexOfChild(item), item.text(0))
        else:
            # TODO report or log somehow?
            pass

    @pyqtSlot(RGBSelectedBands)
    def __handle_rgb_select(self, bands:RGBSelectedBands):
        file_name = bands.file_name()
        if file_name in self.__file_sets:
            file_set = self.__file_sets[file_name]
            file_set.add_rgb_window_set(bands.red_index(), bands.green_index(),
                bands.blue_index(), bands.label())
        else:
            # TODO report or log somehow?
            pass


class FileManager(QObject):

    def __init__(self, file:OpenSpectraFile, file_widget:QTreeWidgetItem):
        super(FileManager, self).__init__(None)
        self.__file = file
        self.__file_widget = file_widget
        self.__file_name = file_widget.text(0)
        self.__window_sets = list()

    def __del__(self):
        print("FileSet.__del__ called...")
        self.__window_sets = None
        self.__file_name = None
        self.__file_widget = None
        self.__file = None

    def add_rgb_window_set(self, red, green, blue, label:str):
        image = self.__file.rgb_image(red, green, blue)
        self.__create_window_set(image, label)

    def add_grey_window_set(self, index, label:str):
        image = self.__file.greyscale_image(index)
        self.__create_window_set(image, label)

    def band(self, line:Union[int, tuple], sample:Union[int, tuple]) -> np.ndarray:
        return self.__file.band(line, sample)

    def header(self) -> OpenSpectraHeader:
        return self.__file.header()

    def __create_window_set(self, image:Image, label:str):
        window_set = WindowSet(image, self)
        window_set.closed.connect(self.__handle_windowset_closed)
        title = self.__file_name + ": " + label

        y = 25
        if len(self.__window_sets) == 0:
            x = 300
        else:
            rect = self.__window_sets[len(self.__window_sets) - 1].get_image_geometry()
            x = rect.x() + rect.width() + 25

        window_set.initialize(title, x, y)
        self.__window_sets.append(window_set)

    @pyqtSlot(QChildEvent)
    def __handle_windowset_closed(self, event:QChildEvent):
        window_set = event.child()
        self.__window_sets.remove(window_set)
        del window_set
        print("WindowSets open ", len(self.__window_sets))


class WindowSet(QObject):

    closed = pyqtSignal(QChildEvent)

    def __init__(self, image:Image, file_manager:FileManager):
        super(WindowSet, self).__init__(None)
        self.__image = image
        self.__file_manager = file_manager
        self.__image_window = None
        self.__spec_plot_window = LinePlotDisplayWindow()
        self.__histogram_window = HistogramDisplayWindow()
        self.__histogram_window.limit_changed.connect(self.__handle_hist_limit_change)
        self.__label = None

    def __del__(self):
        print("WindowSet.__del__ called...")
        self.__label = None
        self.__spec_plot_window = None
        self.__histogram_window = None
        self.__image_window = None
        self.__file_manager = None
        self.__image = None

    def initialize(self, label, x, y):
        if isinstance(self.__image, GreyscaleImage):
            self.__image_window = ImageDisplayWindow(self.__image, label,
                QImage.Format_Grayscale8)
        elif isinstance(self.__image, RGBImage):
            self.__image_window = ImageDisplayWindow(self.__image, label,
                QImage.Format_RGB32)
        else:
            raise TypeError("Image type not recognized, found type: {0}".
                format(type(self.__image)))

        self.__label = label
        self.__init_image_window(x, y)

        # TODO figure out what to do with RGB images
        if isinstance(self.__image, GreyscaleImage):
            self.__init_histogram(x, y)

    def __init_image_window(self, x, y):
        self.__image_window.pixel_selected.connect(self.__handle_pixel_click)
        self.__image_window.mouse_moved.connect(self.__handle_mouse_move)
        self.__image_window.closed.connect(self.__handle_image_closed)
        self.__image_window.area_selected.connect(self.__handle_area_selected)

        # TODO need some sort of layout manager?
        self.__image_window.move(x, y)
        self.__image_window.show()

    def __init_histogram(self, x, y):
        # TODO UI components shouldn't be doing these data manipulations to create the plot
        # TODO want to as much seperation as possible, should get the plot from an API so how do we ID the one we want here?
        # TODO x range should be natural and wee need to show raw data and processed data
        raw_data = self.__image.raw_data()
        raw_hist = PlotData(
            np.arange(raw_data.min(), raw_data.max() + 1, 1),
            raw_data.flatten(), "X-FixMe", "Y-FixMe", "Raw " + self.__label,
            "hist", "r", lower_limit=self.__image.low_cutoff(),
            upper_limit=self.__image.high_cutoff())
        self.__histogram_window.set_raw_data(raw_hist)

        image_data = self.__image.image_data()
        image_hist = PlotData(
            np.arange(image_data.min(), image_data.max() + 1, 1),
            image_data.flatten(), "X-FixMe", "Y-FixMe", "Adjusted " + self.__label, "hist")
        self.__histogram_window.set_adjusted_data(image_hist)

        # TODO need some sort of layout manager?
        self.__histogram_window.setGeometry(x, y + self.get_image_geometry().height() + 50, 800, 400)
        self.__histogram_window.show()

    def get_image_geometry(self):
        return self.__image_window.geometry()

    def __get_plot_data(self, x:Union[int, tuple], y:Union[int, tuple]) -> PlotData:
        line = y
        sample = x
        band = self.__file_manager.band(line, sample)
        wavelengths = self.__file_manager.header().wavelengths()

        # users expect upper left corner of image is 1, 1
        return PlotData(wavelengths, band, "Wavelength", "Brightness",
            "Spectra S-{0}, L-{1}".format(sample + 1, line + 1))

    @pyqtSlot(AdjustedMouseEvent)
    def __handle_pixel_click(self, event:AdjustedMouseEvent):
        if self.__spec_plot_window.isVisible():
            self.__spec_plot_window.canvas().add_plot(
                self.__get_plot_data(event.pixel_x(), event.pixel_y()))

    @pyqtSlot(AdjustedMouseEvent)
    def __handle_mouse_move(self, event:AdjustedMouseEvent):
        self.__spec_plot_window.canvas().plot(
            self.__get_plot_data(event.pixel_x(), event.pixel_y()))

        if not self.__spec_plot_window.isVisible():
            # TODO need some sort of layout manager?
            rect = self.__histogram_window.geometry()
            self.__spec_plot_window.setGeometry(rect.x() + 50, rect.y() + 50, 500, 400)
            self.__spec_plot_window.show()

    @pyqtSlot()
    def __handle_image_closed(self):
        self.__histogram_window.close()
        self.__histogram_window = None

        self.__spec_plot_window.close()
        self.__spec_plot_window = None

        self.closed.emit(QChildEvent(QChildEvent.ChildRemoved, self))

    @pyqtSlot(LimitChangeEvent)
    def __handle_hist_limit_change(self, event:LimitChangeEvent):
        print("Got limit change event ", event.id(), event.limit())
        if event.id() == "upper":
            self.__image.set_high_cutoff(event.limit())
        elif event.id() == "lower":
            self.__image.set_low_cutoff(event.limit())
        else:
            return

        self.__image.adjust()

        # TODO use event instead?
        # trigger update in image window
        self.__image_window.refresh_image()

        # TODO trigger update in adjusted histogram
        image_data = self.__image.image_data()
        # TODO replotting the whole thing is bit inefficient
        # TODO don't have the label here
        image_hist = PlotData(
            np.arange(image_data.min(), image_data.max() + 1, 1),
            image_data.flatten(), "X-FixMe", "Y-FixMe", "Adjusted " + self.__label, "hist")
        self.__histogram_window.set_adjusted_data(image_hist)

    @pyqtSlot(AreaSelectedEvent)
    def __handle_area_selected(self, event:AreaSelectedEvent):
        lines = event.y_points()
        samples = event.x_points()
        print("Got area: ", samples, lines)
        bands = self.__file_manager.band(lines, samples)
        # TODO OK so now we can get the bands, who should do the calculations???
        print("bands: ", bands)