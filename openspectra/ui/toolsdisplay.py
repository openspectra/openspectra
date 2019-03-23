#  Developed by Joseph M. Conti and Joseph W. Boardman on 3/17/19 2:30 PM.
#  Last modified 3/17/19 2:30 PM
#  Copyright (c) 2019. All rights reserved.
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, \
    QTableWidget, QTableWidgetItem, QApplication, QStyle, QPushButton

from openspectra.openspecrtra_tools import RegionOfInterest
from openspectra.utils import Logger, LogHelper


class RegionEvent(QObject):

    def __init__(self, region:RegionOfInterest):
        super().__init__(None)
        self.__region = region

    def region(self) -> RegionOfInterest:
        return self.__region


class RegionStatsEvent(RegionEvent):

    def __init__(self, region:RegionOfInterest):
        super().__init__(region)


class RegionToggleEvent(RegionEvent):

    def __init__(self, region:RegionOfInterest, is_on:bool):
        super().__init__(region)
        self.__is_on = is_on

    def is_on(self) -> bool:
        return self.is_on()


class StatsButton(QPushButton):

    stats_clicked = pyqtSignal(RegionStatsEvent)

    __LOG:Logger = LogHelper.logger("StatsButton")

    def __init__(self, text:str, region:RegionOfInterest, parent=None):
        super().__init__(text, parent)
        self.__region = region
        self.clicked.connect(self.__handle_stats_click)

    def __handle_stats_click(self):
        StatsButton.__LOG.debug("Stats button clicked for region: {0}", self.__region.id())


class RegionOfInterestControl(QWidget):

    __LOG:Logger = LogHelper.logger("RegionOfInterestControl")

    stats_clicked = pyqtSignal(RegionStatsEvent)
    region_toggled = pyqtSignal(RegionToggleEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__regions = list()
        layout = QVBoxLayout()

        self.__margins = 5
        layout.setContentsMargins(self.__margins, self.__margins, self.__margins, self.__margins)

        self.__rows = 0
        self.__table = QTableWidget(self.__rows, 5, self)
        self.__table.setShowGrid(False)
        self.__table.verticalHeader().hide()
        self.__table.cellClicked.connect(self.__handle_cell_clicked)
        self.__table.cellChanged.connect(self.__handle_cell_changed)

        self.__table.setColumnWidth(0, 40)

        self.__table.setHorizontalHeaderLabels(["Color", "Name", "Size (h x w)", "Stats", "Description"])
        layout.addWidget(self.__table)
        self.setLayout(layout)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__table.cellClicked.disconnect(self.__handle_cell_clicked)
        self.__table.cellChanged.disconnect(self.__handle_cell_changed)
        self.__table.setRowCount(self.__rows + 1)

        name_item = QTableWidgetItem(region.name())

        color_item = QTableWidgetItem()
        color_item.setBackground(QBrush(color))
        color_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        color_item.setCheckState(Qt.Checked)

        stats_button = StatsButton("Stats", region)
        stats_button.stats_clicked.connect(self.stats_clicked)

        size_item = QTableWidgetItem(
            str(region.image_height()) + " x " + str(region.image_width()))
        size_item.setTextAlignment(Qt.AlignVCenter)

        image_name_item = QTableWidgetItem(region.image_name())

        self.__table.setItem(self.__rows, 0, color_item)
        self.__table.setItem(self.__rows, 1, name_item)
        self.__table.setItem(self.__rows, 2, size_item)
        self.__table.setCellWidget(self.__rows, 3, stats_button)
        self.__table.setItem(self.__rows, 4, image_name_item)

        if self.__rows == 0:
            self.__table.resizeColumnsToContents()
            length = self.__table.horizontalHeader().length()
            RegionOfInterestControl.__LOG.debug("Header length: {0}", length)
            self.setMinimumWidth(length + self.__margins * 2 +
                                 QApplication.style().pixelMetric(QStyle.PM_DefaultFrameWidth) * 2)
            self.__table.horizontalHeader().setStretchLastSection(True)

        self.__regions.append(region)
        self.__rows += 1
        self.__table.cellClicked.connect(self.__handle_cell_clicked)
        self.__table.cellChanged.connect(self.__handle_cell_changed)

    def __handle_cell_clicked(self, row:int, column:int):
        RegionOfInterestControl.__LOG.debug("Cell clicked row: {0}, column: {1}", row, column)
        if column == 0:
            region = self.__regions[row].id()
            is_on = self.__table.item(row, column).checkState() == Qt.Checked
            RegionOfInterestControl.__LOG.debug("Checkbox is on: {0}, region: {1}",
                is_on, region)
            if region is not None:
                self.region_toggled.emit(RegionToggleEvent(region, is_on))

    def __handle_cell_changed(self, row:int, column:int):
        RegionOfInterestControl.__LOG.debug("Cell changed row: {0}, column: {1}", row, column)
        if column == 1:
            item = self.__table.item(row, column)
            RegionOfInterestControl.__LOG.debug("Cell changed, new value: {0}", item.text())
            region:RegionOfInterest = self.__regions[row]
            region.set_name(item.text())

    # TODO for testing only, remove if not used otherwise
    # def resizeEvent(self, event:QResizeEvent):
    #     RegionOfInterestControl.__LOG.debug("Resize to {0}", event.size())


class RegionOfInterestDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("RegionOfInterestDisplayWindow")

    stats_clicked = pyqtSignal(RegionStatsEvent)
    region_toggled = pyqtSignal(RegionToggleEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__roi_control = RegionOfInterestControl()
        self.setCentralWidget(self.__roi_control)
        self.__roi_control.stats_clicked.connect(self.stats_clicked)
        self.__roi_control.region_toggled.connect(self.region_toggled)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__roi_control.add_item(region, color)

    # TODO for testing only, remove if not used otherwise
    # def resizeEvent(self, event:QResizeEvent):
    #     RegionOfInterestDisplayWindow.__LOG.debug("Resize to {0}", event.size())
