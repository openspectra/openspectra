import logging
from math import floor, ceil

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QResizeEvent, QCloseEvent
from PyQt5.QtWidgets import QSizePolicy, QMainWindow, QHBoxLayout, QWidget
from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.lines as lines

from openspectra.openspecrtra_tools import PlotData, HistogramPlotData, LinePlotData
from openspectra.utils import Logger


class LimitChangeEvent(QObject):

    def __init__(self, id, limit):
        super().__init__()
        self.__id = id
        self.__limit = limit

    def id(self):
        return self.__id

    def limit(self):
        return self.__limit


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
        self._axes.set_xlabel(data.xlabel)
        self._axes.set_ylabel(data.ylabel)
        self._axes.set_title(data.title)
        self.draw()


class LinePlotCanvas(PlotCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=75):
        super().__init__(parent, width, height, dpi)

    def plot(self, data:LinePlotData):
        if self._current_plot is not None:
            self._current_plot.remove()

        self._current_plot, = self._axes.plot(data.xdata, data.ydata,
            color=data.color, linestyle=data.linestyle, label=data.legend)
        if data.legend is not None:
            self._axes.legend(loc='best')
        super().plot(data)

    def add_plot(self, data:LinePlotData):
        self._axes.plot(data.xdata, data.ydata, color=data.color,
            linestyle=data.linestyle, label=data.legend)
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
        self._axes.hist(data.ydata, data.xdata,
            color=data.color, linestyle=data.linestyle)
        super().plot(data)

    def update_plot(self, data:HistogramPlotData):
        # TODO clear and replace whole plot is a bit inefficient
        self._axes.clear()
        self.plot(data)


class AdjustableHistogramPlotCanvas(HistogramPlotCanvas):

    __LOG:logging.Logger = Logger.logger("AdjustableHistogramPlotCanvas")

    limit_changed = pyqtSignal(LimitChangeEvent)

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

        # TODO don't think this will work with float data, need figure out scale
        self.__min_adjust_x = ceil(self._axes.get_xlim()[0])
        self.__max_adjust_x = floor(self._axes.get_xlim()[1])
        AdjustableHistogramPlotCanvas.__LOG.debug("min_adjust_x: %f, max_adjust_x %f",
            self.__min_adjust_x, self.__max_adjust_x)

    def __on_mouse_release(self, event: MouseEvent):
        if self.__dragging is not None:
            line_id = self.__get_limit_id(self.__dragging)
            if line_id is not None:
                new_loc = floor(self.__dragging.get_xdata()[0])
                limit_event = LimitChangeEvent(line_id, new_loc)
                self.limit_changed.emit(limit_event)
                AdjustableHistogramPlotCanvas.__LOG.debug("New limit loc: %f", new_loc)

            self.__dragging = None

    # TODO why do I need this? eventually need to tell them apart? better way?
    def __get_limit_id(self, limit_line: lines.Line2D) -> str:
        if limit_line is self.__lower_limit:
            return "lower"
        elif limit_line is self.__upper_limit:
            return "upper"
        else:
            return None

    def __on_pick(self, event: PickEvent):
        if event.artist == self.__lower_limit:
            AdjustableHistogramPlotCanvas.__LOG.debug("picked lower limit at %s",
                str(self.__lower_limit.get_xdata()))
        elif event.artist == self.__upper_limit:
            AdjustableHistogramPlotCanvas.__LOG.debug("picked upper limit at %s",
                str(self.__upper_limit.get_xdata()))

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
            # TODO???? Logger blows up because sometimes some values are None
            # TODO remove this
            # AdjustableHistogramPlotCanvas.__LOG.debug(
            #     "Mouse move - name: %s, canvas: %s, axes: %s, x: %f, y: %f, xdata: %f, ydata: %f",
            #     event.name, event.canvas, event.inaxes,
            #     event.x, event.y, event.xdata, event.ydata)


class LinePlotDisplayWindow(QMainWindow):

    __LOG:logging.Logger = Logger.logger("LinePlotDisplayWindow")

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


class HistogramDisplayWindow(QMainWindow):

    __LOG:logging.Logger = Logger.logger("HistogramDisplayWindow")

    limit_changed = pyqtSignal(LimitChangeEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histogram")
        self.__frame = QWidget()

        self.__raw_data_canvas = AdjustableHistogramPlotCanvas(self, width=5, height=4)
        self.__raw_data_canvas.limit_changed.connect(self.__handle_hist_limit_change)
        self.__adjusted_data_canvas = HistogramPlotCanvas(self, width=5, height=4)

        layout = QHBoxLayout()
        layout.addWidget(self.__raw_data_canvas)
        layout.addWidget(self.__adjusted_data_canvas)

        self.__frame.setLayout(layout)
        self.setCentralWidget(self.__frame)
        self.__has_adjusted_data = False;

    def __del__(self):
        HistogramDisplayWindow.__LOG.debug("HistogramDisplayWindow.__del__ called...")
        self.__adjusted_data_canvas = None
        self.__raw_data_canvas = None
        self.__frame = None

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
