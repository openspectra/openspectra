#  Developed by Joseph M. Conti and Joseph W. Boardman on 3/17/19 2:30 PM.
#  Last modified 3/17/19 2:30 PM
#  Copyright (c) 2019. All rights reserved.
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor, QPaintEvent, QPainter, QPalette, QPolygon, QBrush, QResizeEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout, \
    QTableWidget, QTableWidgetItem, QApplication, QStyle

from openspectra.openspecrtra_tools import RegionOfInterest
from openspectra.utils import Logger, LogHelper


class ColorDisplayControl(QLabel):

    def __init__(self, color:QColor, parent=None):
        super().__init__(parent)
        self.__color = color

        width = 10
        height = 20
        self.__polygon = QPolygon()
        for x in range(width):
            for y in range(height):
                self.__polygon << QPoint(x, y)

        self.setMinimumSize(width, height)
        self.setBackgroundRole(QPalette.Base)
        self.setBackgroundRole(QPalette.Light)
        self.show()

    def paintEvent(self, paint_event:QPaintEvent):
        super().paintEvent(paint_event)
        # not sure why but it seems we need to create the painter each time
        painter = QPainter(self)
        painter.setPen(self.__color)
        painter.drawPoints(self.__polygon)


class RegionOfInterestControl(QWidget):

    __LOG:Logger = LogHelper.logger("RegionOfInterestControl")

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)

        self.__rows = 0
        self.__table = QTableWidget(self.__rows, 5, self)
        self.__table.setShowGrid(False)
        self.__table.verticalHeader().hide()

        self.__table.setColumnWidth(0, 40)

        self.__table.setHorizontalHeaderLabels(["Color", "Name", "Size (h x w)", "Stats", "Description"])
        layout.addWidget(self.__table)
        self.setLayout(layout)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__table.setRowCount(self.__rows + 1)

        name_item = QTableWidgetItem(region.name())

        color_item = QTableWidgetItem()
        color_item.setBackground(QBrush(color))
        color_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        color_item.setCheckState(Qt.Checked)

        stats_item = QTableWidgetItem("stats")

        size_item = QTableWidgetItem(
            str(region.image_height()) + " x " + str(region.image_width()))

        image_name_item = QTableWidgetItem(region.image_name())

        self.__table.setItem(self.__rows, 0, color_item)
        self.__table.setItem(self.__rows, 1, name_item)
        self.__table.setItem(self.__rows, 2, size_item)
        self.__table.setItem(self.__rows, 3, stats_item)
        self.__table.setItem(self.__rows, 4, image_name_item)

        if self.__rows == 0:
            self.__table.resizeColumnsToContents()
            length = self.__table.horizontalHeader().length()
            RegionOfInterestControl.__LOG.debug("Header length: {0}", length)
            self.setMinimumWidth(length + QApplication.style().pixelMetric(QStyle.PM_DefaultFrameWidth) * 2)
            self.__table.horizontalHeader().setStretchLastSection(True)

        self.__rows += 1

    # TODO for testing only, remove if not used otherwise
    def resizeEvent(self, event:QResizeEvent):
        RegionOfInterestControl.__LOG.debug("Resize to {0}", event.size())


class RegionOfInterestDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("RegionOfInterestDisplayWindow")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__roi_control = RegionOfInterestControl()
        self.setCentralWidget(self.__roi_control)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__roi_control.add_item(region, color)

    # TODO for testing only, remove if not used otherwise
    def resizeEvent(self, event:QResizeEvent):
        RegionOfInterestDisplayWindow.__LOG.debug("Resize to {0}", event.size())
