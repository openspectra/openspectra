#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog
from PyQt5.QtGui import QIcon

from openspectra.openspectra_file import OpenSpectraFileFactory
from openspectra.ui.bandlist import BandList
from openspectra.ui.windowmanager import WindowManager


class OpenSpectraUI(QMainWindow):

    def __init__(self):
        super(OpenSpectraUI, self).__init__(None)
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

        # TODO figure out/get icons
        open_action = QAction(QIcon('open.png'), '&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open file')
        open_action.triggered.connect(self.__open)

        plot_action = QAction(QIcon('plot.png'), '&Plot', self)
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
        # fileMenu.addAction(exitAct)

        plot_menu = menu_bar.addMenu("&Plot")
        plot_menu.addAction(plot_action)

        self.__band_list = BandList(self)
        self.setCentralWidget(self.__band_list)

        self.__window_manager = WindowManager(self.__band_list)

        self.statusBar().showMessage('Ready')
        self.setGeometry(10, 25, 270, 700)
        self.show()

    def __open(self):
        # TODO remove hard coded path
        file_dialog = QFileDialog.getOpenFileName(None, "Open file", "/Users/jconti/dev/data/JoeSamples")
        file_name = file_dialog[0]

        file = OpenSpectraFileFactory.create_open_spectra_file(file_name)
        self.__window_manager.add_file(file)

    def __plot(self):
        pass
