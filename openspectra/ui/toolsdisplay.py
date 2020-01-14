#  Developed by Joseph M. Conti and Joseph W. Boardman on 3/17/19 2:30 PM.
#  Last modified 3/17/19 2:30 PM
#  Copyright (c) 2019. All rights reserved.
from itertools import chain
from typing import Dict, List, Tuple, Union

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPoint, pyqtSlot, QRegExp
from PyQt5.QtGui import QColor, QBrush, QCloseEvent, QFont, QResizeEvent, QRegExpValidator, QValidator
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, \
    QTableWidget, QTableWidgetItem, QApplication, QStyle, QMenu, QAction, QHBoxLayout, QLabel, QComboBox, QFormLayout, \
    QLineEdit, QPushButton, QMessageBox, QSlider

from openspectra.openspecrtra_tools import RegionOfInterest, CubeParams
from openspectra.openspectra_file import OpenSpectraHeader
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

    def __init__(self, region:RegionOfInterest):
        super().__init__(region)


class RegionCloseEvent(RegionEvent):

    def __init__(self, region:RegionOfInterest, row:int):
        super().__init__(region)
        self.__row = row

    def row(self) -> int:
        return self.__row


class RegionNameChangeEvent(RegionEvent):

    def __init__(self, region:RegionOfInterest):
        super().__init__(region)


class RegionSaveEvent(RegionEvent):

    def __init__(self, region:RegionOfInterest, include_bands:bool=False):
        super().__init__(region)
        self.__include_bands = include_bands

    def include_bands(self) -> bool:
        return self.__include_bands


class RegionOfInterestControl(QWidget):

    __LOG:Logger = LogHelper.logger("RegionOfInterestControl")

    stats_clicked = pyqtSignal(RegionStatsEvent)
    region_toggled = pyqtSignal(RegionToggleEvent)
    region_name_changed = pyqtSignal(RegionNameChangeEvent)
    region_saved = pyqtSignal(RegionSaveEvent)
    region_closed = pyqtSignal(RegionCloseEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__regions = list()
        self.__selected_row = None

        layout = QVBoxLayout()

        self.__margins = 5
        layout.setContentsMargins(self.__margins, self.__margins, self.__margins, self.__margins)

        self.__rows = 0
        self.__table = QTableWidget(self.__rows, 4, self)
        self.__table.setShowGrid(False)
        self.__table.verticalHeader().hide()
        self.__table.cellClicked.connect(self.__handle_cell_clicked)
        self.__table.cellChanged.connect(self.__handle_cell_changed)

        self.__table.setColumnWidth(0, 40)

        self.__table.setHorizontalHeaderLabels(["Color", "Name", "Size (h x w)", "Description"])
        layout.addWidget(self.__table)
        self.setLayout(layout)

        self.__init_menu()

    def __init_menu(self):
        self.__menu:QMenu = QMenu(self)
        toggle_action = QAction("Toggle", self)
        toggle_action.triggered.connect(self.__handle_region_toggle)
        self.__menu.addAction(toggle_action)

        stats_action = QAction("Band stats", self)
        stats_action.triggered.connect(self.__handle_band_stats)
        self.__menu.addAction(stats_action)

        self.__menu.addSeparator()

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.__handle_region_save)
        self.__menu.addAction(save_action)

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.__handle_region_close)
        self.__menu.addAction(close_action)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__table.cellClicked.disconnect(self.__handle_cell_clicked)
        self.__table.cellChanged.disconnect(self.__handle_cell_changed)
        self.__table.setRowCount(self.__rows + 1)

        name_item = QTableWidgetItem(region.display_name())

        color_item = QTableWidgetItem("...")
        font = QFont()
        font.setBold(True)
        color_item.setFont(font)
        color_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        color_item.setBackground(QBrush(color))
        color_item.setFlags(Qt.ItemIsEnabled)

        size_item = QTableWidgetItem(
            str(region.image_height()) + " x " + str(region.image_width()))
        size_item.setTextAlignment(Qt.AlignVCenter)
        size_item.setFlags(Qt.ItemIsEnabled)

        description_item = QTableWidgetItem(region.description())
        description_item.setFlags(Qt.ItemIsEnabled)

        self.__table.setItem(self.__rows, 0, color_item)
        self.__table.setItem(self.__rows, 1, name_item)
        self.__table.setItem(self.__rows, 2, size_item)
        self.__table.setItem(self.__rows, 3, description_item)

        if self.__rows == 0:
            self.__table.horizontalHeader().setStretchLastSection(True)

        self.__adjust_width()

        self.__regions.append(region)
        self.__rows += 1
        self.__table.cellClicked.connect(self.__handle_cell_clicked)
        self.__table.cellChanged.connect(self.__handle_cell_changed)

    def remove_all(self):
        self.__table.clearContents()
        self.__regions.clear()
        self.__rows = 0

    def remove_item(self, region:RegionOfInterest):
        RegionOfInterestControl.__LOG.debug("remove_item called for region: {}", region)
        try:
            index = self.__regions.index(region)
            self.__remove_item_at(index)
        except ValueError:
            RegionOfInterestControl.__LOG.error("Tried to remove RegionOfInterest item not in list")

    def remove(self, event:RegionCloseEvent):
        row = event.row()
        region = self.__regions[row]
        if region is not None:
            self.__remove_item_at(row)

    def __remove_item_at(self, index:int):
        self.__table.removeRow(index)
        del self.__regions[index]
        self.__rows -= 1
        self.__selected_row = None

    def __adjust_width(self):
        self.__table.resizeColumnsToContents()
        length = self.__table.horizontalHeader().length()
        RegionOfInterestControl.__LOG.debug("Header length: {0}", length)
        self.setMinimumWidth(length + self.__margins * 2 +
                             QApplication.style().pixelMetric(QStyle.PM_DefaultFrameWidth) * 2)

    @pyqtSlot(int, int)
    def __handle_cell_clicked(self, row:int, column:int):
        position = self.mapToGlobal(QPoint(self.__table.columnViewportPosition(column), self.__table.rowViewportPosition(row)))
        RegionOfInterestControl.__LOG.debug("Cell clicked row: {0}, column: {1}, y pos: {2}",
            row, column, position)
        if column == 0 and -1 < row < len(self.__regions):
            self.__selected_row = row
            RegionOfInterestControl.__LOG.debug("Found region: {0}", self.__regions[row].display_name())
            self.__menu.popup(position)

    @pyqtSlot(int, int)
    def __handle_cell_changed(self, row:int, column:int):
        RegionOfInterestControl.__LOG.debug("Cell changed row: {0}, column: {1}", row, column)
        if column == 1:
            item = self.__table.item(row, column)
            RegionOfInterestControl.__LOG.debug("Cell changed, new value: {0}", item.text())
            region:RegionOfInterest = self.__regions[row]
            region.set_display_name(item.text())
            self.region_name_changed.emit(RegionNameChangeEvent(region))
            self.__adjust_width()

    @pyqtSlot()
    def __handle_region_toggle(self):
        region = self.__regions[self.__selected_row]
        RegionOfInterestControl.__LOG.debug("Toogle region: {0}", region.display_name())
        self.region_toggled.emit(RegionToggleEvent(region))
        self.__selected_row = None

    @pyqtSlot()
    def __handle_region_save(self):
        region = self.__regions[self.__selected_row]
        RegionOfInterestControl.__LOG.debug("Save region: {0}", region.display_name())
        self.region_saved.emit(RegionSaveEvent(region))
        self.__selected_row = None

    @pyqtSlot()
    def __handle_region_close(self):
        region = self.__regions[self.__selected_row]
        RegionOfInterestControl.__LOG.debug("Close region: {0}", region.display_name())
        self.region_closed.emit(RegionCloseEvent(region, self.__selected_row))

    @pyqtSlot()
    def __handle_band_stats(self):
        region = self.__regions[self.__selected_row]
        RegionOfInterestControl.__LOG.debug("Band stats region: {0}", region.display_name())
        self.stats_clicked.emit(RegionStatsEvent(region))
        self.__selected_row = None


class RegionOfInterestDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("RegionOfInterestDisplayWindow")

    stats_clicked = pyqtSignal(RegionStatsEvent)
    region_toggled = pyqtSignal(RegionToggleEvent)
    region_name_changed = pyqtSignal(RegionNameChangeEvent)
    region_saved = pyqtSignal(RegionSaveEvent)
    region_closed =  pyqtSignal(RegionCloseEvent)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Region of Interest")
        self.__region_control = RegionOfInterestControl()
        self.setCentralWidget(self.__region_control)
        self.__region_control.stats_clicked.connect(self.stats_clicked)
        self.__region_control.region_toggled.connect(self.region_toggled)
        self.__region_control.region_name_changed.connect(self.region_name_changed)
        self.__region_control.region_saved.connect(self.region_saved)
        self.__region_control.region_closed.connect(self.region_closed)

    def add_item(self, region:RegionOfInterest, color:QColor):
        self.__region_control.add_item(region, color)

    def remove_all(self):
        self.__region_control.remove_all()

    def remove_item(self, region:RegionOfInterest):
        self.__region_control.remove_item(region)

    def remove(self, event:RegionCloseEvent):
        self.__region_control.remove(event)

    def closeEvent(self, event:QCloseEvent):
        self.closed.emit()
        # accepting hides the window
        event.accept()


class RangeSelector(QWidget):

    __LOG:Logger = LogHelper.logger("RangeSelector")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__init_ui__()

    def __init_ui__(self):
        layout = QHBoxLayout()

        from_layout = QVBoxLayout()
        from_layout.addWidget(QLabel("From:"))

        self.__from_select = QComboBox(self)
        # gets ignored for certain styles, like Mac, when not editable
        # possibly allow editable but make it jump to item instead of adding to list?
        self.__from_select.setMaxVisibleItems(20)
        self.__from_select.currentIndexChanged.connect(self.__handle_from_changed)

        from_layout.addWidget(self.__from_select)
        layout.addLayout(from_layout)

        to_layout = QVBoxLayout()
        to_layout.addWidget(QLabel("To:"))

        self.__to_select = QComboBox(self)
        # gets ignored for certain styles, like Mac, when not editable
        # possibly allow editable but make it jump to item instead of adding to list?
        self.__to_select.setMaxVisibleItems(20)
        self.__to_select.currentIndexChanged.connect(self.__handle_to_changed)

        to_layout.addWidget(self.__to_select)
        layout.addLayout(to_layout)

        self.setLayout(layout)

    @pyqtSlot(int)
    def __handle_from_changed(self, index:int):
        RangeSelector.__LOG.debug("from index changed to: {0}".format(index))
        if self.__to_select.currentIndex() < index:
            self.__to_select.setCurrentIndex(index)

    @pyqtSlot(int)
    def __handle_to_changed(self, index:int):
        RangeSelector.__LOG.debug("to index changed to: {0}".format(index))
        if self.__from_select.currentIndex() > index:
            self.__from_select.setCurrentIndex(index)

    def clear(self):
        self.__from_select.clear()
        self.__to_select.clear()

    def from_value(self) -> int:
        return int(self.__from_select.currentText())

    def to_value(self) -> int:
        return int(self.__to_select.currentText())

    def set_range(self, start:int, end:int):
        if end <= start:
            raise ValueError("end value must be greater than start")

        self.__from_select.currentIndexChanged.disconnect(self.__handle_from_changed)
        self.__to_select.currentIndexChanged.disconnect(self.__handle_to_changed)

        index = 0
        for item in range(start, end):
            self.__from_select.insertItem(index, str(item))
            self.__to_select.insertItem(index, str(item + 1))
            index += 1

        self.__from_select.setCurrentIndex(0)
        self.__to_select.setCurrentIndex(end - 2)

        self.__from_select.currentIndexChanged.connect(self.__handle_from_changed)
        self.__to_select.currentIndexChanged.connect(self.__handle_to_changed)


class FileSubCubeParams:

    def __init__(self, name:str, lines:int, samples:int, bands:int, interleave:str):
        self.__name = name
        self.__lines = lines
        self.__samples = samples
        self.__bands = bands
        self.__interleave = interleave

    def name(self) -> str:
        return self.__name

    def lines(self) -> int:
        return self.__lines

    def samples(self) -> int:
        return self.__samples

    def bands(self) -> int:
        return self.__bands

    def file_format(self) -> str:
        return self.__interleave


class SaveSubCubeEvent(QObject):

    def __init__(self, source_file_name:str, new_cude_params:CubeParams):
        super().__init__(None)
        self.__source_file_name = source_file_name
        self.__new_cude_params = new_cude_params

    def source_file_name(self) -> str:
        return self.__source_file_name

    def cube_params(self) -> CubeParams:
        return self.__new_cude_params


class SubCubeControl(QWidget):

    __LOG:Logger = LogHelper.logger("SubCubeControl")

    cancel = pyqtSignal()
    save = pyqtSignal(SaveSubCubeEvent)

    def __init__(self, files:Dict[str, FileSubCubeParams], parent=None):
        super().__init__(parent)
        self.__files = files
        num_files = len(self.__files)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.__file_list = QComboBox(self)

        if num_files > 1:
            self.__file_list.insertItem(0, "Select origin file...")
            self.__file_list.insertItems(1, self.__files.keys())
        else:
            self.__file_list.insertItems(0, self.__files.keys())

        self.__file_list.currentIndexChanged.connect(self.__handle_file_select)
        form_layout.addRow("Original File:", self.__file_list)

        self.__file_type = QComboBox(self)
        self.__format_map = {OpenSpectraHeader.BIL_INTERLEAVE : "BIL - Band Interleaved by Line",
                             OpenSpectraHeader.BSQ_INTERLEAVE : "BSQ - Band Sequential",
                             OpenSpectraHeader.BIP_INTERLEAVE : "BIP - Band Interleaved by Pixel"}
        self.__file_type.insertItem(0, "")
        self.__file_type.insertItems(1, self.__format_map.values())
        form_layout.addRow("Output File Interleave:", self.__file_type)

        self.__sample_range = RangeSelector(self)
        form_layout.addRow("Sample Range:", self.__sample_range)

        self.__line_range = RangeSelector(self)
        form_layout.addRow("Line Range:", self.__line_range)

        self.__band_select = QLineEdit(self)
        self.__band_select.setMinimumWidth(250)
        self.__band_validator = QRegExpValidator(QRegExp("[1-9][0-9]*((-|,)([1-9][0-9]*))*"))
        self.__band_select.setValidator(self.__band_validator)
        self.__band_select.setToolTip\
                ("Use '-' for a range, ',' to separate ranges and single bands.\nExample: 1-10,12,14,19-21")
        self.__max_band = 0

        form_layout.addRow("Bands:", self.__band_select)
        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.cancel)
        button_layout.addWidget(cancel_button)

        self.__save_button = QPushButton("Save", self)
        self.__save_button.setDisabled(True)
        self.__save_button.clicked.connect(self.__handle_save)
        button_layout.addWidget(self.__save_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.__handle_file_select(0)

    @pyqtSlot(int)
    def __handle_file_select(self, index:int):
        if index == 0 and len(self.__files) > 1:
            self.__save_button.setDisabled(True)
            self.__line_range.clear()
            self.__sample_range.clear()
            self.__max_band = 0
            self.__band_select.clear()
            self.__file_type.setCurrentIndex(0)
        else:
            selected_file_name = self.__file_list.currentText()
            params:FileSubCubeParams = self.__files[selected_file_name]
            self.__line_range.set_range(1, params.lines())
            self.__sample_range.set_range(1, params.samples())
            self.__max_band = params.bands()
            self.__band_select.setText("1-" + str(self.__max_band))
            self.__file_type.setCurrentText(self.__format_map[params.file_format()])
            self.__save_button.setDisabled(False)

    @pyqtSlot()
    def __handle_save(self):
        source_file_name = self.__file_list.currentText()
        file_type = self.__file_type.currentText()[0:3].lower()

        # Convert to zero based indexing using slice range rules
        lines = self.__line_range.from_value() - 1, self.__line_range.to_value()
        samples = self.__sample_range.from_value() - 1, self.__sample_range.to_value()
        bands_str = self.__band_select.text()

        SubCubeControl.__LOG.debug(
            "save button clicked, source file: {0}, type: {1}, lines: {2}, samples: {3}, bands: {4}".
                format(source_file_name, file_type, lines, samples, bands_str))

        # validate bands args and build the parameter
        bands = self.__get_band_list(bands_str)
        SubCubeControl.__LOG.debug("get_band_list returned: {0}".format(bands))
        if bands is not None:
            cube_params = CubeParams(file_type, lines, samples, bands)
            self.save.emit(SaveSubCubeEvent(source_file_name, cube_params))

    def __get_band_list(self, bands:str) -> Union[Tuple[int, int], List[int]]:
        bands_str = bands
        validate_result = self.__band_validator.validate(bands_str, 0)
        if validate_result[0] == QValidator.Invalid:
            self.__show_error("Cannot validate band list argument of {0}".format(self.__band_select.text()))
            return None

        elif validate_result[0] == QValidator.Intermediate:
            if str.endswith(bands_str, (",", "-")):
                bands_str = bands_str[:len(bands_str) - 1]
                SubCubeControl.__LOG.debug("attempted to fix band str and got: {0}".format(bands_str))

                validate_result = self.__band_validator.validate(bands_str, 0)
                if validate_result[0] != QValidator.Acceptable:
                    self.__show_error("Cannot validate band list argument of {0}".format(self.__band_select.text()))
                    return None

        # collect up the ranges and single bands
        ranges:List[Tuple[int, int]] = list()
        single_bands:List[int] = list()

        # this should produce a list of ranges, 1-5, and individual values
        # we also convert indexes from 1 based to 0 here
        # thanks to the validator we should not be getting 0 or negative values so no need to check
        # validate against self.__max_bands
        band_range_strs = str.split(bands_str, ",")
        for band_range in band_range_strs:
            range_parts = str.split(band_range, "-")
            if len(range_parts) == 2:
                # make sure tuple ranges have the lesser value first
                # it will make things a bit more simple below
                r1 = int(range_parts[0]) - 1
                r2 = int(range_parts[1])

                if r1 > self.__max_band:
                    self.__show_error("Band range value cannot exceed {0}, received range with one end {1}".
                        format(self.__max_band, range_parts[0]))

                if r2 > self.__max_band:
                    self.__show_error("Band range value cannot exceed {0}, received range with one end {1}".
                        format(self.__max_band, range_parts[1]))

                if r1 < r2:
                    ranges.append((r1, r2))
                elif r2 < r1:
                    ranges.append((r2, r1))
                else:
                    # they were equal
                    single_bands.append(r1)

            elif len(range_parts) == 1:
                b = int(range_parts[0])
                if b >= self.__max_band:
                    self.__show_error("Band value cannot exceed {0}, received single band index of {1}".
                        format(self.__max_band, range_parts[0]))
                single_bands.append(b)
            else:
                self.__show_error("Cannot validate band list argument of {0}".format(self.__band_select.text()))
                return None

        # check to see if we just have a single range or band
        range_cnt = len(ranges)
        singles_cnt = len(single_bands)
        if range_cnt == 1 and singles_cnt == 0:
            return ranges[0]

        if range_cnt == 0 and singles_cnt == 1:
            return single_bands

        # otherwise consolidate the lists to a minimum set of ranges and single bands
        # reducing it to a tuple if possible
        # first generate a list of containing all the ranges
        range_list_list = [list(range(r[0], r[1])) for r in ranges]
        # SubCubeControl.__LOG.debug("range_list_list: {0}".format(range_list_list))

        band_list = list(chain.from_iterable(range_list_list))
        # SubCubeControl.__LOG.debug("band_list: {0}".format(band_list))

        band_list.extend(single_bands)
        # SubCubeControl.__LOG.debug("full band_list: {0}".format(band_list))

        # now we have all the bands specified by both ranges and single bands
        # so now create a set from the list to eliminate duplicates
        band_set = set(band_list)
        sorted_band_list = sorted(band_set)
        # SubCubeControl.__LOG.debug("sorted band_set: {0}".format(sorted_band_list))

        # now see if it's contiguous and can be returned as a tuple
        is_contiguous = True
        last_index = -1
        for band_index in sorted_band_list:
            if last_index == -1:
                last_index = band_index
            elif band_index != last_index + 1:
                is_contiguous = False
                break
            else:
                last_index = band_index

        if is_contiguous:
            # then return the bounds as a tuple
            return sorted_band_list[0], sorted_band_list[len(sorted_band_list) - 1]
        else:
            return sorted_band_list

    def __show_error(self, message:str):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setText(message)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec()


class SubCubeWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("SubCubeWindow")

    save = pyqtSignal(SaveSubCubeEvent)

    def __init__(self, files:Dict[str, FileSubCubeParams], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Sub-Cube")

        subcube_control = SubCubeControl(files, self)
        subcube_control.cancel.connect(self.__handle_cancel)
        subcube_control.save.connect(self.save)
        self.setCentralWidget(subcube_control)

        self.setMinimumWidth(500)
        self.setMinimumHeight(325)

        self.setMaximumWidth(500)
        self.setMaximumHeight(325)


    @pyqtSlot()
    def __handle_cancel(self):
        SubCubeWindow.__LOG.debug("cancel button clicked")
        self.close()

    def resizeEvent(self, event:QResizeEvent):
        SubCubeWindow.__LOG.debug("new size: {0}".format(event.size()))


class ZoomSetControl(QWidget):
    __LOG:Logger = LogHelper.logger("ZoomSetControl")

    zoom_factor_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__default_zoom_factor = 1.5
        self.__precision = 1
        self.__display_format = "{{:.{}f}}".format(self.__precision)

        layout = QVBoxLayout()
        self.__label = QLabel("Zoom Factor")
        layout.addWidget(self.__label)

        adjuster_layout = QHBoxLayout()

        self.__value_display = QLineEdit(self)
        self.__value_display.setFixedWidth(35)
        self.__value_display.setEnabled(False)
        self.__value_display.setText(self.__display_format.format(self.__default_zoom_factor))

        self.__slider = QSlider(self)
        self.__slider.setMinimum(11)
        self.__slider.setMaximum(50)
        self.__slider.setTickInterval(2)
        self.__slider.setTickPosition(QSlider.TicksBothSides)
        self.__slider.setValue(self.__default_zoom_factor * 10)
        self.__slider.valueChanged.connect(self.__handle_slider_value_change)

        adjuster_layout.addWidget(self.__value_display)
        adjuster_layout.addWidget(self.__slider)

        layout.addLayout(adjuster_layout)
        self.setLayout(layout)

    @pyqtSlot(int)
    def __handle_slider_value_change(self, value:int):
        new_value = value / 10
        self.__value_display.setText(self.__display_format.format(new_value))
        self.zoom_factor_changed.emit(new_value)

    def zoom_factor(self) -> float:
        return float(self.__value_display.text())


class ZoomSetWindow(QMainWindow):
    __LOG:Logger = LogHelper.logger("ZoomSetWindow")

    zoom_factor_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__zoom_set_control = ZoomSetControl()
        self.__zoom_set_control.zoom_factor_changed.connect(self.zoom_factor_changed)

        self.setMinimumWidth(100)
        self.setMaximumWidth(100)
        self.setMinimumHeight(300)
        self.setMaximumHeight(300)

        self.setToolTip("Change the zoom factor for all zoom windows")
        self.setCentralWidget(self.__zoom_set_control)

    def zoom_factor(self) -> float:
        return self.__zoom_set_control.zoom_factor()