#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

from enum import Enum
from typing import Union

import matplotlib.lines as lines
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QPoint
from PyQt5.QtGui import QResizeEvent, QCloseEvent, QDoubleValidator, QFocusEvent, QKeyEvent
from PyQt5.QtWidgets import QSizePolicy, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QFrame, \
    QLineEdit, QPushButton, QStackedLayout, QRadioButton, QAction, QMenu
from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from openspectra.image import Band
from openspectra.openspectra_tools import PlotData, HistogramPlotData, LinePlotData
from openspectra.utils import LogHelper, Logger


class Limit(Enum):
    Lower = 0
    Upper = 1


class LimitResetEvent(QObject):

    def __init__(self):
        super().__init__()


class LimitChangeEvent(QObject):

    def __init__(self, limit:Limit=None, value:Union[int, float]=None,
            lower_limit:Union[int, float]=None, upper_limit:Union[int, float]=None,
            band:Band=None):
        """Expects either limit and value or at least one of lower_limit or upper_limit.
        If limit and value are set lower_limit and upper_limit are ignored."""
        super().__init__()
        self.__band = band
        self.__has_lower:bool = False
        self.__has_upper:bool = False
        self.__lower_limit:Union[int, float] = None
        self.__upper_limit:Union[int, float] = None

        if limit is not None and value is not None:
            if limit == Limit.Lower:
                self.__init_lower(value)

            if limit == Limit.Upper:
                self.__init_upper(value)
        else:
            if lower_limit is not None:
                self.__init_lower(lower_limit)

            if upper_limit is not None:
                self.__init_upper(upper_limit)

    def __init_lower(self, value:Union[int, float]):
        self.__lower_limit = value
        self.__has_lower = True

    def __init_upper(self, value:Union[int, float]):
        self.__upper_limit = value
        self.__has_upper = True

    def has_lower_limit_change(self) -> bool:
        return self.__has_lower

    def has_upper_limit_change(self) -> bool:
        return self.__has_upper

    def lower_limit(self) -> Union[int, float]:
        return self.__lower_limit

    def upper_limit(self) -> Union[int, float]:
        return self.__upper_limit

    def band(self) -> Band:
        return self.__band


class PlotChangeEvent(QObject):

    def __init__(self, lower_limit:Union[int, float], upper_limit:Union[int, float],
            lower_min:Union[int, float], upper_max:Union[int, float]):
        super().__init__()
        self.__lower_limit = lower_limit
        self.__upper_limit = upper_limit
        self.__lower_min = lower_min
        self.__upper_max = upper_max

    def lower_limit(self) -> Union[int, float]:
        return self.__lower_limit

    def upper_limit(self) -> Union[int, float]:
        return self.__upper_limit

    def lower_min(self) -> Union[int, float]:
        return self.__lower_min

    def upper_max(self) -> Union[int, float]:
        return self.__upper_max


class PlotCanvas(FigureCanvas):

    __LOG:Logger = LogHelper.logger("PlotCanvas")

    def __init__(self, parent=None, width=5, height=4, dpi=75):
        self._current_plot = None

        fig = Figure(figsize=(width, height), dpi=dpi)
        self._axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot(self, data:PlotData):
        self._axes.set_xlabel(data.x_label)
        self._axes.set_ylabel(data.y_label)
        self._axes.set_title(data.title)
        self._axes.relim()
        self._axes.autoscale(True)
        self.draw()

    def set_plot_title(self, title:str):
        PlotCanvas.__LOG.debug("new title: {0} ", title)
        self._axes.set_title(title)
        self.draw()


class LinePlotCanvas(PlotCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=75):
        super().__init__(parent, width, height, dpi)

    def plot(self, data:LinePlotData):
        if self._current_plot is not None:
            self._current_plot.remove()

        self._current_plot, = self._axes.plot(data.x_data, data.y_data,
            color=data.color, linestyle=data.line_style, label=data.legend)
        if data.legend is not None:
            self._axes.legend(loc='best')
        super().plot(data)

    def add_plot(self, data:LinePlotData):
        self._axes.plot(data.x_data, data.y_data, color=data.color,
            linestyle=data.line_style, label=data.legend)
        if data.legend is not None:
            self._axes.legend(loc='best')
        self.draw()

    def clear(self):
        self._axes.clear()
        self._current_plot = None


class HistogramPlotCanvas(PlotCanvas):

    def __init__(self, band:Band, parent=None, width=5, height=4, dpi=75):
        super().__init__(parent, width, height, dpi)
        self.__band = band

    def plot(self, data:HistogramPlotData):
        self._axes.hist(data.y_data, data.bins, data.x_data,
            color=data.color, linestyle=data.line_style)
        super().plot(data)

    def update_plot(self, data:HistogramPlotData):
        self._axes.clear()
        self.plot(data)

    def band(self) -> Band:
        return self.__band


class LimitValueLineEdit(QLineEdit):

    __LOG:Logger = LogHelper.logger("LimitValueLineEdit")

    value_changed = pyqtSignal(float)

    def __init__(self, name:str, parent:QWidget=None):
        super().__init__(parent)
        self.__name = name
        self.__set_precision(3)

    def __set_precision(self, precision:int):
        self.__precision = precision
        self.__limit_display_format = "{{:.{}f}}".format(self.__precision)

    def set_value(self, value:Union[int, float]):
        super().setText(self.__limit_display_format.format(value))

    def set_validator(self, lower_limit:Union[int, float], upper_limit:Union[int, float], precision:int):
        super().setValidator(QDoubleValidator(lower_limit, upper_limit, precision))
        self.__set_precision(precision)

    def focusOutEvent(self, event:QFocusEvent):
        # http://doc.qt.io/qt-5/qt.html#FocusReason-enum
        # LimitValueLineEdit.__LOG.debug("{0} edit focus out, reason: {1}",
        #     self.__name, event.reason())
        reason = event.reason()
        if reason == Qt.MouseFocusReason or reason == Qt.TabFocusReason:
            if self.hasAcceptableInput():
                self.value_changed.emit(float(self.text()))
                super().focusOutEvent(event)
            else:
                self.setFocus()

    def keyPressEvent(self, event:QKeyEvent):
        # http://doc.qt.io/qt-5/qt.html#Key-enum
        # LimitValueLineEdit.__LOG.debug("{0} edit key press, key: {1}",
        #     self.__name, event.key())
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Return and self.hasAcceptableInput():
            self.value_changed.emit(float(self.text()))


class AdjustableHistogramPlotCanvas(HistogramPlotCanvas):

    __LOG:Logger = LogHelper.logger("AdjustableHistogramPlotCanvas")

    limit_changed = pyqtSignal(LimitChangeEvent)
    plot_changed = pyqtSignal(PlotChangeEvent)

    def __init__(self, band:Band, parent=None, width=5, height=4, dpi=75):
        super().__init__(band, parent, width, height, dpi)
        self.__lower_limit = None
        self.__upper_limit = None
        self.__min_adjust_x = None
        self.__max_adjust_x = None
        self.__dragging:lines.Line2D = None

    def __on_mouse_release(self, event:MouseEvent):
        if self.__dragging is not None:
            line_id = self.__get_limit_id(self.__dragging)
            if line_id is not None:
                new_loc = self.__dragging.get_xdata()[0]
                limit_event = LimitChangeEvent(line_id, new_loc, band=self.band())
                self.limit_changed.emit(limit_event)
                AdjustableHistogramPlotCanvas.__LOG.debug("New limit loc: {0}", new_loc)

            self.__dragging = None

    def __get_limit_id(self, limit_line:lines.Line2D) -> Limit:
        if limit_line is self.__lower_limit:
            return Limit.Lower
        elif limit_line is self.__upper_limit:
            return Limit.Upper
        else:
            return None

    def __get_limit_from_id(self, limit:Limit) -> lines.Line2D:
        if limit == Limit.Lower:
            return self.__lower_limit
        else:
            return self.__upper_limit

    def __on_pick(self, event:PickEvent):
        if event.artist == self.__lower_limit:
            AdjustableHistogramPlotCanvas.__LOG.debug("picked lower limit at {0}", self.__lower_limit.get_xdata())
        elif event.artist == self.__upper_limit:
            AdjustableHistogramPlotCanvas.__LOG.debug("picked upper limit at {0}", self.__upper_limit.get_xdata())

        self.__dragging = event.artist

    def __on_mouse_move(self, event:MouseEvent):
        if self.__dragging is not None and event.xdata is not None:
            new_x = event.xdata
            if new_x > self.__max_adjust_x:
                new_x = self.__max_adjust_x
            elif new_x < self.__min_adjust_x:
                new_x = self.__min_adjust_x

            self.__dragging.set_xdata([new_x, new_x])
            self.draw()

    def plot(self, data:HistogramPlotData):
        super().plot(data)

        self.mpl_connect("motion_notify_event", self.__on_mouse_move)
        self.mpl_connect("button_release_event", self.__on_mouse_release)

        self.__min_adjust_x = self._axes.get_xlim()[0]
        self.__max_adjust_x = self._axes.get_xlim()[1]
        AdjustableHistogramPlotCanvas.__LOG.debug("min_adjust_x: {0}, max_adjust_x {1}",
            self.__min_adjust_x, self.__max_adjust_x)

        lower_limit = self.__get_line_position(data.lower_limit())
        self.__lower_limit = lines.Line2D([lower_limit, lower_limit],
            [0, self._axes.get_ylim()[1] - 8], transform=self._axes.transData,
            figure=self._axes.figure, picker=5)

        upper_limit = self.__get_line_position(data.upper_limit())
        self.__upper_limit = lines.Line2D([upper_limit, upper_limit],
            [0, self._axes.get_ylim()[1] - 8], transform=self._axes.transData,
            figure=self._axes.figure, picker=5)

        self.figure.lines.extend([self.__lower_limit, self.__upper_limit])
        self.mpl_connect("pick_event", self.__on_pick)

        min_valid = self.__min_adjust_x
        if data.lower_limit() < min_valid:
            min_valid = data.lower_limit()

        max_valid = self.__max_adjust_x
        if data.upper_limit() > max_valid:
            max_valid = data.upper_limit()

        plot_event = PlotChangeEvent(data.lower_limit(), data.upper_limit(), min_valid, max_valid)
        self.plot_changed.emit(plot_event)

    def update_limit_line(self, lower_limit:Union[int, float]=None, upper_limit:Union[int, float]=None):

        updated:bool = False
        if lower_limit is not None:
            lower_limit = self.__get_line_position(lower_limit)
            self.__get_limit_from_id(Limit.Lower).set_xdata([lower_limit, lower_limit])
            updated = True

        if upper_limit is not None:
            upper_limit = self.__get_line_position(upper_limit)
            self.__get_limit_from_id(Limit.Upper).set_xdata([upper_limit, upper_limit])
            updated = True

        if updated:
            self.draw()

    def __get_line_position(self, limit:Union[int, float]):
        result = limit
        if result > self.__max_adjust_x:
            result = self.__max_adjust_x

        if result < self.__min_adjust_x:
            result = self.__min_adjust_x

        return result


class LinePlotDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("LinePlotDisplayWindow")

    closed = pyqtSignal(QMainWindow)

    def __init__(self, parent=None, title:str=None):
        super().__init__(parent)
        if title is not None:
            self.setWindowTitle(title)

        self.__plot_canvas = LinePlotCanvas(self, width=5, height=4)
        self.setCentralWidget(self.__plot_canvas)

    def plot(self, data:LinePlotData):
        self.__plot_canvas.plot(data)

    def add_plot(self, data:LinePlotData):
        self.__plot_canvas.add_plot(data)

    def clear(self):
        self.__plot_canvas.clear()

    def set_plot_title(self, title:str):
        self.__plot_canvas.set_plot_title(title)

    def resizeEvent(self, event:QResizeEvent):
        self.__plot_canvas.resize(event.size())

    def closeEvent(self, event:QCloseEvent):
        self.closed.emit(self)
        # accepting hides the window
        event.accept()


class AdjustableHistogramControl(QWidget):

    __LOG:Logger = LogHelper.logger("AdjustableHistogramControl")

    limit_changed = pyqtSignal(LimitChangeEvent)
    limits_reset = pyqtSignal(LimitResetEvent)

    def __init__(self, band:Band, parent=None):
        super().__init__(parent)
        self.__band = band
        self.__has_adjusted_data = False
        self.__raw_data_canvas = AdjustableHistogramPlotCanvas(band, self, width=5, height=4)
        self.__raw_data_canvas.limit_changed.connect(self.__handle_hist_limit_change)
        self.__raw_data_canvas.plot_changed.connect(self.__handle_plot_change)
        self.__adjusted_data_canvas = HistogramPlotCanvas(band, self, width=5, height=4)

        self.__edit_precision:int = 3

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        control_frame = QFrame(self)
        control_frame.setFrameStyle(QFrame.Panel)
        control_frame.setLineWidth(1)

        control_layout = QHBoxLayout()
        control_layout.setAlignment(Qt.AlignLeft)
        control_layout.setContentsMargins(2, 2, 2, 2)
        control_layout.setSpacing(3)

        low_label = QLabel("low limit:")
        low_label.setFixedWidth(60)
        control_layout.addWidget(low_label)

        self.__lower_edit:LimitValueLineEdit = LimitValueLineEdit("lower limit")
        self.__lower_edit.setMaximumWidth(80)
        self.__lower_edit.deselect()
        self.__lower_edit.setAlignment(Qt.AlignLeft)
        self.__lower_edit.value_changed.connect(self.__handle_lower_limit_edit)
        control_layout.addWidget(self.__lower_edit)
        control_layout.addSpacing(10)

        high_label = QLabel("high limit:")
        high_label.setFixedWidth(60)
        control_layout.addWidget(high_label)

        self.__upper_edit:LimitValueLineEdit = LimitValueLineEdit("upper limit")
        self.__upper_edit.setMaximumWidth(80)
        self.__upper_edit.deselect()
        self.__upper_edit.setAlignment(Qt.AlignLeft)
        self.__upper_edit.value_changed.connect(self.__handle_upper_limit_edit)
        control_layout.addWidget(self.__upper_edit)
        control_layout.addSpacing(10)

        self.__reset_button = QPushButton("Reset")
        self.__reset_button.setFixedWidth(60)
        self.__reset_button.clicked.connect(self.__handle_reset_clicked)
        control_layout.addWidget(self.__reset_button)

        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)

        # plot_frame = QGroupBox(self)
        plot_frame = QFrame(self)
        plot_frame.setFrameStyle(QFrame.Panel)
        plot_frame.setLineWidth(1)

        # plot_frame = QWidget(self)
        plot_layout = QHBoxLayout()
        plot_layout.setContentsMargins(2, 2, 2, 2)
        plot_layout.setSpacing(2)
        plot_layout.addWidget(self.__raw_data_canvas)
        plot_layout.addWidget(self.__adjusted_data_canvas)
        plot_frame.setLayout(plot_layout)
        layout.addWidget(plot_frame)

        self.setLayout(layout)

    def set_raw_data(self, data:HistogramPlotData):
        self.__raw_data_canvas.plot(data)

    def update_limits(self, data:HistogramPlotData):
        self.__lower_edit.set_value(data.lower_limit())
        self.__upper_edit.set_value(data.upper_limit())
        self.__raw_data_canvas.update_limit_line(
            data.lower_limit(), data.upper_limit())

    def set_adjusted_data(self, data:HistogramPlotData):
        if not self.__has_adjusted_data:
            self.__adjusted_data_canvas.plot(data)
            self.__has_adjusted_data = True
        else:
            self.__adjusted_data_canvas.update_plot(data)

    @pyqtSlot()
    def __handle_reset_clicked(self):
        self.limits_reset.emit(LimitResetEvent())

    @pyqtSlot(float)
    def __handle_lower_limit_edit(self, new_value:Union[int, float]):
        AdjustableHistogramControl.__LOG.debug("lower edit limit: {0}",
            new_value)
        # emit limit_changed to bubble up and notify
        self.limit_changed.emit(LimitChangeEvent(
            lower_limit=new_value, band=self.__band))
        # update plot lines
        self.__raw_data_canvas.update_limit_line(lower_limit=new_value)

    @pyqtSlot(float)
    def __handle_upper_limit_edit(self, new_value:Union[int, float]):
        AdjustableHistogramControl.__LOG.debug("upper edit limit: {0}",
            new_value)
        # emit limit_changed to bubble up and notify
        self.limit_changed.emit(LimitChangeEvent(
            upper_limit=new_value, band=self.__band))
        # update plot lines
        self.__raw_data_canvas.update_limit_line(upper_limit=new_value)

    @pyqtSlot(LimitChangeEvent)
    def __handle_hist_limit_change(self, event:LimitChangeEvent):
        AdjustableHistogramControl.__LOG.debug("__handle_hist_limit_change {0}, {1}",
            event.lower_limit(), event.upper_limit())
        self.limit_changed.emit(event)
        if event.has_lower_limit_change():
            self.__lower_edit.set_value(event.lower_limit())

        if event.has_upper_limit_change():
            self.__upper_edit.set_value(event.upper_limit())

    @pyqtSlot(PlotChangeEvent)
    def __handle_plot_change(self, event:PlotChangeEvent):
        AdjustableHistogramControl.__LOG.debug("__handle_plot_change {0}, {1}",
            event.lower_limit(), event.upper_limit())

        self.__upper_edit.set_validator(
            event.lower_min(), event.upper_max(), self.__edit_precision)
        self.__lower_edit.set_validator(
            event.lower_min(), event.upper_max(), self.__edit_precision)

        self.__lower_edit.set_value(event.lower_limit())

        self.__upper_edit.set_value(event.upper_limit())


class HistogramDisplayControl(QWidget):

    class Layout(Enum):
        STACKED = 0
        HORIZONTAL = 1
        VERTICAL = 2

    class DisplayType(Enum):
        GREY_SCALE = 0
        RBG = 1

    __LOG:Logger = LogHelper.logger("HistogramDisplayControl")

    limit_changed = pyqtSignal(LimitChangeEvent)
    limits_reset = pyqtSignal(LimitResetEvent)
    layout_changed = pyqtSignal(Layout)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__menu = None
        self.__plots = dict()

        # Use stacked layout as default
        self.__create_stacked_layout()

    def __create_horizontal_layout(self):
        self.__plot_layout = QHBoxLayout()
        self.__plot_layout.setSpacing(1)
        self.__plot_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.__plot_layout)
        self.__current_layout = HistogramDisplayControl.Layout.HORIZONTAL

    def __create_vertical_layout(self):
        self.__plot_layout = QVBoxLayout()
        self.__plot_layout.setSpacing(1)
        self.__plot_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.__plot_layout)
        self.__current_layout = HistogramDisplayControl.Layout.VERTICAL

    def __create_stacked_layout(self):
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(1, 1, 1, 1)

        self.__plot_layout = QStackedLayout()
        self.__plot_layout.setContentsMargins(1, 1, 1, 1)
        self.__plot_layout.setSpacing(1)

        self.__tab_widget = QWidget()
        self.__tab_widget.setFixedHeight(20)
        self.__tab_widget.hide()

        self.__tab_layout = QHBoxLayout()
        self.__tab_layout.setContentsMargins(1, 1, 1, 1)
        self.__tab_layout.setAlignment(Qt.AlignLeft)
        self.__tab_layout.addSpacing(10)

        self.__red_button = QRadioButton("Red")
        self.__red_button.setStyleSheet("QRadioButton {color: red}")
        self.__red_button.toggled.connect(self.__handle_red_toggled)
        self.__tab_layout.addWidget(self.__red_button)
        self.__red_plot_index = None

        self.__green_button = QRadioButton("Green")
        self.__green_button.setStyleSheet("QRadioButton {color: green}")
        self.__green_button.toggled.connect(self.__handle_green_toggled)
        self.__tab_layout.addWidget(self.__green_button)
        self.__green_plot_index = None

        self.__blue_button = QRadioButton("Blue")
        self.__blue_button.setStyleSheet("QRadioButton {color: blue}")
        self.__blue_button.toggled.connect(self.__handle_blue_toggled)
        self.__tab_layout.addWidget(self.__blue_button)
        self.__tab_widget.setLayout(self.__tab_layout)
        self.__blue_plot_index = None

        layout.addWidget(self.__tab_widget)
        layout.addLayout(self.__plot_layout)
        self.setLayout(layout)
        self.__current_layout = HistogramDisplayControl.Layout.STACKED

    def __init_menu(self):
        self.__menu:QMenu = QMenu(self)

        stacked_action = QAction("Stacked", self)
        stacked_action.triggered.connect(self.__handle_stacked_selected)
        self.__menu.addAction(stacked_action)

        horizontal_action = QAction("Horizontal", self)
        horizontal_action.triggered.connect(self.__handle_horizontal_selected)
        self.__menu.addAction(horizontal_action)

        vertical_action = QAction("Vertical", self)
        vertical_action.triggered.connect(self.__handle_vertical_selected)
        self.__menu.addAction(vertical_action)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__handle_custom_context_menu)

    def __handle_custom_context_menu(self, position:QPoint):
        HistogramDisplayControl.__LOG.debug("__handle_custom_context_menu called position: {0}", position)
        self.__menu.popup(self.mapToGlobal(position))

    def __handle_stacked_selected(self):
        self.__swap_layout(HistogramDisplayControl.Layout.STACKED)

    def __handle_horizontal_selected(self):
        self.__swap_layout(HistogramDisplayControl.Layout.HORIZONTAL)

    def __handle_vertical_selected(self):
        self.__swap_layout(HistogramDisplayControl.Layout.VERTICAL)

    def __swap_layout(self, new_layout:Layout):
        # The plot's will have had their parent set to the layout so first
        # we undo that so they won't get deleted when the layout does.
        for band, plot in self.__plots.items():
            plot.setParent(None)

        if self.__current_layout == HistogramDisplayControl.Layout.STACKED:
            self.__red_button.setParent(None)
            self.__green_button.setParent(None)
            self.__blue_button.setParent(None)
            self.__tab_widget.setParent(None)

        # Per Qt docs we need to delete the current layout before we can set a new one
        # And it turns out we can't delete the layout until we reassign it to another widget
        # who becomes it's parent, then we delete the parent.
        tmp = QWidget()
        tmp.setLayout(self.layout())
        del tmp

        if new_layout == HistogramDisplayControl.Layout.STACKED:
            self.__create_stacked_layout()

        if new_layout == HistogramDisplayControl.Layout.HORIZONTAL:
            self.__create_horizontal_layout()

        if new_layout == HistogramDisplayControl.Layout.VERTICAL:
            self.__create_vertical_layout()

        for band, plot in self.__plots.items():
            self.__plot_layout.addWidget(plot)
            self.__wire_band(band, plot)
            if new_layout != HistogramDisplayControl.Layout.STACKED:
                # stacked layout hides plots not displayed so set them back
                plot.show()

        self.layout_changed.emit(new_layout)

    def __wire_band(self, band:Band, plot:AdjustableHistogramControl):
        if self.__current_layout == HistogramDisplayControl.Layout.STACKED:
            set_checked:bool = False
            if self.__plot_layout.count() == 1:
                set_checked = True
                self.__tab_widget.show()

            if band == Band.RED:
                self.__red_plot_index = self.__plot_layout.indexOf(plot)
                self.__red_button.setChecked(set_checked)

            if band == Band.GREEN:
                self.__green_plot_index = self.__plot_layout.indexOf(plot)
                self.__green_button.setChecked(set_checked)

            if band == Band.BLUE:
                self.__blue_plot_index = self.__plot_layout.indexOf(plot)
                self.__blue_button.setChecked(set_checked)

    @pyqtSlot(bool)
    def __handle_red_toggled(self, checked:bool):
        if checked:
            HistogramDisplayControl.__LOG.debug("red toggle checked")
            self.__plot_layout.setCurrentIndex(self.__red_plot_index)

    @pyqtSlot(bool)
    def __handle_green_toggled(self, checked:bool):
        if checked:
            HistogramDisplayControl.__LOG.debug("green toggle checked")
            self.__plot_layout.setCurrentIndex(self.__green_plot_index)

    @pyqtSlot(bool)
    def __handle_blue_toggled(self, checked:bool):
        if checked:
            HistogramDisplayControl.__LOG.debug("blue toggle checked")
            self.__plot_layout.setCurrentIndex(self.__blue_plot_index)

    def add_plot(self, raw_data:HistogramPlotData, adjusted_data:HistogramPlotData, band:Band):
        """Expects either one band with band of Band.GREY or three bands one each of
        Band.RED, Band.GREEN, Band.BLUE.  If these conditions are not met the code will attempt
        to be accommodating and won't throw and error but you might get strange results."""
        plots = AdjustableHistogramControl(band)
        plots.set_raw_data(raw_data)
        plots.set_adjusted_data(adjusted_data)
        plots.limit_changed.connect(self.limit_changed)
        plots.limits_reset.connect(self.limits_reset)

        self.__plots[band] = plots
        self.__plot_layout.addWidget(plots)

        if self.__plot_layout.count() == 2:
            self.__init_menu()

        if band == Band.RED or band == Band.GREEN or band == Band.BLUE:
            self.__wire_band(band, plots)

    def set_adjusted_data(self, data:HistogramPlotData, band:Band):
        """Update the adjusted data for a Band that has already been added using
        add_plot"""
        plots:AdjustableHistogramControl = self.__plots[band]
        if plots is not None:
            plots.set_adjusted_data(data)

    def update_limits(self, data:HistogramPlotData, band:Band):
        plots:AdjustableHistogramControl = self.__plots[band]
        if plots is not None:
            plots.update_limits(data)


class HistogramDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("HistogramDisplayWindow")

    limit_changed = pyqtSignal(LimitChangeEvent)
    limits_reset = pyqtSignal(LimitResetEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__init_ui()

    def __init_ui(self):
        self.setWindowTitle("Histogram")
        self.__histogram_control = HistogramDisplayControl()
        self.__histogram_control.limit_changed.connect(self.limit_changed)
        self.__histogram_control.limits_reset.connect(self.limits_reset)
        self.__histogram_control.layout_changed.connect(self.__handle_layout_changed)
        self.setCentralWidget(self.__histogram_control)

    @pyqtSlot(HistogramDisplayControl.Layout)
    def __handle_layout_changed(self, new_layout:HistogramDisplayControl.Layout):
        if new_layout == HistogramDisplayControl.Layout.STACKED:
            self.resize(800, 400)

        if new_layout == HistogramDisplayControl.Layout.HORIZONTAL:
            self.resize(1300, 400)

        if new_layout == HistogramDisplayControl.Layout.VERTICAL:
            self.resize(800, 800)

    def create_plot_control(self, raw_data:HistogramPlotData, adjusted_data:HistogramPlotData, band:Band):
        self.__histogram_control.add_plot(raw_data, adjusted_data, band)

    def set_adjusted_data(self, data:HistogramPlotData, band:Band):
        self.__histogram_control.set_adjusted_data(data, band)

    def update_limits(self, raw_data:HistogramPlotData, band:Band):
        self.__histogram_control.update_limits(raw_data, band)
