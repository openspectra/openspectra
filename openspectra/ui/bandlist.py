from PyQt5.QtCore import pyqtSignal, pyqtSlot, QItemSelectionModel, QObject, QModelIndex
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAbstractItemView, QTreeWidget, QTreeWidgetItem, QRadioButton, \
    QHBoxLayout, QPushButton
from openspectra.openspectra_file import OpenSpectraFile


class RGBSelectedBands(QObject):

    def __init__(self, red: QModelIndex, green: QModelIndex, blue: QModelIndex):
        super().__init__()
        if not (red.parent().row() == green.parent().row() == blue.parent().row()):
            raise ValueError("Bands are not all from the same file")

        self.__red = red
        self.__green = green
        self.__blue = blue
        self.__label = "R: " + self.__red.data().strip() + \
                       ", G: " + self.__green.data().strip() + \
                       ", B: " + self.__blue.data().strip()

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

    def label(self):
        return self.__label


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

    def __del__(self):
        # TODO???
        pass

    def add_file(self, open_spectra_file:OpenSpectraFile) -> QTreeWidgetItem:
        header = open_spectra_file.header()
        band_labels = header.band_labels()

        # TODO need to manage multiple parent items, 1 per file
        parent_item = QTreeWidgetItem()
        parent_item.setText(0, open_spectra_file.name())
        for index, val in enumerate(band_labels):
            child = QTreeWidgetItem(parent_item)
            child.setText(0, str(val[0] + " - " + val[1]))

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
            parent_item = item.parent()
            # if it has no parent it's a file, ignore it
            if parent_item is not None:
                self.bandSelected.emit(item)

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
                    selected = RGBSelectedBands(indexes[0], indexes[1], indexes[2])
                    self.rgbSelected.emit(selected)
                except:
                    # TODO report or log somehow??
                    pass