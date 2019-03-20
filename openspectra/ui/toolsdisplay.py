#  Developed by Joseph M. Conti and Joseph W. Boardman on 3/17/19 2:30 PM.
#  Last modified 3/17/19 2:30 PM
#  Copyright (c) 2019. All rights reserved.
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QColor, QPaintEvent, QPainter, QPalette, QPolygon, QBrush
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLineEdit, QLabel, QScrollArea, QVBoxLayout, \
    QTableWidget, QTableWidgetItem

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

        self.__rows = 0
        self.__table = QTableWidget(self.__rows, 3, self)
        self.__table.setColumnWidth(0, 40)
        self.__table.setColumnWidth(1, 175)
        self.__table.setColumnWidth(2, 100)

        self.__table.setHorizontalHeaderLabels(["Color", "Name", "Size (h x w) "])
        layout.addWidget(self.__table)
        self.setLayout(layout)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__table.setRowCount(self.__rows + 1)

        name_item = QTableWidgetItem(region.name())

        color_item = QTableWidgetItem()
        color_item.setBackground(QBrush(color))
        color_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        color_item.setCheckState(Qt.Checked)

        size_item = QTableWidgetItem(
            str(region.image_height()) + " x " + str(region.image_width()))

        self.__table.setItem(self.__rows, 0, color_item)
        self.__table.setItem(self.__rows, 1, name_item)
        self.__table.setItem(self.__rows, 2, size_item)
        self.__rows += 1


class RegionOfInterestDisplayWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__roi_control = RegionOfInterestControl()
        self.setCentralWidget(self.__roi_control)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__roi_control.add_item(region, color)
