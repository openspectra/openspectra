#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import logging
import os
import sys
import traceback
from typing import Dict, Tuple, List

from PyQt5.QtCore import pyqtSlot, QObject, QRect, pyqtSignal, QChildEvent, Qt, QStandardPaths
from PyQt5.QtGui import QGuiApplication, QScreen, QImage
from PyQt5.QtWidgets import QTreeWidgetItem, QFileDialog, QMessageBox, QCheckBox, QMainWindow

from openspectra.image import Image, GreyscaleImage, RGBImage, Band, BandDescriptor
from openspectra.openspecrtra_tools import OpenSpectraHistogramTools, OpenSpectraBandTools, OpenSpectraImageTools, \
    RegionOfInterest, OpenSpectraRegionTools, SubCubeTools
from openspectra.openspectra_file import OpenSpectraFile, OpenSpectraHeader, OpenSpectraFileFactory, \
    OpenSpectraFileError
from openspectra.ui.bandlist import BandList, RGBSelectedBands
from openspectra.ui.imagedisplay import MainImageDisplayWindow, AdjustedMouseEvent, AreaSelectedEvent, \
    ZoomImageDisplayWindow, RegionDisplayItem, WindowCloseEvent, ImageDisplayWindow
from openspectra.ui.plotdisplay import LinePlotDisplayWindow, HistogramDisplayWindow, LimitChangeEvent, LimitResetEvent
from openspectra.ui.thread_tools import ThreadedImageTools
from openspectra.ui.toolsdisplay import RegionOfInterestDisplayWindow, RegionStatsEvent, RegionToggleEvent, \
    RegionCloseEvent, RegionNameChangeEvent, RegionSaveEvent, SubCubeWindow, FileSubCubeParams, SaveSubCubeEvent, \
    ZoomSetWindow
from openspectra.utils import LogHelper, Logger, OpenSpectraProperties


class MenuEvent(QObject):

    OPEN_EVENT:int = 0
    CLOSE_EVENT:int = 1
    SAVE_EVENT:int = 2
    HIST_PLOT_EVENT:int = 3
    SPEC_PLOT_EVENT:int = 4
    ZOOM_IN:int = 5
    ZOOM_OUT:int = 6
    ZOOM_RESET:int = 7
    ZOOM_SET:int = 8

    def __init__(self, event_type:int, window:QMainWindow):
        super().__init__()
        self.__event_type = event_type
        self.__window = window

    def event_type(self) -> int:
        return self.__event_type

    def window(self) -> QMainWindow:
        return self.__window


class SaveManager(QObject):

    __LOG:Logger = LogHelper.logger("SaveManager")

    def __init__(self, default_dir: os.PathLike, caption:str, filter_str:str, extension:str):
        super().__init__()
        self.__save_dir_default = default_dir
        self.__caption = caption
        self.__filter_str = filter_str
        self.__extension = extension

    def save_dialog(self, default_name:str) -> str:
        # TODO there appears to be an unresolved problem with QFileDialog when using native dialogs at least on Mac
        # seems to be related to the text field where you would type a file name not getting cleaned up which
        # may explain why it only seems to impact the save dialog.
        # |QFileDialog.ShowDirsOnly only good with native dialog

        default_save_name = os.path.join(self.__save_dir_default, default_name)
        SaveManager.__LOG.debug("Default location: {0}", self.__save_dir_default)
        dialog_result = QFileDialog.getSaveFileName(caption=self.__caption, directory=default_save_name,
            filter=self.__filter_str, options=QFileDialog.DontUseNativeDialog)

        file_name:str = dialog_result[0]
        if file_name:
            if not file_name.endswith(self.__extension):
                file_name = file_name + self.__extension

        # save the last save location, default there next time
        split_path = os.path.split(file_name)
        if split_path[0]:
            self.__save_dir_default = split_path[0]

        return file_name


class ExceptionManager(QObject):

    def __init__(self):
        super().__init__()

    def _logger(self) -> Logger:
        pass

    def _handle_exception(self, message:str, sys_info:tuple, trace_back:str):
        error_msg = "{}: {} {}".format(message, sys_info[0], sys_info[1])
        tb = traceback.format_exc()
        self._logger().error("{}\n{}".format(error_msg, trace_back))
        self._error_prompt(error_msg, trace_back)

    def _error_prompt(self, error_msg:str, trace_back:str=None):
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Critical)
        dialog.setText(error_msg)
        if trace_back is not None:
            dialog.setDetailedText(trace_back)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec()


class WindowManager(ExceptionManager):

    __LOG:Logger = LogHelper.logger("WindowManager")

    image_closed = pyqtSignal(WindowCloseEvent)
    plot_closed = pyqtSignal(WindowCloseEvent)
    plot_opened = pyqtSignal(MenuEvent)
    zoom_in = pyqtSignal(MenuEvent)
    zoom_out = pyqtSignal(MenuEvent)
    zoom_reset = pyqtSignal(MenuEvent)
    zoom_factor_changed = pyqtSignal(float)

    def __init__(self, parent_window:QMainWindow, band_list:BandList):
        super().__init__()
        screen:QScreen = QGuiApplication.primaryScreen()
        self.__screen_geometry:QRect = screen.geometry()

        WindowManager.__LOG.debug("Screen height: {0}, width: {1}",
            self.__screen_geometry.height(), self.__screen_geometry.width())

        # The available size is the size excluding window manager reserved areas such as task bars and system menus.
        self.__available_geometry:QRect = screen.availableGeometry()
        WindowManager.__LOG.debug("Available height: {0}, width: {1}",
            self.__available_geometry.height(), self.__available_geometry.width())

        self.__parent_window = parent_window
        self.__file_managers:Dict[str, FileManager] = dict()
        self.__band_list = band_list
        self.__band_list.bandSelected.connect(self.__handle_band_select)
        self.__band_list.rgbSelected.connect(self.__handle_rgb_select)

        self.__default_open_dir = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        self.__save_manager = SaveManager(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
                                "Save Data", "", "")

        self.__zoom_set_window:ZoomSetWindow = ZoomSetWindow()
        self.__zoom_set_window.zoom_factor_changed.connect(self.zoom_factor_changed)
        self.__zoom_set_window.move(self.__screen_geometry.width() - self.__zoom_set_window.width() - 5, 0)

    def open_file(self):
        file_dialog = QFileDialog.getOpenFileName(self.__parent_window, "Open file", self.__default_open_dir)
        file_name = file_dialog[0]

        if len(file_name) > 0:
            try:
                file = OpenSpectraFileFactory.create_open_spectra_file(file_name)
                self.add_file(file)

                # save the last save location, default there next time
                split_path = os.path.split(file_name)
                if split_path[0]:
                    self.__default_open_dir = split_path[0]

            except:
                self._handle_exception("Failed to open file {} with error".
                    format(file_name), sys.exc_info(), traceback.format_exc())
        else:
            WindowManager.__LOG.debug("File open canceled...")

    def add_file(self, file:OpenSpectraFile):
        file_manager = FileManager(file, self)
        file_name = file_manager.file_name()
        if file_name in self.__file_managers:
            # TODO file names must be unique, handle dups somehow, no need to reopen really
            # TODO Just throw a up a dialog box saying it's already open?
            return

        self.__file_managers[file_name] = file_manager
        self.__band_list.add_file(file_name, file_manager.header().band_count(), file_manager.band_tools())

        if WindowManager.__LOG.isEnabledFor(logging.DEBUG):
            WindowManager.__LOG.debug("{0}", file.header().dump())

    def close_file(self, file_name:str):
        if file_name is not None and file_name in self.__file_managers:
            manager = self.__file_managers.pop(file_name, None)
            if manager is not None:
                manager.close()

            self.__band_list.remove_file(file_name)
            WindowManager.__LOG.debug("File {} closed", file_name)

    def screen_geometry(self) -> QRect:
        return self.__screen_geometry

    def available_geometry(self) -> QRect:
        return self.__available_geometry

    def parent_window(self) -> QMainWindow:
        return self.__parent_window

    def zoom_factor(self) -> float:
        return self.__zoom_set_window.zoom_factor()

    def open_save_subcube(self, file_name:str):
        if len(self.__file_managers) > 0:
            files:Dict[str, FileSubCubeParams] = dict()
            if file_name is not None:
                manager = self.__file_managers.get(file_name)
                if manager is not None:
                    header: OpenSpectraHeader = manager.header()
                    params = FileSubCubeParams(file_name, header.lines(), header.samples(),
                        header.band_count(), header.interleave())
                    files[file_name] = params
                else:
                    dialog = QMessageBox()
                    dialog.setIcon(QMessageBox.Critical)
                    dialog.setText("An internal error occurred, file '{}' doesn't appear to be open".format(file_name))
                    dialog.addButton(QMessageBox.Ok)
                    dialog.exec()
            else:
                for file_name, manager in self.__file_managers.items():
                    header:OpenSpectraHeader = manager.header()
                    params = FileSubCubeParams(file_name, header.lines(), header.samples(),
                        header.band_count(), header.interleave())
                    files[file_name] = params

            save_window = SubCubeWindow(files, self.parent_window())
            save_window.setAttribute(Qt.WA_DeleteOnClose, True)
            save_window.save.connect(self.__handle_save_subcube)
            save_window.show()
        else:
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Critical)
            dialog.setText("You must have at least one file open to save a sub-cube")
            dialog.addButton(QMessageBox.Ok)
            dialog.exec()

    @pyqtSlot(MenuEvent)
    def menu_event_handler(self, event:MenuEvent):
        event_type = event.event_type()
        target_window = event.window()
        WindowManager.__LOG.debug("Received menu event type: {}, for window: {}", event_type, target_window)

        try:
            if event_type == MenuEvent.OPEN_EVENT:
                self.open_file()

            elif event_type == MenuEvent.SAVE_EVENT:
                if target_window == self.__parent_window:
                    self.open_save_subcube(self.__band_list.selected_file())
                elif isinstance(target_window, ImageDisplayWindow):
                    # TODO will do a save image eventually
                    pass

            elif event_type == MenuEvent.CLOSE_EVENT:
                if target_window == self.__parent_window:
                    self.close_file(self.__band_list.selected_file())
                elif isinstance(target_window, ImageDisplayWindow):
                    # notify the window sets they'll decide if it applies
                    self.image_closed.emit(WindowCloseEvent(target_window))
                elif isinstance(target_window, LinePlotDisplayWindow) or isinstance(target_window,
                        HistogramDisplayWindow):
                    # notify the window sets they'll decide if it applies
                    self.plot_closed.emit(WindowCloseEvent(target_window))
                elif isinstance(target_window, ZoomSetWindow):
                    self.__zoom_set_window.close()

            elif (event_type == MenuEvent.SPEC_PLOT_EVENT or event_type == MenuEvent.HIST_PLOT_EVENT) and \
                    isinstance(target_window, ImageDisplayWindow):
                # notify the window sets they'll decide if it applies
                self.plot_opened.emit(event)

            elif event_type == MenuEvent.ZOOM_IN and isinstance(target_window, ZoomImageDisplayWindow):
                self.zoom_in.emit(event)

            elif event_type == MenuEvent.ZOOM_OUT and isinstance(target_window, ZoomImageDisplayWindow):
                self.zoom_out.emit(event)

            elif event_type == MenuEvent.ZOOM_RESET and isinstance(target_window, ZoomImageDisplayWindow):
                self.zoom_reset.emit(event)

            elif event_type == MenuEvent.ZOOM_SET:
                if not self.__zoom_set_window.isVisible():
                    self.__zoom_set_window.show()

                self.__zoom_set_window.activateWindow()

            else:
                WindowManager.__LOG.warning(
                    "Unrecognized menu event and window combination event type: {}, with target: {}",
                    event_type, target_window)
        except:
            # This will only catch the actions that don't result in an event being emitted
            self._handle_exception("Error handling menu action {}".format(event_type),
                sys.exc_info(), traceback.format_exc())

    @pyqtSlot(SaveSubCubeEvent)
    def __handle_save_subcube(self, event:SaveSubCubeEvent):
        file_name = event.source_file_name()
        WindowManager.__LOG.debug("__handle_save_subcube for source file: {0}, with params: {1}".
            format(file_name, event.cube_params()))

        try:
            if file_name in self.__file_managers:
                os_file = self.__file_managers[file_name].file()
                sub_cube_tools = SubCubeTools(os_file, event.cube_params())
                sub_cube_tools.create_sub_cube()
                default_name = "{}_{}_{}_{}".format(file_name,
                    max(sub_cube_tools.lines()) - min(sub_cube_tools.lines()),
                    max(sub_cube_tools.samples()) - min(sub_cube_tools.samples()),
                    max(sub_cube_tools.bands()) - min(sub_cube_tools.bands()))
                new_file_name = self.__save_manager.save_dialog(default_name)
                if new_file_name:
                    sub_cube_tools.save(new_file_name)
                else:
                    WindowManager.__LOG.debug("Sub cube save canceled")
            else:
                msg = "An internal error occurred.  Requested source cube, {}, does not appear to be open".\
                    format(file_name)
                WindowManager.__LOG.error(msg)
                self._error_prompt(msg)
        except:
            self._handle_exception("Failed save sub cube due to an error.",
                sys.exc_info(), traceback.format_exc())

    @pyqtSlot(QTreeWidgetItem)
    def __handle_band_select(self, item:QTreeWidgetItem):
        band_descriptor:BandDescriptor = item.data(0, Qt.UserRole)
        WindowManager.__LOG.debug("Band selected for: {0}, {1}, {2}".format(
            band_descriptor.file_name(), band_descriptor.band_name(), band_descriptor.wavelength_label()))

        try:
            parent_item = item.parent()
            file_name = parent_item.text(0)
            if file_name in self.__file_managers:
                file_set = self.__file_managers[file_name]
                file_set.add_grey_window_set(
                    parent_item.indexOfChild(item), band_descriptor)
            else:
                msg = "An interal error occurred.  Failed to find the bands' file in the open file list.  Looking for file named {}".\
                    format(file_name)
                WindowManager.__LOG.error(msg)
                self._error_prompt(msg)
        except:
            self._handle_exception("Failed open image due to an error.",
                sys.exc_info(), traceback.format_exc())

    @pyqtSlot(RGBSelectedBands)
    def __handle_rgb_select(self, bands:RGBSelectedBands):
        try:
            file_name = bands.file_name()
            if file_name in self.__file_managers:
                file_set = self.__file_managers[file_name]
                file_set.add_rgb_window_set(bands)
            else:
                msg = "An interal error occurred.  Failed to find the bands' file in the open file list.  Looking for file named {}".\
                    format(file_name)
                WindowManager.__LOG.error(msg)
                self._error_prompt(msg)
        except:
            self._handle_exception("Failed open image due to an error.",
                sys.exc_info(), traceback.format_exc())

    def _logger(self) -> Logger:
        return WindowManager.__LOG


class FileManager(QObject):

    __LOG:Logger = LogHelper.logger("FileManager")

    def __init__(self, file:OpenSpectraFile, window_manager:WindowManager):
        super().__init__()
        self.__window_manager = window_manager
        self.__file = file
        self.__band_tools = OpenSpectraBandTools(self.__file)
        self.__is_threading_enabled = OpenSpectraProperties.get_property("ThreadingEnabled", True)

        if self.__is_threading_enabled:
            FileManager.__LOG.info("Threading enabled for Image Tools")
            self.__image_tools = ThreadedImageTools(self.__file)
            self.__image_tools.image_created.connect(self.__create_window_set)
        else:
            FileManager.__LOG.info("Threading not enabled for Image Tools")
            self.__image_tools = OpenSpectraImageTools(self.__file)

        self.__window_sets = list()

    def add_rgb_window_set(self, bands:RGBSelectedBands):
        FileManager.__LOG.debug("New RGB window: {0} - {1} - {2}".format(
            bands.red_descriptor().label(), bands.green_descriptor().label(),
            bands.blue_descriptor().label()))

        image = self.__image_tools.rgb_image(
            bands.red_index(), bands.green_index(), bands.blue_index(),
            bands.red_descriptor(), bands.green_descriptor(), bands.blue_descriptor())

        if not self.__is_threading_enabled:
            if image is not None:
                self.__create_window_set(image)
            else:
                FileManager.__LOG.error("Image tools did not return and image")

    def add_grey_window_set(self, index:int, band_descriptor:BandDescriptor):
        image = self.__image_tools.greyscale_image(index, band_descriptor)
        if not self.__is_threading_enabled:
            if image is not None:
                self.__create_window_set(image)

    def header(self) -> OpenSpectraHeader:
        return self.__file.header()

    def file(self) -> OpenSpectraFile:
        return self.__file

    def file_name(self) -> str:
        return self.__file.name()

    def band_tools(self) -> OpenSpectraBandTools:
        return self.__band_tools

    def window_manager(self) -> WindowManager:
        return self.__window_manager

    def close(self):
        while len(self.__window_sets) > 0:
            window_set = self.__window_sets.pop()
            window_set.close()

    @pyqtSlot(Image)
    def __create_window_set(self, image:Image):
        FileManager.__LOG.debug("__create_window_set called...")
        title = image.label()
        window_set = WindowSet(image, title, self)
        window_set.closed.connect(self.__handle_windowset_closed)

        # TODO need a layout manager
        y = 25
        if len(self.__window_sets) == 0:
            x = 300
        else:
            rect = self.__window_sets[len(self.__window_sets) - 1].get_image_window_geometry()
            x = rect.x() + rect.width() + 25

        window_set.init_position(x, y)
        self.__window_sets.append(window_set)

    @pyqtSlot(QChildEvent)
    def __handle_windowset_closed(self, event:QChildEvent):
        window_set = event.child()
        # if the file was closed the window_set will have been closed already
        if window_set in self.__window_sets:
            self.__window_sets.remove(window_set)
            del window_set

        FileManager.__LOG.debug("WindowSets open {0}", len(self.__window_sets))


class WindowSet(QObject):

    __LOG:Logger = LogHelper.logger("WindowSet")

    closed = pyqtSignal(QChildEvent)

    def __init__(self, image:Image, title:str, file_manager:FileManager):
        super().__init__()
        self.__file_manager = file_manager
        self.__image = image
        self.__title = title

        self.__histogram_tools = OpenSpectraHistogramTools(self.__image)
        self.__band_tools = file_manager.band_tools()

        self.__init_image_window()
        self.__init_plot_windows()
        self.__init_roi()

    def __init_image_window(self):
        if isinstance(self.__image, GreyscaleImage):
            self.__main_image_window = MainImageDisplayWindow(self.__image, self.__title,
                QImage.Format_Grayscale8, self.__file_manager.window_manager().available_geometry(),
                self.__file_manager.header().map_info(),
                self.file_manager().window_manager().parent_window())
            self.__zoom_image_window = ZoomImageDisplayWindow(self.__image, self.__title,
                QImage.Format_Grayscale8, self.__file_manager.window_manager().available_geometry(),
                self.__file_manager.window_manager().zoom_factor(),
                self.__file_manager.header().map_info(),
                self.file_manager().window_manager().parent_window())
        elif isinstance(self.__image, RGBImage):
            self.__main_image_window = MainImageDisplayWindow(self.__image, self.__title,
                QImage.Format_RGB32, self.__file_manager.window_manager().available_geometry(),
                self.__file_manager.header().map_info(),
                self.file_manager().window_manager().parent_window())
            self.__zoom_image_window = ZoomImageDisplayWindow(self.__image, self.__title,
                QImage.Format_RGB32, self.__file_manager.window_manager().available_geometry(),
                self.__file_manager.window_manager().zoom_factor(),
                self.__file_manager.header().map_info(),
                self.file_manager().window_manager().parent_window())
        else:
            raise TypeError("Image type not recognized, found type: {0}".
                format(type(self.__image)))

        # assure the windows get deleted when closed
        self.__main_image_window.setAttribute(Qt.WA_DeleteOnClose, True)
        self.__zoom_image_window.setAttribute(Qt.WA_DeleteOnClose, True)

        self.__main_image_window.connect_zoom_window(self.__zoom_image_window)

        self.__main_image_window.pixel_selected.connect(self.__handle_pixel_click)
        self.__main_image_window.mouse_moved.connect(self.__handle_mouse_move)
        self.__main_image_window.closed.connect(self.__handle_image_closed)
        self.__main_image_window.area_selected.connect(self.__handle_area_selected)
        self.__main_image_window.area_selected.connect(self.__zoom_image_window.handle_region_selected)

        self.__zoom_image_window.pixel_selected.connect(self.__handle_pixel_click)
        self.__zoom_image_window.mouse_moved.connect(self.__handle_mouse_move)
        self.__zoom_image_window.closed.connect(self.__handle_image_closed)
        self.__zoom_image_window.area_selected.connect(self.__handle_area_selected)
        self.__zoom_image_window.area_selected.connect(self.__main_image_window.handle_region_selected)
        self.file_manager().window_manager().zoom_factor_changed.connect(self.__zoom_image_window.handle_zoom_factor_changed)

        # Register for close events coming from the menu system
        self.__file_manager.window_manager().image_closed.connect(self.__handle_image_closed)
        self.__file_manager.window_manager().plot_closed.connect(self.__handle_plot_closed)
        self.__file_manager.window_manager().plot_opened.connect(self.__handle_plot_open)
        self.__file_manager.window_manager().zoom_in.connect(self.__handle_zoom_in)
        self.__file_manager.window_manager().zoom_out.connect(self.__handle_zoom_out)
        self.__file_manager.window_manager().zoom_reset.connect(self.__handle_zoom_reset)

    def __init_plot_windows(self):
        self.__spec_plot_window = LinePlotDisplayWindow(self.__main_image_window)

        self.__histogram_window = HistogramDisplayWindow(self.__main_image_window)
        self.__histogram_init = False
        self.__histogram_window.limit_changed.connect(self.__handle_hist_limit_change)
        self.__histogram_window.limits_reset.connect(self.__handle_hist_limits_reset)

    def __init_roi(self):
        # RegionOfInterestManager is a singleton so all WindowSets
        # will get a reference to the same instance
        self.__roi_manager = RegionOfInterestManager.get_instance()

        # Register so we know if the region window is closed
        self.__roi_manager.window_closed.connect(self.__handle_region_window_close)

        # a dictionary to keep track of the band stats windows
        self.__band_stats_windows:Dict[str, LinePlotDisplayWindow] = dict()

    def __init_histogram(self):
        if not self.__histogram_init:
            if isinstance(self.__image, GreyscaleImage):
                raw_hist = self.__histogram_tools.raw_histogram()
                image_hist = self.__histogram_tools.adjusted_histogram()
                self.__histogram_window.create_plot_control(raw_hist, image_hist, Band.GREY)
                self.__histogram_init = True
            elif isinstance(self.__image, RGBImage):
                self.__histogram_window.create_plot_control(
                    self.__histogram_tools.raw_histogram(Band.RED),
                    self.__histogram_tools.adjusted_histogram(Band.RED), Band.RED)
                self.__histogram_window.create_plot_control(
                    self.__histogram_tools.raw_histogram(Band.GREEN),
                    self.__histogram_tools.adjusted_histogram(Band.GREEN), Band.GREEN)
                self.__histogram_window.create_plot_control(
                    self.__histogram_tools.raw_histogram(Band.BLUE),
                    self.__histogram_tools.adjusted_histogram(Band.BLUE), Band.BLUE)
                self.__histogram_init = True
            else:
                WindowSet.__LOG.error("Window set has unknown image type")

        # TODO need some sort of layout manager?
        window_rect = self.get_image_window_geometry()
        self.__histogram_window.setGeometry(window_rect.x(), window_rect.y() + window_rect.height() + 50, 800, 400)
        self.__histogram_window.show()

    @pyqtSlot(MenuEvent)
    def __handle_zoom_reset(self, event:MenuEvent):
        if event.window() == self.__zoom_image_window:
            self.__zoom_image_window.handle_zoom_reset()

    @pyqtSlot(MenuEvent)
    def __handle_zoom_in(self, event:MenuEvent):
        if event.window() == self.__zoom_image_window:
            self.__zoom_image_window.handle_zoom_in()

    @pyqtSlot(MenuEvent)
    def __handle_zoom_out(self, event:MenuEvent):
        if event.window() == self.__zoom_image_window:
            self.__zoom_image_window.handle_zoom_out()

    @pyqtSlot(MenuEvent)
    def __handle_plot_open(self, event:MenuEvent):
        target_window = event.window()
        if target_window == self.__main_image_window or target_window == self.__zoom_image_window:
            WindowSet.__LOG.debug("__handle_plot type: {}, target: {}", event.event_type(), target_window)
            event_type = event.event_type()

            if event_type == MenuEvent.HIST_PLOT_EVENT and not self.__histogram_window.isVisible():
                self.__init_histogram()
            elif event_type == MenuEvent.SPEC_PLOT_EVENT and not self.__spec_plot_window.isVisible():
                # TODO need some sort of layout manager?
                window_rect = self.get_image_window_geometry()
                self.__spec_plot_window.setGeometry(window_rect.x() + 150, window_rect.y() + window_rect.height() + 50, 500, 400)
                self.__spec_plot_window.show()
            else:
                WindowSet.__LOG.warning("Unknown menu plot event type: {}", event_type)

    @pyqtSlot(AdjustedMouseEvent)
    def __handle_pixel_click(self, event:AdjustedMouseEvent):
        if self.__spec_plot_window.isVisible():
            plot_data = self.__band_tools.spectral_plot(event.pixel_y(), event.pixel_x())
            plot_data.color = "g"
            self.__spec_plot_window.add_plot(plot_data)

    @pyqtSlot(AdjustedMouseEvent)
    def __handle_mouse_move(self, event:AdjustedMouseEvent):
        if self.__spec_plot_window.isVisible():
            plot_data = self.__band_tools.spectral_plot(event.pixel_y(), event.pixel_x())
            self.__spec_plot_window.plot(plot_data)

    @pyqtSlot(WindowCloseEvent)
    def __handle_plot_closed(self, event:WindowCloseEvent):
        target_window = event.target()
        if target_window == self.__spec_plot_window:
            self.__spec_plot_window.close()
        elif target_window == self.__histogram_window:
            self.__histogram_window.close()
        else:
            self.__handle_band_stats_closed(target_window)

    @pyqtSlot(WindowCloseEvent)
    def __handle_image_closed(self, event:WindowCloseEvent):
        target_window = event.target()
        if target_window == self.__main_image_window or target_window == self.__zoom_image_window:
            WindowSet.__LOG.debug("__handle_image_closed target: {}", target_window)
            if self.__zoom_image_window is not None:
                # disconnect so we don't get a second event
                self.__zoom_image_window.closed.disconnect(self.__handle_image_closed)
                self.__zoom_image_window.close()
                self.__zoom_image_window = None

            if self.__main_image_window is not None:
                # disconnect so we don't get a second event
                self.__main_image_window.closed.disconnect(self.__handle_image_closed)
                self.__main_image_window.close()
                self.__main_image_window = None

            if self.__histogram_window is not None:
                self.__histogram_window.close()
                self.__histogram_window = None

            if self.__spec_plot_window is not None:
                # It should have been closed when the main window, it's parent closed
                self.__spec_plot_window.close()
                self.__spec_plot_window = None

            while len(self.__band_stats_windows) > 0:
                key, window = self.__band_stats_windows.popitem()
                window.close()

            self.closed.emit(QChildEvent(QChildEvent.ChildRemoved, self))

    @pyqtSlot()
    def __handle_region_window_close(self):
        while len(self.__band_stats_windows) != 0:
            key, value = self.__band_stats_windows.popitem()
            value.close()

        self.__main_image_window.remove_all_regions()
        self.__zoom_image_window.remove_all_regions()

    @pyqtSlot(LimitResetEvent)
    def __handle_hist_limits_reset(self):
        self.__image.reset_stretch()
        self.__image.adjust()
        self.__main_image_window.refresh_image()
        self.__zoom_image_window.refresh_image()

        bands = list()
        if isinstance(self.__image, RGBImage):
            bands.extend([Band.RED, Band.GREEN, Band.BLUE])
        else:
            bands.append(Band.GREY)

        for band in bands:
            image_hist = self.__histogram_tools.adjusted_histogram(band)
            raw_data = self.__histogram_tools.raw_histogram(band)
            self.__histogram_window.update_limits(raw_data, band)
            self.__histogram_window.set_adjusted_data(image_hist, band)

    @pyqtSlot(LimitChangeEvent)
    def __handle_hist_limit_change(self, event:LimitChangeEvent):
        WindowSet.__LOG.debug("limit change event {0}, {1}", event.lower_limit(), event.upper_limit())
        updated:bool = False
        if event.has_upper_limit_change():
            self.__image.set_high_cutoff(event.upper_limit(), event.band())
            updated = True
            WindowSet.__LOG.debug("limit change event upper limit: {0}", event.upper_limit())

        if event.has_lower_limit_change():
            self.__image.set_low_cutoff(event.lower_limit(), event.band())
            updated = True
            WindowSet.__LOG.debug("Got limit change event lower limit: {0}", event.lower_limit())

        if updated:
            self.__image.adjust()

            # TODO use event instead?
            # trigger update in image window
            self.__main_image_window.refresh_image()
            self.__zoom_image_window.refresh_image()

            # TODO replotting the whole thing is bit inefficient?
            # TODO don't have the label here
            image_hist = self.__histogram_tools.adjusted_histogram(event.band())
            self.__histogram_window.set_adjusted_data(image_hist, event.band())
        else:
            WindowSet.__LOG.warning("Got limit change event with no limits")

    @pyqtSlot(AreaSelectedEvent)
    def __handle_area_selected(self, event:AreaSelectedEvent):
        region = event.region()
        self.__roi_manager.add_region(region, event.display_item(), self)

    @pyqtSlot(QMainWindow)
    def __handle_band_stats_closed(self, target_window:LinePlotDisplayWindow):
        delete_key = None
        for key, value in self.__band_stats_windows.items():
            if value == target_window:
                delete_key = key
                break
        if delete_key is not None:
            # Disconnect close listener in case we're closing from the menu
            # and the close below actually does close it so we don't get called again
            target_window.closed.disconnect(self.__handle_band_stats_closed)

            # if it's already been closed by window decorator this should harm anything
            target_window.close()

            # now finally remove our reference
            del self.__band_stats_windows[delete_key]
        WindowSet.__LOG.debug("Dummy statement")

    def init_position(self, x:int, y:int):
        # TODO need some sort of layout manager?
        self.__main_image_window.move(x, y)
        self.__main_image_window.show()

        self.__zoom_image_window.move(x + 50, y + 50)
        self.__zoom_image_window.show()

    def get_image_window_geometry(self):
        return self.__main_image_window.geometry()

    def band_tools(self) -> OpenSpectraBandTools:
        return self.__band_tools

    def file_manager(self) -> FileManager:
        return self.__file_manager

    def close(self, target_window:QMainWindow=None):
        if target_window is not None:
            if isinstance(target_window, ImageDisplayWindow) and \
                    (target_window == self.__main_image_window or target_window == self.__zoom_image_window):
                self.__handle_image_closed(WindowCloseEvent(target_window))
        else:
            self.__handle_image_closed(WindowCloseEvent(self.__main_image_window))

    @pyqtSlot(RegionStatsEvent)
    def handle_region_stats(self, event:RegionStatsEvent):
        region = event.region()
        lines = region.y_points()
        samples = region.x_points()
        WindowSet.__LOG.debug("lines dim: {0}, samples dim: {1}", lines.ndim, samples.ndim)

        band_stats_window = LinePlotDisplayWindow(self.__main_image_window, "Band Stats")
        # Make sure band stats window gets deleted on close, we won't reuse them here
        band_stats_window.setAttribute(Qt.WA_DeleteOnClose, True)
        band_stats_window.closed.connect(self.__handle_band_stats_closed)
        self.__band_stats_windows[region] = band_stats_window

        # TODO still??? bug here when image window has been resized, need adjusted coords
        stats_plot = self.__band_tools.statistics_plot(lines, samples, "Region: {0}".format(region.display_name()))
        band_stats_window.plot(stats_plot.mean())
        band_stats_window.add_plot(stats_plot.min())
        band_stats_window.add_plot(stats_plot.max())
        band_stats_window.add_plot(stats_plot.plus_one_std())
        band_stats_window.add_plot(stats_plot.minus_one_std())

        # TODO need some sort of layout manager?
        rect = self.__histogram_window.geometry()
        band_stats_window.setGeometry(rect.x() + 75, rect.y() + 75, 500, 400)
        band_stats_window.show()

    @pyqtSlot(RegionCloseEvent)
    def handle_region_closed(self, event:RegionCloseEvent):
        region = event.region()
        if region in self.__band_stats_windows:
            self.__band_stats_windows[region].close()
            # Shouldn't need this since we set Qt.WA_DeleteOnClose when creating the window
            # so check if it's still there first
            if region in self.__band_stats_windows:
                del self.__band_stats_windows[region]
                WindowSet.__LOG.warning("Band stat window was still in the list after being closed")

    @pyqtSlot(RegionNameChangeEvent)
    def handle_region_name_changed(self, event:RegionNameChangeEvent):
        region = event.region()
        WindowSet.__LOG.debug("new band stats title {0}: ", region.display_name())

        if region in self.__band_stats_windows:
            self.__band_stats_windows[region]. \
                set_plot_title("Region: {0}".format(region.display_name()))


class RegionSet:

    def __init__(self, region:RegionOfInterest, window_set:WindowSet,
            display_item:RegionDisplayItem, is_saved:bool=False):
        self.__region = region
        self.__window_set = window_set
        self.__display_item = display_item
        self.__is_saved = is_saved

    def region(self):
        return self.__region

    def window_set(self) -> WindowSet:
        return self.__window_set

    def display_item(self) -> RegionDisplayItem:
        return self.__display_item

    def is_saved(self) -> bool:
        return self.__is_saved

    def set_saved(self, is_saved:bool):
        self.__is_saved = is_saved


class RegionSetManager(QObject):

    __LOG:Logger = LogHelper.logger("RegionSetManager")

    def __init__(self, region_window:RegionOfInterestDisplayWindow):
        super().__init__()
        self.__region_window = region_window
        self.__region_window.region_name_changed.connect(self.__handle_region_name_changed)
        self.__region_window.region_toggled.connect(self.__handle_region_toggled)
        self.__region_window.stats_clicked.connect(self.__handle_stats_clicked)

        self.__region_display_items:Dict[RegionOfInterest, RegionSet] = dict()
        self.__window_sets:Dict[WindowSet, List[RegionSet]] = dict()

    @pyqtSlot(QChildEvent)
    def __handle_window_set_closed(self, event:QChildEvent):
        RegionSetManager.__LOG.debug("__handle_window_set_closed called for window set: {}", event.child())
        window_set = event.child()
        if window_set in self.__window_sets:
            region_set_list = self.__window_sets.pop(window_set, None)
            while len(region_set_list) > 0:
                region_set = region_set_list.pop()
                region_set.display_item().close()

                region = region_set.region()
                self.__region_display_items.pop(region)
                self.__region_window.remove_item(region)

    @pyqtSlot(RegionNameChangeEvent)
    def __handle_region_name_changed(self, event:RegionNameChangeEvent):
        region = event.region()
        if region in self.__region_display_items:
            self.__region_display_items[region].window_set().handle_region_name_changed(event)
        else:
            RegionSetManager.__LOG.warning("Region with id: {0}, name: {1} not found handling name event",
                region, region.display_name())

    @pyqtSlot(RegionToggleEvent)
    def __handle_region_toggled(self, event:RegionToggleEvent):
        region = event.region()
        if region in self.__region_display_items:
            display_item = self.__region_display_items[region].display_item()
            display_item.set_is_on(not display_item.is_on())
        else:
            RegionSetManager.__LOG.warning("Region with id: {0}, name: {1} not found handling toggle event",
                region, region.display_name())

    @pyqtSlot(RegionStatsEvent)
    def __handle_stats_clicked(self, event:RegionStatsEvent):
        region = event.region()
        if region in self.__region_display_items:
            self.__region_display_items[region].window_set().handle_region_stats(event)
        else:
            RegionSetManager.__LOG.warning("Region with id: {0}, name: {1} not found handling stats event",
                region, region.display_name())

    def add(self, region:RegionOfInterest, display_item:RegionDisplayItem, window_set:WindowSet):
        region_set = RegionSet(region, window_set, display_item)
        self.__region_display_items[region] = region_set

        if window_set not in self.__window_sets:
            window_set.closed.connect(self.__handle_window_set_closed)
            region_set_list:List[RegionSet] = list()
            region_set_list.append(region_set)
            self.__window_sets[window_set] = region_set_list
        else:
            self.__window_sets[window_set].append(region_set)

    def get(self, region:RegionOfInterest) -> RegionSet:
        return self.__region_display_items.get(region, None)

    def close(self, region_set:RegionSet, event:RegionCloseEvent):
        region = event.region()
        self.__region_display_items.pop(region, None)

        window_set = region_set.window_set()
        window_set.handle_region_closed(event)
        self.__window_sets.pop(window_set)

        region_set.display_item().close()
        self.__region_window.remove(event)

    def clear_all(self):
        self.__region_display_items.clear()
        self.__window_sets.clear()


class RegionOfInterestManager(QObject):

    __LOG:Logger = LogHelper.logger("RegionOfInterestManager")

    window_closed = pyqtSignal()

    # Since QObject doesn't want to play well with the metaclass approach
    # to creating a singleton we'll take a slightly less elegant approach
    __instance = None

    @staticmethod
    def get_instance():
        if RegionOfInterestManager.__instance is None:
            RegionOfInterestManager()

        return RegionOfInterestManager.__instance

    def __init__(self):
        # Prevent all but the first call to our constructor
        if RegionOfInterestManager.__instance is not None:
            raise Exception("RegionOfInterestManager is a singleton, use RegionOfInterestManager.Get_Instance() instead")
        else:
            super().__init__()
            # TODO figure out how to position the window??
            # Region of interest window, note we intentionally don't set Qt.WA_DeleteOnClose
            # because we can reuse it easily.
            self.__region_window = RegionOfInterestDisplayWindow()
            self.__region_window.region_saved.connect(self.__handle_region_saved)
            self.__region_window.region_closed.connect(self.__handle_region_closed)
            self.__region_window.closed.connect(self.__handle_window_closed)

            self.__region_set_manager = RegionSetManager(self.__region_window)
            self.__counter = 1

            self.__include_bands_default = Qt.Unchecked
            self.__save_manager = SaveManager(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
                                    "Save Region", "CSV files (*.csv)", ".csv")
            # the single instance
            RegionOfInterestManager.__instance = self

    def add_region(self, region:RegionOfInterest, display_item:RegionDisplayItem, window_set:WindowSet):
        if region.display_name() is None:
            region.set_display_name("Region {0}".format(self.__counter))
            self.__counter += 1

        # Set the regions map info if it's available
        map_info = window_set.file_manager().header().map_info()
        if map_info is not None:
            region.set_map_info(map_info)
        self.__region_window.add_item(region, display_item.color())
        self.__region_set_manager.add(region, display_item, window_set)

        if not self.__region_window.isVisible():
            self.__region_window.show()

    @pyqtSlot(MenuEvent)
    def handle_menu_close(self, event:MenuEvent):
        if event.window() == self.__region_window:
            self.__region_window.close()

    @pyqtSlot(RegionSaveEvent)
    def __handle_region_saved(self, event:RegionSaveEvent):
        region = event.region()
        RegionOfInterestManager.__LOG.debug("Region saved for region: {0}".format(region.display_name()))

        # prompt for save bands or not
        result, include_bands = self.__save_prompt(region)

        if result == QMessageBox.Save:
            region_set = self.__region_set_manager.get(region)
            if region_set is not None:
                region_tools = OpenSpectraRegionTools(region, region_set.window_set().band_tools())
                self.__include_bands_default = Qt.Checked if include_bands else Qt.Unchecked
                file_name = self.__save_manager.save_dialog(region.display_name())

                if file_name:
                    region_tools.save_region(file_name, include_bands=include_bands)
                    region_set.set_saved(True)
                else:
                    RegionOfInterestManager.__LOG.debug("Region save canceled")
            else:
                # Report region not found?  Shouldn't happen...
                # TODO raise here?
                RegionOfInterestManager.__LOG.error(
                    "Attempt to save region failed because the region could not be found, region name: {0}".
                        format(region.display_name()))

    def __save_prompt(self, region:RegionOfInterest) -> Tuple[int, bool]:
        dialog = QMessageBox(self.__region_window)
        dialog.setIcon(QMessageBox.Question)
        dialog.setText("Save region '{0}'?".format(region.display_name()))
        check_box = QCheckBox("Include bands?", dialog)
        check_box.setCheckState(self.__include_bands_default)
        dialog.setCheckBox(check_box)
        dialog.addButton(QMessageBox.Cancel)
        dialog.addButton(QMessageBox.Save)
        result = dialog.exec()
        include_bands = dialog.checkBox().checkState() == Qt.Checked
        RegionOfInterestManager.__LOG.debug("Save dialog result: {0}, is checked: {1}", result, include_bands)
        return result, include_bands

    def __close_prompt(self, region:RegionOfInterest) -> int:
        dialog = QMessageBox(self.__region_window)
        dialog.setIcon(QMessageBox.Question)
        dialog.setText("Are you sure you want close the unsaved region '{0}'?  It will be lost.".
            format(region.display_name()))
        dialog.addButton(QMessageBox.Cancel)
        dialog.addButton(QMessageBox.Yes)
        result = dialog.exec()
        RegionOfInterestManager.__LOG.debug("Close dialog result: {0}", result)
        return result

    @pyqtSlot(RegionCloseEvent)
    def __handle_region_closed(self, event:RegionCloseEvent):
        region = event.region()
        region_set = self.__region_set_manager.get(region)
        if region_set is not None:
            if not region_set.is_saved():
                result = self.__close_prompt(region)
                if result == QMessageBox.Yes:
                    self.__region_set_manager.close(region_set, event)
                else:
                    RegionOfInterestManager.__LOG.debug("Region close canceled")
            else:
                self.__region_set_manager.close(region_set, event)
        else:
            RegionOfInterestManager.__LOG.warning("Region with id: {0}, name: {1} not found handling close event",
                region, region.display_name())

    @pyqtSlot()
    def __handle_window_closed(self):
        RegionOfInterestManager.__LOG.debug("__handle_window_closed called...")
        self.__region_window.remove_all()
        self.__region_set_manager.clear_all()
        self.window_closed.emit()
