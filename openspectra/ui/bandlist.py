#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
import sys
from typing import List

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QItemSelectionModel, QObject, QModelIndex, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAbstractItemView, QTreeWidget, QTreeWidgetItem, QRadioButton, \
    QHBoxLayout, QPushButton, QMessageBox, QCheckBox, QTreeWidgetItemIterator

from openspectra.openspectra_tools import OpenSpectraBandTools
from openspectra.image import BandDescriptor
from openspectra.utils import Logger, LogHelper


class RGBSelectedBands(QObject):

    def __init__(self, parent_file:QTreeWidgetItem, red:QTreeWidgetItem, green:QTreeWidgetItem, blue:QTreeWidgetItem):
        super().__init__()
        if not(red.parent() == green.parent() == blue.parent() == parent_file):
            ValueError("All bands must have parent_file as their parent")

        self.__parent_file = parent_file
        self.__red = red
        self.__green = green
        self.__blue = blue

    def file_name(self) -> str:
        return self.__parent_file.text(0)

    def red_index(self) -> int:
        return self.__parent_file.indexOfChild(self.__red)

    def green_index(self) -> int:
        return self.__parent_file.indexOfChild(self.__green)

    def blue_index(self) -> int:
        return self.__parent_file.indexOfChild(self.__blue)

    def red_descriptor(self) -> BandDescriptor:
        return self.__red.data(0, Qt.UserRole)

    def green_descriptor(self) -> BandDescriptor:
        return self.__green.data(0, Qt.UserRole)

    def blue_descriptor(self) -> BandDescriptor:
        return self.__blue.data(0, Qt.UserRole)


class TypeSelector(QWidget):

    greyscale_selected = pyqtSignal()
    rgb_selected = pyqtSignal()
    open_clicked = pyqtSignal()

    def __init__(self, parent:QWidget):
        super().__init__(parent)

        self.__open_button = QPushButton("Show Image", self)
        self.__open_button.clicked.connect(self.__handle_open_clicked)
        self.__open_button.setDisabled(True)

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
            self.greyscale_selected.emit()

    @pyqtSlot(bool)
    def __handle_rgb_toggle(self, checked:bool):
        if checked:
            self.__open_button.setDisabled(True)
            self.rgb_selected.emit()


class BandList(QWidget):

    __LOG:Logger = LogHelper.logger("BandList")

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
        self.__treeWidget.itemDoubleClicked.connect(self.__handle_item_double_click)
        self.__treeWidget.itemSelectionChanged.connect(self.__handle_item_selection_changed)

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

        # add the band information for the file
        for band_index in range(band_count):
            child = QTreeWidgetItem(parent_item)
            band_descriptor = band_tools.band_descriptor(band_index)
            if band_descriptor.is_bad_band():
                child.setToolTip(0, "Bad band")
                child.setForeground(0, Qt.red)

            child.setText(0, band_descriptor.band_label())
            child.setData(0, Qt.UserRole, band_descriptor)

        # unselected any selected items from another file
        [item.setSelected(False) for item in self.__treeWidget.selectedItems()]

        # collapse any other file band lists that are expanded
        for index in range(0, self.__treeWidget.topLevelItemCount()):
            self.__treeWidget.topLevelItem(index).setExpanded(False)

        # add the new file with bands and expand the tree
        self.__treeWidget.addTopLevelItem(parent_item)
        parent_item.setExpanded(True)
        self.__parent_items.append(parent_item)
        return parent_item

    def remove_file(self, file_name:str):
        items = self.__treeWidget.findItems(file_name, Qt.MatchExactly)
        if len(items) == 1:
            index = self.__treeWidget.indexOfTopLevelItem(items[0])
            self.__treeWidget.takeTopLevelItem(index)
        else:
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Critical)
            dialog.setText("An internal error occurred, file '{}' doesn't appear to be open".format(file_name))
            dialog.addButton(QMessageBox.Ok)
            dialog.exec()

    def selected_file(self) -> str:
        selected_items:List[QTreeWidgetItem] = self.__treeWidget.selectedItems()
        selected_file:str = None
        if len(selected_items) > 0:
            if selected_items[0].parent() is None:
                selected_file = selected_items[0].text(0)
            else:
                selected_file = selected_items[0].parent().text(0)

        return selected_file

    @pyqtSlot()
    def __handle_greyscale_selected(self):
        selected_items:List[QTreeWidgetItem] = self.__treeWidget.selectedItems()
        for item in selected_items:
            if item.parent() is not None:
                item.setSelected(False)

        self.__treeWidget.setSelectionMode(QAbstractItemView.SingleSelection)

    @pyqtSlot()
    def __handle_rgb_selected(self):
        self.__treeWidget.setSelectionMode(QAbstractItemView.MultiSelection)

    @pyqtSlot(QTreeWidgetItem)
    def __handle_item_double_click(self, item:QTreeWidgetItem):
        if self.__type_selector.is_greyscale_selected() and item.parent() is not None:
            item.setSelected(False)
            self.__open_item(item)

    @pyqtSlot()
    def __handle_item_selection_changed(self):
        selected_items:List[QTreeWidgetItem] = self.__treeWidget.selectedItems()
        BandList.__LOG.debug("start __handle_item_selection_changed, selected size: {}, selected items: {}, state: {}",
            len(selected_items), str(selected_items), self.__treeWidget.state())

        # When clicking or dragging down then list items are appended to the end of the
        # selected_items list so selected_items[len(selected_items) - 1] is last selected
        # However when dragging up the list the order is reversed!
        if self.__type_selector.is_rgb_selected() and len(selected_items) > 0:
            last_selected = selected_items[len(selected_items) - 1]
            if last_selected.parent() is None:
                # A file item was selected
                for selected_item in selected_items:
                    if selected_item != last_selected:
                        selected_item.setSelected(False)
            else:
                # A band item was selected
                for selected_item in selected_items:
                    if selected_item.parent() is None:
                        # if we previously had a file selected, unselect it
                        selected_item.setSelected(False)
                    elif selected_item.parent() != last_selected.parent():
                        # otherwise check to make sure all selected bands are from
                        # the same file
                        selected_item.setSelected(False)

                selected_items = self.__treeWidget.selectedItems()
                if len(selected_items) > 3:
                    BandList.__LOG.debug("unselecting item: {}", selected_items[0])
                    selected_items[0].setSelected(False)

            # Now see what we're left with
            selected_items = self.__treeWidget.selectedItems()
            BandList.__LOG.debug("end __handle_item_selection_changed, selected size: {}, selected items: {}",
                len(selected_items), str(selected_items))
            if len(selected_items) == 3:
                self.__type_selector.open_enabled(True)
            else:
                self.__type_selector.open_enabled(False)
        else:
            # grey scale is selected
            if len(selected_items) == 1 and selected_items[0].parent() is not None:
                self.__type_selector.open_enabled(True)
            else:
                self.__type_selector.open_enabled(False)

    @pyqtSlot()
    def __handle_open_clicked(self):
        items:List[QTreeWidgetItem] = self.__treeWidget.selectedItems()
        if self.__type_selector.is_rgb_selected():
            if len(items) == 3:

                if items[0].parent() is None or items[1].parent() is None or items[2].parent() is None:
                    self.__show_error("Only bands should be selected, not files")
                    return

                if not (items[0].parent() == items[1].parent() == items[2].parent()):
                    self.__show_error("All bands must be from the same file")
                    return

                result:int = QMessageBox.Yes
                for index in range(3):
                    descriptor:BandDescriptor = items[index].data(0, Qt.UserRole)
                    if self.__show_bad_bands_prompt and descriptor.is_bad_band():
                        result = self.__bad_band_prompt(descriptor)
                        if result == QMessageBox.Cancel:
                            break

                if result == QMessageBox.Yes:
                    [item.setSelected(False) for item in items]
                    selected = RGBSelectedBands(items[0].parent(), items[0], items[1], items[2])
                    self.rgbSelected.emit(selected)

        if self.__type_selector.is_greyscale_selected():
            if len(items) == 1:
                item:QTreeWidgetItem = items[0]
                item.setSelected(False)
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
        else:
            self.__show_error("A band must be selected not a file.")

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

    def __show_error(self, message:str):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setText(message)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec()
