from math import floor

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QSizePolicy, QMainWindow, QHBoxLayout, QWidget
from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.lines as lines

from openspectra.openspecrtra_tools import PlotData, HistogramPlotData, LinePlotData


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
            color=data.color, linestyle=data.linestyle)

        super().plot(data)

    def add_plot(self, data:LinePlotData):
        self._axes.plot(data.xdata, data.ydata, color=data.color, linestyle=data.linestyle)
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

    limit_changed = pyqtSignal(LimitChangeEvent)

    def __init__(self, parent=None, width=5, height=4, dpi=75):
        super().__init__(parent, width, height, dpi)
        self.__lower_limit_x = None
        self.__upper_limit_x = None
        self.__dragging = None
        self.__drag_start = None

    def __del__(self):
        self.__dragging = None
        self.__drag_start = None
        self.__upper_limit_x = None
        self.__lower_limit_x = None

    def plot(self, data:HistogramPlotData):
        super().plot(data)

        self.mpl_connect("motion_notify_event", self.__on_mouse_move)
        self.mpl_connect("button_release_event", self.__on_mouse_release)

        self.__lower_limit_x = data.lower_limit
        self.__upper_limit_x = data.upper_limit

        self.__lower_limit = lines.Line2D([self.__lower_limit_x, self.__lower_limit_x],
            [0, self._axes.get_ylim()[1] - 8], transform=self._axes.transData,
            figure=self._axes.figure, picker=5)

        self.__upper_limit = lines.Line2D([self.__upper_limit_x, self.__upper_limit_x],
            [0, self._axes.get_ylim()[1] - 8], transform=self._axes.transData,
            figure=self._axes.figure, picker=5)
        self.figure.lines.extend([self.__lower_limit, self.__upper_limit])
        self.mpl_connect("pick_event", self.__on_pick)

    # TODO ??
    def set_lower_limit(self, xdata):
        pass

    # TODO ??
    def set_upper_limit(self, xdata):
        pass

    def __on_mouse_release(self, event: MouseEvent):
        print("Mouse released at ", event.xdata)
        if self.__dragging is not None and self.__drag_start is not None:
            line_id = self.__get_limit_id(self.__dragging)
            if line_id is not None:
                new_loc = floor(event.xdata)
                limit_event = LimitChangeEvent(line_id, new_loc)
                self.limit_changed.emit(limit_event)

            self.__drag_start = None
            self.__dragging = None

    def __get_limit_id(self, limit_line: lines.Line2D) -> str:
        if limit_line is self.__lower_limit:
            return "lower"
        elif limit_line is self.__upper_limit:
            return "upper"
        else:
            return None

    def __on_pick(self, event: PickEvent):
        if event.artist == self.__lower_limit:
            print("picked lower limit at ", self.__lower_limit.get_xdata())
        elif event.artist == self.__upper_limit:
            print("picked upper limit at ", self.__upper_limit.get_xdata())

        self.__dragging = event.artist
        self.__drag_start = event.artist.get_xdata()

    def __on_mouse_move(self, event: MouseEvent):
        if self.__dragging is not None and self.__drag_start is not None:
            self.__dragging.set_xdata([event.xdata, event.xdata])
            self.draw()
        else:
            print("Mouse move - name: {0}, canvas: {1}, axes: {2}, x: {3}, y: {4}, xdata: {5}, ydata: {6}".
                format(event.name, event.canvas, event.inaxes,
                event.x, event.y, event.xdata, event.ydata))


class LinePlotDisplayWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__plot_canvas = LinePlotCanvas(self, width=5, height=4)

    def __del__(self):
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


class HistogramDisplayWindow(QMainWindow):

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
