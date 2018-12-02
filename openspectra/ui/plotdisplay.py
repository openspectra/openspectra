from enum import Enum
from math import floor, ceil
from typing import Union

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QResizeEvent, QCloseEvent
from PyQt5.QtWidgets import QSizePolicy, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QFrame, QGroupBox, \
    QLineEdit, QInputDialog
from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.lines as lines

from openspectra.openspecrtra_tools import PlotData, HistogramPlotData, LinePlotData
from openspectra.utils import LogHelper, Logger


class LimitChangeEvent(QObject):

    class Limit(Enum):
        Lower = 0
        Upper = 1

    def __init__(self, id:Limit, limit:Union[int, float]):
        super().__init__()
        self.__id = id
        self.__limit = limit

    def id(self) -> Limit:
        return self.__id

    def limit(self) -> Union[int, float]:
        return self.__limit


class PlotChangeEvent(QObject):

    def __init__(self, lower_limit:Union[int, float], upper_limit:Union[int, float],
            lower_min: Union[int, float], upper_max: Union[int, float]):
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


# TODO seperate out plot generation from any UI classes - an API perhaps?
class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=75):
        self._current_plot = None

        fig = Figure(figsize=(width, height), dpi=dpi)
        self._axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def __del__(self):
        self._current_plot = None
        self._axes.clear()
        self._axes = None
        # TODO anything else?

    def plot(self, data:PlotData):
        # TODO something better than setting it over and over??
        # TODO only reset if change is detected??  Seems to work though
        self._axes.set_xlabel(data.x_label)
        self._axes.set_ylabel(data.y_label)
        self._axes.set_title(data.title)
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

    def __init__(self, parent=None, width=5, height=4, dpi=75):
        super().__init__(parent, width, height, dpi)

    def plot(self, data:HistogramPlotData):
        self._axes.hist(data.y_data, data.bins, data.x_data,
            color=data.color, linestyle=data.line_style)
        super().plot(data)

    def update_plot(self, data:HistogramPlotData):
        # TODO clear and replace whole plot is a bit inefficient
        self._axes.clear()
        self.plot(data)


class AdjustableHistogramPlotCanvas(HistogramPlotCanvas):

    __LOG:Logger = LogHelper.logger("AdjustableHistogramPlotCanvas")

    limit_changed = pyqtSignal(LimitChangeEvent)
    plot_changed = pyqtSignal(PlotChangeEvent)

    def __init__(self, parent=None, width=5, height=4, dpi=75):
        super().__init__(parent, width, height, dpi)
        self.__min_adjust_x = None
        self.__max_adjust_x = None
        self.__dragging:lines.Line2D = None

    def __del__(self):
        self.__dragging = None
        self.__min_adjust_x = None
        self.__max_adjust_x = None

    def plot(self, data:HistogramPlotData):
        super().plot(data)

        self.mpl_connect("motion_notify_event", self.__on_mouse_move)
        self.mpl_connect("button_release_event", self.__on_mouse_release)

        self.__lower_limit = lines.Line2D([data.lower_limit, data.lower_limit],
            [0, self._axes.get_ylim()[1] - 8], transform=self._axes.transData,
            figure=self._axes.figure, picker=5)

        self.__upper_limit = lines.Line2D([data.upper_limit, data.upper_limit],
            [0, self._axes.get_ylim()[1] - 8], transform=self._axes.transData,
            figure=self._axes.figure, picker=5)
        self.figure.lines.extend([self.__lower_limit, self.__upper_limit])
        self.mpl_connect("pick_event", self.__on_pick)

        self.__min_adjust_x = self._axes.get_xlim()[0]
        self.__max_adjust_x = self._axes.get_xlim()[1]
        AdjustableHistogramPlotCanvas.__LOG.debug("min_adjust_x: {0}, max_adjust_x {1}",
            self.__min_adjust_x, self.__max_adjust_x)

        plot_event = PlotChangeEvent(data.lower_limit, data.upper_limit,
            self.__min_adjust_x, self.__max_adjust_x)
        self.plot_changed.emit(plot_event)

    def __on_mouse_release(self, event: MouseEvent):
        if self.__dragging is not None:
            line_id = self.__get_limit_id(self.__dragging)
            if line_id is not None:
                new_loc = self.__dragging.get_xdata()[0]
                limit_event = LimitChangeEvent(line_id, new_loc)
                self.limit_changed.emit(limit_event)
                AdjustableHistogramPlotCanvas.__LOG.debug("New limit loc: {0}", new_loc)

            self.__dragging = None

    # TODO why do I need this? eventually need to tell them apart? better way?
    def __get_limit_id(self, limit_line: lines.Line2D) -> LimitChangeEvent.Limit:
        if limit_line is self.__lower_limit:
            return LimitChangeEvent.Limit.Lower
        elif limit_line is self.__upper_limit:
            return LimitChangeEvent.Limit.Upper
        else:
            return None

    def __on_pick(self, event: PickEvent):
        if event.artist == self.__lower_limit:
            AdjustableHistogramPlotCanvas.__LOG.debug("picked lower limit at {0}", self.__lower_limit.get_xdata())
        elif event.artist == self.__upper_limit:
            AdjustableHistogramPlotCanvas.__LOG.debug("picked upper limit at {0}", self.__upper_limit.get_xdata())

        self.__dragging = event.artist

    def __on_mouse_move(self, event: MouseEvent):
        if self.__dragging is not None and event.xdata is not None:
            new_x = event.xdata
            if new_x > self.__max_adjust_x:
                new_x = self.__max_adjust_x
            elif new_x < self.__min_adjust_x:
                new_x = self.__min_adjust_x

            self.__dragging.set_xdata([new_x, new_x])
            self.draw()

        else:
            pass
            # TODO remove this
            # AdjustableHistogramPlotCanvas.__LOG.debug(
            #     "Mouse move - name: {0}, canvas: {1}, axes: {2}, x: {3}, y: {4}, xdata: {5}, ydata: {6}",
            #     event.name, event.canvas, event.inaxes,
            #     event.x, event.y, event.xdata, event.ydata)


class LinePlotDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("LinePlotDisplayWindow")

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__plot_canvas = LinePlotCanvas(self, width=5, height=4)

        # TODO Qt::WA_DeleteOnClose - set to make sure it's deleted???
        # TODO this requires the user to create a new instance to reuse
        # TODO don't think we want this.
        # self.setAttribute(Qt.WA_DeleteOnClose)

        # TODO also read that setting a windows paren assures that the child
        # TODO is deleted when the parent is, might make clean up safer if doing manually

    def __del__(self):
        LinePlotDisplayWindow.__LOG.debug("LinePlotDisplayWindow.__del__ called...")
        self.__plot_canvas = None

    def plot(self, data:LinePlotData):
        self.__plot_canvas.plot(data)

    def add_plot(self, data:LinePlotData):
        self.__plot_canvas.add_plot(data)

    def clear(self):
        self.__plot_canvas.clear()

    # TODO do we need this??
    def resizeEvent(self, event:QResizeEvent):
        size = event.size()
        self.__plot_canvas.resize(size)

    def closeEvent(self, event:QCloseEvent):
        self.closed.emit()
        # accepting hides the window
        event.accept()


class AdjustableHistogramControl(QWidget):

    __LOG:Logger = LogHelper.logger("AdjustableHistogramControl")

    limit_changed = pyqtSignal(LimitChangeEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__has_adjusted_data = False
        self.__raw_data_canvas = AdjustableHistogramPlotCanvas(self, width=5, height=4)
        self.__raw_data_canvas.limit_changed.connect(self.__handle_hist_limit_change)
        self.__raw_data_canvas.plot_changed.connect(self.__handle_plot_change)
        self.__adjusted_data_canvas = HistogramPlotCanvas(self, width=5, height=4)

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

        self.__low_edit = QLineEdit()
        self.__low_edit.setMaximumWidth(60)
        self.__low_edit.deselect()
        # TODO low_edit.setInputMask()
        # TODO low_edit.setValidator()
        # TODO low_edit.addAction()
        control_layout.addWidget(self.__low_edit)
        control_layout.addSpacing(10)

        high_label = QLabel("high limit:")
        high_label.setFixedWidth(60)
        control_layout.addWidget(high_label)

        self.__high_edit = QLineEdit()
        self.__high_edit.setMaximumWidth(60)
        self.__high_edit.deselect()
        # TODO high_edit.setInputMask()
        # TODO high_edit.setValidator()
        # TODO high_edit.addAction()
        control_layout.addWidget(self.__high_edit)

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

    def __del__(self):
        AdjustableHistogramControl.__LOG.debug("AdjustableHistogramControl.__del__ called...")
        self.__adjusted_data_canvas = None
        self.__raw_data_canvas = None
        self.__low_edit = None
        self.__high_edit = None

    def set_raw_data(self, data:HistogramPlotData):
        self.__raw_data_canvas.plot(data)

    def set_adjusted_data(self, data:HistogramPlotData):
        if not self.__has_adjusted_data:
            self.__adjusted_data_canvas.plot(data)
            self.__has_adjusted_data = True
        else:
            self.__adjusted_data_canvas.update_plot(data)

    @pyqtSlot(LimitChangeEvent)
    def __handle_hist_limit_change(self, event:LimitChangeEvent):
        self.limit_changed.emit(event)
        if event.id() == LimitChangeEvent.Limit.Lower:
            self.__low_edit.setText(str(event.limit()))
        elif event.id() == LimitChangeEvent.Limit.Upper:
            self.__high_edit.setText(str(event.limit()))

    @pyqtSlot(PlotChangeEvent)
    def __handle_plot_change(self, event:PlotChangeEvent):
        self.__low_edit.setText(str(event.lower_limit()))
        self.__high_edit.setText(str(event.upper_limit()))


class HistogramDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("HistogramDisplayWindow")

    limit_changed = pyqtSignal(LimitChangeEvent)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self):

        self.setWindowTitle("Histogram")

        # TODO, next add capability for multiple AdjustableHistogramControls here
        # TODO layout options for them
        self.__adj_hist_control = AdjustableHistogramControl(self)
        self.__adj_hist_control.limit_changed.connect(self.limit_changed)
        self.setCentralWidget(self.__adj_hist_control)

    def __del__(self):
        HistogramDisplayWindow.__LOG.debug("HistogramDisplayWindow.__del__ called...")
        self.__adj_hist_control = None

    def create_plot_control(self, raw_data:HistogramPlotData, adjusted_data:HistogramPlotData):
        self.__adj_hist_control.set_raw_data(raw_data)
        self.__adj_hist_control.set_adjusted_data(adjusted_data)

    def set_adjusted_data(self, data:HistogramPlotData):
        self.__adj_hist_control.set_adjusted_data(data)
