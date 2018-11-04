from typing import Union

import numpy as np

from PyQt5.QtCore import pyqtSlot, QObject, QRect, pyqtSignal, QChildEvent
from PyQt5.QtGui import QGuiApplication, QScreen, QImage
from PyQt5.QtWidgets import QTreeWidgetItem

from openspectra.image import Image, GreyscaleImage, RGBImage
from openspectra.ui.bandlist import BandList, RGBSelectedBands
from openspectra.openspectra_file import OpenSpectraFile, OpenSpectraHeader
from openspectra.ui.imagedisplay import ImageDisplayWindow, AdjustedMouseEvent, AreaSelectedEvent
from openspectra.ui.plotdisplay import LinePlotDisplayWindow, HistogramDisplayWindow, LimitChangeEvent
from openspectra.openspecrtra_tools import OpenSpectraImageTools, OpenSpectraBandTools


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
        self.__band_tools = OpenSpectraBandTools(self.__file)
        self.__file_widget = file_widget
        self.__file_name = file_widget.text(0)
        self.__window_sets = list()

    def __del__(self):
        print("FileSet.__del__ called...")
        self.__window_sets = None
        self.__file_name = None
        self.__file_widget = None
        self.__band_tools = None
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

    def band_tools(self):
        return self.__band_tools

    def __create_window_set(self, image:Image, label:str):
        window_set = WindowSet(image, self)
        window_set.closed.connect(self.__handle_windowset_closed)
        title = self.__file_name + ": " + label

        y = 25
        if len(self.__window_sets) == 0:
            x = 300
        else:
            rect = self.__window_sets[len(self.__window_sets) - 1].get_image_window_geometry()
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
        self.__image_tools = OpenSpectraImageTools(self.__image)
        self.__band_tools = file_manager.band_tools()
        # TODO can probably remove self.__file_manager in favor of self.__band_tools??
        self.__file_manager = file_manager
        self.__image_window = None
        self.__spec_plot_window = LinePlotDisplayWindow()
        self.__band_stats_window = LinePlotDisplayWindow()
        self.__histogram_window = HistogramDisplayWindow()
        self.__histogram_window.limit_changed.connect(self.__handle_hist_limit_change)
        self.__label = None

    def __del__(self):
        print("WindowSet.__del__ called...")
        self.__label = None
        self.__spec_plot_window = None
        self.__band_stats_window = None
        self.__histogram_window = None
        self.__image_window = None
        self.__file_manager = None
        self.__band_tools = None
        self.__image_tools = None
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
        self.__image_tools.set_label(self.__label)
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
        raw_hist = self.__image_tools.raw_histogram()
        self.__histogram_window.set_raw_data(raw_hist)

        image_hist = self.__image_tools.adjusted_histogram()
        self.__histogram_window.set_adjusted_data(image_hist)

        # TODO need some sort of layout manager?
        self.__histogram_window.setGeometry(x, y + self.get_image_window_geometry().height() + 50, 800, 400)
        self.__histogram_window.show()

    def get_image_window_geometry(self):
        return self.__image_window.geometry()

    @pyqtSlot(AdjustedMouseEvent)
    def __handle_pixel_click(self, event:AdjustedMouseEvent):
        if self.__spec_plot_window.isVisible():
            plot_data = self.__band_tools.spectral_plot(event.pixel_y(), event.pixel_x())
            plot_data.color = "g"
            self.__spec_plot_window.add_plot(plot_data)

    @pyqtSlot(AdjustedMouseEvent)
    def __handle_mouse_move(self, event:AdjustedMouseEvent):
        plot_data = self.__band_tools.spectral_plot(event.pixel_y(), event.pixel_x())
        self.__spec_plot_window.plot(plot_data)

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

        # TODO replotting the whole thing is bit inefficient?
        # TODO don't have the label here
        image_hist = self.__image_tools.adjusted_histogram()
        self.__histogram_window.set_adjusted_data(image_hist)

    @pyqtSlot(AreaSelectedEvent)
    def __handle_area_selected(self, event:AreaSelectedEvent):
        if self.__band_stats_window.isVisible():
            self.__band_stats_window.clear()

        lines = event.y_points()
        samples = event.x_points()
        stats_plot = self.__band_tools.statistics_plot(lines, samples)
        self.__band_stats_window.plot(stats_plot.mean())
        self.__band_stats_window.add_plot(stats_plot.min())
        self.__band_stats_window.add_plot(stats_plot.max())
        self.__band_stats_window.add_plot(stats_plot.plus_one_std())
        self.__band_stats_window.add_plot(stats_plot.minus_one_std())

        # TODO need some sort of layout manager?
        rect = self.__histogram_window.geometry()
        self.__band_stats_window.setGeometry(rect.x() + 75, rect.y() + 75, 500, 400)

        if not self.__band_stats_window.isVisible():
            self.__band_stats_window.show()