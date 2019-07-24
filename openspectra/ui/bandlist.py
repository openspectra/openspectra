#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
import sys

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QItemSelectionModel, QObject, QModelIndex, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAbstractItemView, QTreeWidget, QTreeWidgetItem, QRadioButton, \
    QHBoxLayout, QPushButton, QMessageBox, QCheckBox

from openspectra.openspecrtra_tools import OpenSpectraBandTools
from openspectra.image import BandDescriptor
from openspectra.utils import Logger, LogHelper


class RGBSelectedBands(QObject):

    def __init__(self, red: QModelIndex, green: QModelIndex, blue: QModelIndex):
        super().__init__()
        if not (red.parent().row() == green.parent().row() == blue.parent().row()):
            raise ValueError("Bands are not all from the same file")

        self.__red = red
        self.__green = green
        self.__blue = blue

    def file_name(self) -> str:
        return self.__red.parent().data()

    def parent_index(self) -> int:
        return self.__red.parent().row()

    def red_index(self) -> int:
        return self.__red.row()

    def green_index(self) -> int:
        return self.__green.row()

    def blue_index(self) -> int:
        return self.__blue.row()

    def red_descriptor(self) -> BandDescriptor:
        return self.__red.data(Qt.UserRole)

    def green_descriptor(self) -> BandDescriptor:
        return self.__green.data(Qt.UserRole)

    def blue_descriptor(self) -> BandDescriptor:
        return self.__blue.data(Qt.UserRole)


class TypeSelector(QWidget):

    greyscale_selected = pyqtSignal()
    rgb_selected = pyqtSignal()
    open_clicked = pyqtSignal()

    def __init__(self, parent:QWidget):
        super().__init__(parent)

        self.__open_button = QPushButton("Open", self)
        self.__open_button.clicked.connect(self.__handle_open_clicked)

        h_layout = QHBoxLayout()

        self.__radio_button_group = QWidget(self)
        self.__grey_button = QRadioButton("Greyscale", self.__radio_button_group)
        self.__rgb_button = QRadioButton("RGB", self.__radio_button_group)
        self.__grey_button.setChecked(True)
        self.__grey_button.toggled.connect(self.__handle_greyscale_toggle)
        self.__rgb_button.toggled.connect(self.__handle_rgb_toggle)

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.__grey_button)
        v_layout.addWidget(self.__rgb_button)
        self.__radio_button_group.setLayout(v_layout)

        h_layout.addWidget(self.__radio_button_group)
        h_layout.addWidget(self.__open_button)

        self.setLayout(h_layout)

    def is_greyscale_selected(self) -> bool:
        return self.__grey_button.isChecked()

    def is_rgb_selected(self) -> bool:
        return self.__rgb_button.isChecked()

    def open_enabled(self, value:bool):
        self.__open_button.setDisabled(not value)

    @pyqtSlot()
    def __handle_open_clicked(self):
        self.open_clicked.emit()

    @pyqtSlot(bool)
    def __handle_greyscale_toggle(self, checked:bool):
        if checked:
            self.__open_button.setDisabled(False)
            self.greyscale_selected.emit()

    @pyqtSlot(bool)
    def __handle_rgb_toggle(self, checked:bool):
        if checked:
            self.__open_button.setDisabled(True)
            self.rgb_selected.emit()


class BandList(QWidget):

    __LOG:Logger = LogHelper.logger("RegionOfInterestManager")

    bandSelected = pyqtSignal(QTreeWidgetItem)
    rgbSelected = pyqtSignal(RGBSelectedBands)

    def __init__(self, parent:QWidget):
        super().__init__(parent)
        self.title = 'Bands'
        self.left = 0
        self.top = 0
        self.width = 260
        self.height = 675
        self.__init_ui()
        self.__parent_items = list()
        self.__show_bad_bands_prompt:bool = True

    def __init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.__type_selector = TypeSelector(self)
        self.__type_selector.greyscale_selected.connect(
            self.__handle_greyscale_selected)
        self.__type_selector.rgb_selected.connect(self.__handle_rgb_selected)
        self.__type_selector.open_clicked.connect(self.__handle_open_clicked)

        self.__treeWidget = QTreeWidget(self)
        self.__treeWidget.setColumnCount(1)
        self.__treeWidget.setHeaderLabel("File / Bands")
        self.__treeWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__treeWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__treeWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.__treeWidget.move(0, 0)

        # table item selection
        self.__treeWidget.itemDoubleClicked.connect(self.__on_double_click)
        self.__treeWidget.itemClicked.connect(self.__on_click)

        # Add box layout, add table to box layout and add box layout to widget
        self.__layout = QVBoxLayout()
        self.__layout.addWidget(self.__type_selector)
        self.__layout.addWidget(self.__treeWidget)
        self.setLayout(self.__layout)

        # Show widget
        self.show()

    def add_file(self, file_name:str, band_count:int, band_tools:OpenSpectraBandTools):
        parent_item = QTreeWidgetItem()
        parent_item.setText(0, file_name)

        for band_index in range(band_count):
            child = QTreeWidgetItem(parent_item)
            band_descriptor = band_tools.band_descriptor(band_index)
            if band_descriptor.is_bad_band():
                child.setToolTip(0, "Bad band")
                child.setForeground(0, Qt.red)

            child.setText(0, band_descriptor.band_label())
            child.setData(0, Qt.UserRole, band_descriptor)

        self.__treeWidget.addTopLevelItem(parent_item)
        parent_item.setExpanded(True)
        self.__parent_items.append(parent_item)
        return parent_item

    @pyqtSlot()
    def __handle_greyscale_selected(self):
        self.__treeWidget.selectionModel().clearSelection()
        self.__treeWidget.setSelectionMode(QAbstractItemView.SingleSelection)

    @pyqtSlot()
    def __handle_rgb_selected(self):
        self.__treeWidget.setSelectionMode(QAbstractItemView.MultiSelection)

    @pyqtSlot(QTreeWidgetItem)
    def __on_double_click(self, item:QTreeWidgetItem):
        if self.__type_selector.is_greyscale_selected():
            self.__open_item(item)

    @pyqtSlot(QTreeWidgetItem)
    def __on_click(self, item:QTreeWidgetItem):
        if self.__type_selector.is_rgb_selected():
            indexes = self.__treeWidget.selectionModel().selectedIndexes()
            if len(indexes) > 3:
                self.__treeWidget.selectionModel().select(indexes[0],
                    QItemSelectionModel.Deselect)

            if len(indexes) >= 3:
                self.__type_selector.open_enabled(True)
            else:
                self.__type_selector.open_enabled(False)

    def __handle_open_clicked(self):
        if self.__type_selector.is_rgb_selected():
            indexes = self.__treeWidget.selectionModel().selectedIndexes()
            if len(indexes) == 3:
                try:
                    result:int = QMessageBox.Yes
                    for index in range(3):
                        descriptor:BandDescriptor = indexes[index].data(Qt.UserRole)
                        if self.__show_bad_bands_prompt and descriptor.is_bad_band():
                            result = self.__bad_band_prompt(descriptor)
                            if result == QMessageBox.Cancel:
                                break

                    if result == QMessageBox.Yes:
                        selected = RGBSelectedBands(indexes[0], indexes[1], indexes[2])
                        self.rgbSelected.emit(selected)
                # TODO why is this here??
                except:
                    BandList.__LOG.error("Error: {0}".format(sys.exc_info()[0]))

        if self.__type_selector.is_greyscale_selected():
            item:QTreeWidgetItem = self.__treeWidget.selectedItems()[0]
            self.__open_item(item)

    def __open_item(self, item:QTreeWidgetItem):
        parent_item = item.parent()
        # if it has no parent it's a file, ignore it
        if parent_item is not None:
            result: int = QMessageBox.Yes
            descriptor: BandDescriptor = item.data(0, Qt.UserRole)
            if self.__show_bad_bands_prompt and descriptor.is_bad_band():
                result = self.__bad_band_prompt(descriptor)

            if result == QMessageBox.Yes:
                self.bandSelected.emit(item)

    def __bad_band_prompt(self, descriptor:BandDescriptor) -> int:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setText(
            "Band '{0}' from file '{1}' is marked as a 'bad band' in it's header file.  Do you wish to continue?".
            format(descriptor.band_name(), descriptor.file_name()))
        check_box = QCheckBox("Don't ask again", dialog)
        check_box.setCheckState(not self.__show_bad_bands_prompt)
        dialog.setCheckBox(check_box)
        dialog.addButton(QMessageBox.Cancel)
        dialog.addButton(QMessageBox.Yes)
        result = dialog.exec()
        self.__show_bad_bands_prompt = not dialog.checkBox().checkState() == Qt.Checked
        return result
