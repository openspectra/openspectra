#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
from math import floor

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, QApplication, QWidget

from openspectra.ui.bandlist import BandList
from openspectra.ui.imagedisplay import ImageDisplayWindow, ZoomImageDisplayWindow
from openspectra.ui.windowmanager import WindowManager, MenuEvent, RegionOfInterestManager
from openspectra.utils import Logger, LogHelper


class OpenSpectraUI(QMainWindow):

    __LOG:Logger = LogHelper.logger("OpenSpectraUI")

    menu_event = pyqtSignal(MenuEvent)

    def __init__(self):
        super().__init__()

        # listen for focus change events so we can control which menu items are available
        qApp = QtWidgets.qApp
        qApp.focusChanged.connect(self.__handle_focus_changed)

        self.__init_ui()

        # TODO QMainWindow can store the state of its layout with saveState(); it can later be retrieved
        # with restoreState(). It is the position and size (relative to the size of the main window) of the
        # toolbars and dock widgets that are stored.

    def __init_ui(self):
        self.setGeometry(25, 50, 600, 0)
        self.setWindowTitle("OpenSpectra")
        # self.setWindowIcon(QIcon("web.png"))

        # TODO on Mac this is redundant and doesn't seem to do anything, other paltforms probably need it
        # exitAct = QAction(QIcon("exit.png"), "&Exit", self)
        # exitAct.setShortcut("Ctrl+Q")
        # exitAct.setStatusTip("Exit application")
        # exitAct.triggered.connect(qApp.quit)

        self.__open_action = QAction("&Open", self)
        self.__open_action.setShortcut("Ctrl+O")
        self.__open_action.setStatusTip("Open file")
        self.__open_action.triggered.connect(self.__open)

        self.__save_action = QAction("&Save", self)
        self.__save_action.setShortcut("Ctrl+S")
        self.__save_action.setStatusTip("Save sub-cube")
        self.__save_action.triggered.connect(self.__save)
        # TODO probably init to disabled until file opened?

        self.__close_action = QAction("&Close", self)
        self.__close_action.setShortcut("Ctrl+C")
        self.__close_action.setStatusTip("Close file")
        self.__close_action.triggered.connect(self.__close)
        # TODO probably init to disabled until file opened?

        self.__spectrum_plot_action = QAction("&Spectrum", self)
        self.__spectrum_plot_action.setShortcut("Ctrl+P")
        self.__spectrum_plot_action.setStatusTip("Open spectrum plot for current window")
        self.__spectrum_plot_action.triggered.connect(self.__plot_spec)
        self.__spectrum_plot_action.setDisabled(True)

        self.__histogram_plot_action = QAction("&Histogram", self)
        self.__histogram_plot_action.setShortcut("Ctrl+G")
        self.__histogram_plot_action.setStatusTip("Open histogram for current window")
        self.__histogram_plot_action.triggered.connect(self.__plot_hist)
        self.__histogram_plot_action.setDisabled(True)

        self.__set_zoom_action = QAction("&Set Zoom")
        self.__set_zoom_action.setShortcut("Ctrl+Z")
        self.__set_zoom_action.setStatusTip("Set the zoom factor")
        self.__set_zoom_action.triggered.connect(self.__set_zoom)

        self.__zoom_in_action = QAction("&Zoom In")
        self.__zoom_in_action.setShortcut("Ctrl++")
        self.__zoom_in_action.setStatusTip("Zoom in for current zoom window")
        self.__zoom_in_action.triggered.connect(self.__zoom_in)
        self.__zoom_in_action.setDisabled(True)

        self.__zoom_out_action = QAction("&Zoom Out")
        self.__zoom_out_action.setShortcut("Ctrl+-")
        self.__zoom_out_action.setStatusTip("Zoom out for current zoom window")
        self.__zoom_out_action.triggered.connect(self.__zoom_out)
        self.__zoom_out_action.setDisabled(True)

        self.__zoom_reset_action = QAction("&Zoom Reset")
        self.__zoom_reset_action.setShortcut("Ctrl+0")
        self.__zoom_reset_action.setStatusTip("Reset zoom to 1 to 1 for current zoom window")
        self.__zoom_reset_action.triggered.connect(self.__zoom_reset)
        self.__zoom_reset_action.setDisabled(True)

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.__open_action)
        file_menu.addAction(self.__save_action)
        file_menu.addAction(self.__close_action)
        # fileMenu.addAction(exitAct)

        plot_menu = menu_bar.addMenu("&Plot")
        plot_menu.addAction(self.__spectrum_plot_action)
        plot_menu.addAction(self.__histogram_plot_action)

        window_menu = menu_bar.addMenu("&Windows")
        window_menu.addAction(self.__set_zoom_action)
        window_menu.addAction(self.__zoom_reset_action)
        window_menu.addAction(self.__zoom_in_action)
        window_menu.addAction(self.__zoom_out_action)

        self.__band_list = BandList(self)
        self.setCentralWidget(self.__band_list)

        self.__window_manager = WindowManager(self, self.__band_list)
        self.menu_event.connect(self.__window_manager.menu_event_handler)
        roi_manager = RegionOfInterestManager.get_instance()
        self.menu_event.connect(roi_manager.handle_menu_close)

        available_geometry = self.__window_manager.available_geometry()

        self.statusBar().showMessage("Ready")
        self.setGeometry(2, 25, 270, floor(available_geometry.bottom() * 0.90))
        self.show()

    @pyqtSlot()
    def __open(self):
        self.__fire_menu_event(MenuEvent.OPEN_EVENT)

    @pyqtSlot()
    def __save(self):
        self.__fire_menu_event(MenuEvent.SAVE_EVENT)

    @pyqtSlot()
    def __close(self):
        self.__fire_menu_event(MenuEvent.CLOSE_EVENT)

    @pyqtSlot()
    def __plot_spec(self):
        self.__fire_menu_event(MenuEvent.SPEC_PLOT_EVENT)

    @pyqtSlot()
    def __plot_hist(self):
        self.__fire_menu_event(MenuEvent.HIST_PLOT_EVENT)

    @pyqtSlot()
    def __set_zoom(self):
        self.__fire_menu_event(MenuEvent.ZOOM_SET)

    @pyqtSlot()
    def __zoom_reset(self):
        self.__fire_menu_event(MenuEvent.ZOOM_RESET)

    @pyqtSlot()
    def __zoom_in(self):
        self.__fire_menu_event(MenuEvent.ZOOM_IN)

    @pyqtSlot()
    def __zoom_out(self):
        self.__fire_menu_event(MenuEvent.ZOOM_OUT)

    def __fire_menu_event(self, event_type:int):
        current_window:QWidget = QApplication.activeWindow()
        if current_window is not None:
            self.menu_event.emit(MenuEvent(event_type, current_window))

    @pyqtSlot("QWidget*", "QWidget*")
    def __handle_focus_changed(self, old:QWidget, new:QWidget):
        current_window = QApplication.activeWindow()
        OpenSpectraUI.__LOG.debug("__handle_focus_changed called old: {}, new: {}, active window: {}",
            old, new, current_window)

        # control which menus are available based on which window is active
        if current_window is not None and isinstance(current_window, ImageDisplayWindow):
            self.__spectrum_plot_action.setDisabled(False)
            self.__histogram_plot_action.setDisabled(False)

            if isinstance(current_window, ZoomImageDisplayWindow):
                self.__zoom_in_action.setDisabled(False)
                self.__zoom_out_action.setDisabled(False)
                self.__zoom_reset_action.setDisabled(False)

        else:
            self.__spectrum_plot_action.setDisabled(True)
            self.__histogram_plot_action.setDisabled(True)
            self.__zoom_in_action.setDisabled(True)
            self.__zoom_out_action.setDisabled(True)
            self.__zoom_reset_action.setDisabled(True)

