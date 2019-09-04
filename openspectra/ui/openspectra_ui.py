#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
import os
from math import floor

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon

from openspectra.openspectra_file import OpenSpectraFileFactory, OpenSpectraFileError
from openspectra.ui.bandlist import BandList
from openspectra.ui.windowmanager import WindowManager
from openspectra.utils import Logger, LogHelper


class OpenSpectraUI(QMainWindow):

    __LOG:Logger = LogHelper.logger("OpenSpectraUI")

    def __init__(self):
        super(OpenSpectraUI, self).__init__(None)

        self.__save_dir_default = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        self.__init_ui()

        # TODO QMainWindow can store the state of its layout with saveState(); it can later be retrieved
        # with restoreState(). It is the position and size (relative to the size of the main window) of the
        # toolbars and dock widgets that are stored.

    def __init_ui(self):
        self.setGeometry(25, 50, 600, 0)
        self.setWindowTitle('OpenSpectra')
        # self.setWindowIcon(QIcon('web.png'))

        # TODO on Mac this is redundant and doesn't seem to do anything, other paltforms probably need it
        # exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        # exitAct.setShortcut('Ctrl+Q')
        # exitAct.setStatusTip('Exit application')
        # exitAct.triggered.connect(qApp.quit)

        open_action = QAction('&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open file')
        open_action.triggered.connect(self.__open)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save sub-cube")
        save_action.triggered.connect(self.__save)

        close_action = QAction("&Close", self)
        close_action.setShortcut("Ctrl+C")
        close_action.setStatusTip("Close file")
        close_action.triggered.connect(self.__close)

        plot_action = QAction('&Plot', self)
        plot_action.setShortcut('Ctrl+P')
        plot_action.setStatusTip('Plot stuff')
        plot_action.triggered.connect(self.__plot)

        # TODO??
        # self.toolbar = self.addToolBar('Open')
        # self.toolbar.addAction(openAct)

        menu_bar = self.menuBar()

        # TODO turn off native menus for Mac?? Probably not, rather do paltform specific mods
        # menubar.setNativeMenuBar(False)

        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(close_action)
        # fileMenu.addAction(exitAct)

        plot_menu = menu_bar.addMenu("&Plot")
        plot_menu.addAction(plot_action)

        self.__band_list = BandList(self)
        self.setCentralWidget(self.__band_list)

        self.__window_manager = WindowManager(self, self.__band_list)
        available_geometry = self.__window_manager.available_geometry()

        self.statusBar().showMessage('Ready')
        self.setGeometry(2, 25, 270, floor(available_geometry.bottom() * 0.90))
        self.show()

    def __open(self):
        file_dialog = QFileDialog.getOpenFileName(self, "Open file", self.__save_dir_default)
        file_name = file_dialog[0]

        if len(file_name) > 0:
            try:
                file = OpenSpectraFileFactory.create_open_spectra_file(file_name)
                self.__window_manager.add_file(file)

                # save the last save location, default there next time
                split_path = os.path.split(file_name)
                if split_path[0]:
                    self.__save_dir_default = split_path[0]

            except OpenSpectraFileError as e:
                OpenSpectraUI.__LOG.error("Failed to open file with error: {0}".format(e))
                self.__file_not_found_prompt(file_name)
        else:
            OpenSpectraUI.__LOG.debug("File open canceled...")

    def __save(self):
        self.__window_manager.open_save_subcube(self.__band_list.selected_file())

    def __close(self):
        self.__window_manager.close_file(self.__band_list.selected_file())

    def __plot(self):
        pass

    def __file_not_found_prompt(self, file_name:str):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setText("File named '{0}' not found!".format(file_name))
        dialog.addButton(QMessageBox.Ok)
        dialog.exec()



