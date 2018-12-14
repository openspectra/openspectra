import itertools
from enum import Enum
from math import floor

import numpy as np
from numpy import ma

from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QObject, QTimer, QSize, pyqtSlot, QRect, QPoint
from PyQt5.QtGui import QPalette, QImage, QPixmap, QMouseEvent, QResizeEvent, QCloseEvent, QPaintEvent, QPainter, \
    QPolygon, QCursor
from PyQt5.QtWidgets import QScrollArea, QLabel, QSizePolicy, QMainWindow, QDockWidget, QWidget, QPushButton, \
    QHBoxLayout, QApplication, QStyle

from openspectra.image import Image
from openspectra.utils import LogHelper, Logger


class AdjustedMouseEvent(QObject):

    def __init__(self, event:QMouseEvent, xscale, yscale):
        super().__init__(None)
        self.__event = event
        self.__pixel_x = floor(event.x() * xscale)
        self.__pixel_y = floor(event.y() * yscale)
        self.__pixel_pos = (self.__pixel_x, self.__pixel_y)

    def event(self) -> QMouseEvent:
        return self.__event

    def pixel_x(self):
        return self.__pixel_x

    def pixel_y(self):
        return self.__pixel_y

    def pixel_pos(self):
        return self.__pixel_pos


class AreaSelectedEvent(QObject):

    def __init__(self, x_points:np.ndarray, y_points:np.ndarray):
        super().__init__(None)
        self.__x_points = x_points
        self.__y_points = y_points

    def x_points(self) -> np.ndarray:
        return self.__x_points

    def y_points(self) -> np.ndarray:
        return self.__y_points


class MouseCoordinates(QLabel):

    __LOG:Logger = LogHelper.logger("MouseCoordinates")

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(AdjustedMouseEvent)
    def on_mouse_move(self, event:AdjustedMouseEvent):
        # users are accustom to screen coordinates being 1 based
        self.setText(" x: {0} y: {1}".format(
            event.pixel_x() + 1, event.pixel_y() + 1))


class ImageLabel(QLabel):

    __LOG:Logger = LogHelper.logger("ImageLabel")

    class Action(Enum):
        Nothing = 0
        Dragging = 1
        Drawing = 2

    # TODO on double click we get both clicked and doubleClicked
    # TODO decide if we need both and fix
    area_selected = pyqtSignal(AreaSelectedEvent)
    clicked = pyqtSignal(AdjustedMouseEvent)
    double_clicked = pyqtSignal(AdjustedMouseEvent)
    mouse_move = pyqtSignal(AdjustedMouseEvent)

    def __init__(self, location_rect:bool=True, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)

        self.__last_mouse_loc:QPoint = None
        self.__initial_height = 0
        self.__initial_width = 0

        self.__default_cursor = self.cursor()
        self.__drag_cursor = QCursor(Qt.ClosedHandCursor)
        self.__draw_cursor = QCursor(Qt.CrossCursor)

        if location_rect:
            # TODO set based on image dimensions?
            self.__rect = QRect(150, 150, 50, 50)
            self.__center = self.__rect.center()
        else:
            self.__rect = None
            self.__center = None

        self.__dragging = False

        self.__polygon:QPolygon = None
        self.__polygon_bounds:QRect = None
        self.__drawing = False

        self.__current_action = ImageLabel.Action.Nothing

    def __del__(self):
        ImageLabel.__LOG.debug("ImageLabel.__del__ called...")
        self.__polygon_bounds = None
        self.__polygon = None

        self.__center = None
        self.__rect = None

        self.__default_cursor = None
        self.__drag_cursor = None
        self.__draw_cursor = None

        self.__last_mouse_loc = None

    def changeEvent(self, event:QEvent):
        if event.type() == QEvent.ParentChange and self.pixmap() is not None \
                and self.__initial_height == 0 and self.__initial_width == 0:
            self.__initial_height = self.pixmap().height()
            self.__initial_width = self.pixmap().width()

    def mouseMoveEvent(self, event:QMouseEvent):
        if self.__current_action == ImageLabel.Action.Drawing:
            self.__polygon << event.pos()
            self.update()

        if self.__current_action == ImageLabel.Action.Dragging and \
                self.__last_mouse_loc is not None and self.__rect is not None:
            self.__center += event.pos() - self.__last_mouse_loc
            self.__rect.moveCenter(self.__center)
            self.__last_mouse_loc = event.pos()
            self.update()

        adjusted_move = self.__create_adjusted_mouse_event(event)
        self.mouse_move.emit(adjusted_move)

    def mousePressEvent(self, event:QMouseEvent):
        # TODO remove if not used
        ImageLabel.__LOG.debug("mousePressEvent")

    def mouseReleaseEvent(self, event:QMouseEvent):
        if self.__current_action == ImageLabel.Action.Dragging:
            self.__current_action = ImageLabel.Action.Nothing
            self.setCursor(self.__default_cursor)
            self.update()

        elif self.__current_action == ImageLabel.Action.Drawing:
            self.__current_action = ImageLabel.Action.Nothing
            self.setCursor(self.__default_cursor)
            # trigger the collection of spectra plots points
            self.__get_select_pixels()
            self.update()

        # Then it's a click
        elif self.__last_mouse_loc is not None:
            self.clicked.emit(self.__create_adjusted_mouse_event(event))

        self.__last_mouse_loc = None

    def mouseDoubleClickEvent(self, event:QMouseEvent):
        ImageLabel.__LOG.debug("mouseDoubleClickEvent")
        self.double_clicked.emit(self.__create_adjusted_mouse_event(event))

    # TODO don't need??
    def resize(self, size:QSize):
        ImageLabel.__LOG.debug("Resizing to w: {0}, h: {1}", size.width(), size.height())
        super().resize(size)

    def eventFilter(self, object:QObject, event:QEvent):
        if event.type() == QEvent.MouseButtonPress:
            self.__last_mouse_loc = event.pos()
            QTimer.singleShot(300, self.__pressed)
            # event was handled
            return True

        return False

    # TODO not sure we need the DOUBLE CLICK but keep it for the example for now
    # this is best way I could figure to distinguish single and double mouse clicks
    # def eventFilter(self, object:QObject, event:QEvent):
    #     if event.type() == QEvent.MouseButtonPress:
    #         self.__clickEvent = (event.x(), event.y())
    #         QTimer.singleShot(QApplication.instance().doubleClickInterval(), self.__clicked)
    #         # event was handled
    #         return True
    #
    #     elif event.type() == QEvent.MouseButtonDblClick:
    #         self.__clickEvent = None
    #     return False

    def paintEvent(self, qPaintEvent:QPaintEvent):
        # first render the image
        super().paintEvent(qPaintEvent)
        # TODO not sure why but these seem to need to be created here each time
        painter = QPainter(self)
        painter.setPen(Qt.red)

        if self.__rect is not None:
            painter.drawRect(self.__rect)

        if self.__polygon is not None:
            painter.drawPoints(self.__polygon)

            # TODO not sure this is how we want to go but interesting
            self.__polygon_bounds = self.__polygon.boundingRect()
            painter.drawRect(self.__polygon_bounds)

    def clear_selected_area(self):
        self.__polygon_bounds = None
        self.__polygon = None
        self.update()

    def __get_select_pixels(self):
        if self.__polygon_bounds is not None:
            x1, y1, x2, y2 = self.__polygon_bounds.getCoords()
            ImageLabel.__LOG.debug("Selected coords: {0}, {1}, {2}, {3}", x1, y1, x2, y2)

            # create an array of contained by the bounding rectangle
            x_range = ma.arange(x1, x2 + 1)
            y_range = ma.arange(y1, y2 + 1)
            points = ma.array(list(itertools.product(x_range, y_range)))

            # check to see which points also fall inside of the polygon
            for i in range(len(points)):
                if not self.__polygon.containsPoint(QPoint(points[i][0], points[i][1]), Qt.WindingFill):
                    points[i] = ma.masked

            # split the points back into x and y values
            x = points[:, 0]
            y = points[:, 1]

            # take only the point that were inside the polygon
            x = x[~x.mask]
            y = y[~y.mask]
            self.area_selected.emit(AreaSelectedEvent(x, y))

    def __pressed(self):
        # TODO set special cursor depending on action??
        if self.__last_mouse_loc is not None:
            if self.__rect is not None and self.__rect.contains(self.__last_mouse_loc):
                self.__current_action = ImageLabel.Action.Dragging
                self.setCursor(self.__drag_cursor)
            else:
                self.__current_action = ImageLabel.Action.Drawing
                self.setCursor(self.__draw_cursor)
                self.__polygon = QPolygon()

    def __create_adjusted_mouse_event(self, event:QMouseEvent):
        return AdjustedMouseEvent(event, self.__initial_width/self.width(),
            self.__initial_height/self.height())

    # def __clicked(self):
    #     if self.__clickEvent is not None:
    #         self.clicked.emit(self.__clickEvent[0], self.__clickEvent[1])

    # TODO Get aspect ratio here?
    # def setPixmap(self, qPixmap:QPixmap):
    #     super().setPixmap(qPixmap)

    # def heightForWidth(self, width):
    #     print("heightForWidth with: ", width)
    #     return int(width * self.__ratio)

    # def sizeHint(self):
    #     return self.__perferred_size

    # def minimumSizeHint(self):
    #     return self.__perferred_size

    # def minimumHeight(self):
    #     return self.__perferred_size.height()

    # def minimumSize(self):
    #     return self.__perferred_size


class ImageDisplay(QScrollArea):

    __LOG:Logger = LogHelper.logger("ImageDisplay")

    area_selected = pyqtSignal(AreaSelectedEvent)
    clicked = pyqtSignal(AdjustedMouseEvent)
    mouse_move = pyqtSignal(AdjustedMouseEvent)

    def __init__(self, image:Image, qimage_format:QImage.Format=QImage.Format_Grayscale8,
            location_rect:bool=True, parent=None):
        super().__init__(parent)

        # TODO make settable prop?
        self.__margin_width = 4
        self.__margin_height = 4

        # TODO do we need to hold the data itself?
        self.__image = image
        self.__qimage_format = qimage_format

        self.__imageLabel = ImageLabel(location_rect, self)
        self.__imageLabel.setBackgroundRole(QPalette.Base)
        self.__imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        # sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # sizePolicy.setHeightForWidth(True)
        # self.__imageLabel.setSizePolicy(sizePolicy)

        # self.__imageLabel.setScaledContents(True)
        self.__imageLabel.setMouseTracking(True)

        self.__imageLabel.area_selected.connect(self.area_selected)
        self.__imageLabel.clicked.connect(self.clicked)
        self.__imageLabel.double_clicked.connect(self.__double_click_handler)
        self.__imageLabel.mouse_move.connect(self.mouse_move)

        self.setBackgroundRole(QPalette.Dark)
        self.__display_image()

    def __display_image(self):
        # TODO do I need to keep self.__height, & self.__width?
        self.__image_height, self.__image_width = self.__image.image_shape()

        self.__qimage:QImage = QImage(self.__image.image_data(), self.__image_width,
            self.__image_height, self.__image.bytes_per_line(), self.__qimage_format)

        self.__pixmap:QPixmap = QPixmap.fromImage(self.__qimage)
        self.__imageLabel.setPixmap(self.__pixmap)
        self.setWidget(self.__imageLabel)
        self.setAlignment(Qt.AlignHCenter)

        # small margins to give a little extra room so the cursor doesn't change too soon.
        self.setViewportMargins(self.__margin_width, self.__margin_height,
            self.__margin_width, self.__margin_height)

        self.show()

    def __del__(self):
        # TODO ??
        ImageDisplay.__LOG.debug("ImageDisplay.__del__ called...")
        self.__pixmap = None
        self.__qimage = None
        self.__imageLabel = None
        self.__image = None

    # TODO not sure we need this but keep it for the example for now
    @pyqtSlot(AdjustedMouseEvent)
    def __double_click_handler(self, event:AdjustedMouseEvent):
        # TODO remove?
        ImageDisplay.__LOG.debug("Double clicked x: {0} y: {1}",
            event.pixel_x() + 1, event.pixel_y() + 1)

    def refresh_image(self):
        # TODO do I need to del the old QImage & QPixmap object???
        # TODO I think they should be garbage collected once the ref is gone?
        self.__display_image()

    def clear_selected_area(self):
        self.__imageLabel.clear_selected_area()

    def scale_image(self, factor:float):
        ImageDisplay.__LOG.debug("scaling image by: {0}", factor)
        new_size = self.__pixmap.size() * factor
        self.__pixmap = self.__pixmap.scaled(new_size,  Qt.KeepAspectRatio)
        self.__imageLabel.setPixmap(self.__pixmap)
        self.resize(new_size)

    def image_width(self) -> int:
        return self.__image_width

    def image_height(self) -> int:
        return self.__image_height

    def margin_width(self) -> int:
        return self.__margin_width

    def margin_height(self) -> int:
        return self.__margin_height

    def resize(self, size:QSize):
        ImageDisplay.__LOG.debug("Resizing to w: {0}, h: {1}", size.width(), size.height())
        super().resize(size)
        self.__imageLabel.resize(size)


class ImageDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("ImageDisplayWindow")

    pixel_selected = pyqtSignal(AdjustedMouseEvent)
    mouse_moved = pyqtSignal(AdjustedMouseEvent)
    area_selected = pyqtSignal(AreaSelectedEvent)

    def __init__(self, image:Image, label, qimage_format:QImage.Format,
                screen_geometry:QRect, location_rect:bool=True, parent=None):
        super().__init__(parent)
        self._screen_geometry = screen_geometry
        # TODO do we need to hold the data itself?
        self.__image = image
        self._image_display = ImageDisplay(self.__image, qimage_format, location_rect, self)
        self.__init_ui(label)

    def __init_ui(self, label):
        self.setWindowTitle(label)

        self.setCentralWidget(self._image_display)
        self._image_display.setAlignment(Qt.AlignHCenter)

        self._mouse_widget = QDockWidget("Mouse", self)
        self._mouse_widget.setTitleBarWidget(QWidget(None))
        self._mouse_viewer = MouseCoordinates()
        # TODO make height configurable???
        # set to fixed height so we know how to layout the image display window
        self._mouse_viewer.setFixedHeight(16)

        self._image_display.mouse_move.connect(self._mouse_viewer.on_mouse_move)
        self._image_display.clicked.connect(self.pixel_selected)
        self._image_display.mouse_move.connect(self.mouse_moved)
        self._image_display.area_selected.connect(self.area_selected)

        self._mouse_widget.setWidget(self._mouse_viewer)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._mouse_widget)

    def __del__(self):
        # TODO???
        ImageDisplayWindow.__LOG.debug("ImageDisplayWindow.__del__ called...")
        self._image_display = None
        self.__image = None
        #TODO self.____mouseWidget = None Or does the window system handle this?
        self._screen_geometry = None

    @pyqtSlot()
    def handle_stats_closed(self):
        self._image_display.clear_selected_area()

    def refresh_image(self):
        self._image_display.refresh_image()

    def resizeEvent(self, event:QResizeEvent):
        size = event.size()
        # size -= QSize(10, 20)
        # self.__image_display.resize(size)


class MainImageDisplayWindow(ImageDisplayWindow):

    __LOG:Logger = LogHelper.logger("MainImageDisplayWindow")

    closed = pyqtSignal()

    def __init__(self, image:Image, label, qimage_format:QImage.Format,
                screen_geometry:QRect, parent=None):
        super().__init__(image, label, qimage_format, screen_geometry, True, parent)

        self.__scroll_bar_width = QApplication.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        MainImageDisplayWindow.__LOG.debug("scroll_bar_width: {0}", self.__scroll_bar_width)

        self.__frame_width = QApplication.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        MainImageDisplayWindow.__LOG.debug("frame_width: {0}", self.__frame_width)

        self.__margin_width = self._image_display.margin_width()
        self.__margin_height = self._image_display.margin_height()
        MainImageDisplayWindow.__LOG.debug("margin_width: {0}, margin_height {1}", self.__margin_width, self.__margin_height)

        title_bar_height = QApplication.style().pixelMetric(QStyle.PM_TitleBarHeight)
        MainImageDisplayWindow.__LOG.debug("title_bar_height: {0}", title_bar_height)

        self.__mouse_viewer_height = self._mouse_viewer.height()
        MainImageDisplayWindow.__LOG.debug("mouse_viewer_height: {0}", self.__mouse_viewer_height)

        self.__oversize_width = self._screen_geometry.width() - self.__frame_width * 2
        self.__oversize_height = self._screen_geometry.height() - title_bar_height

        self.__set_size()

    def __set_size(self):
        MainImageDisplayWindow.__LOG.debug("self._image_display.image_width(): {0}", self._image_display.image_width())
        MainImageDisplayWindow.__LOG.debug("self._image_display.image_height(): {0}", self._image_display.image_height())

        self.__no_scroll_width = self._image_display.image_width() + self.__frame_width * 2 + self.__margin_width * 2
        self.__scroll_width = self.__no_scroll_width + self.__scroll_bar_width

        self.__no_scroll_height = self._image_display.image_height() + self.__frame_width * 2 + self.__margin_height * 2 + self.__mouse_viewer_height
        self.__scroll_height = self.__no_scroll_height + self.__scroll_bar_width

        MainImageDisplayWindow.__LOG.debug("no scroll w: {0}, h: {1}, scroll w: {2}, h: {3}",
            self.__no_scroll_width, self.__no_scroll_height, self.__scroll_width, self.__scroll_height)

        min_width = self.__no_scroll_width
        min_height = self.__no_scroll_height

        if min_height > self._screen_geometry.height() and min_width > self._screen_geometry.width():
            min_height = self.__oversize_height
            min_width = self.__oversize_width

        elif min_height > self._screen_geometry.height():
            min_width = self.__scroll_width
            min_height = self.__oversize_height

        elif min_width > self._screen_geometry.width():
            min_height = self.__scroll_height
            min_width = self.__oversize_width

        self.setMinimumSize(min_width, min_height)
        MainImageDisplayWindow.__LOG.debug("Window: {0}, {1}", self.width(), self.height())

    def closeEvent(self, event:QCloseEvent):
        self.closed.emit()
        # accepting hides the window
        event.accept()
        # TODO Qt::WA_DeleteOnClose - set to make sure it's deleted???

    # TODO don't need?
    def resizeEvent(self, event:QResizeEvent):
        size = event.size()
        MainImageDisplayWindow.__LOG.debug("Resizing to w: {0}, h: {1}", size.width(), size.height())


class ZoomWidget(QWidget):

    zoom_in = pyqtSignal()
    zoom_out = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__zoom_in_button = QPushButton("+")
        self.__zoom_in_button.setFixedHeight(15)
        self.__zoom_in_button.setFixedWidth(25)
        self.__zoom_in_button.clicked.connect(self.zoom_in)

        self.__zoom_out_button = QPushButton("-")
        self.__zoom_out_button.setFixedHeight(15)
        self.__zoom_out_button.setFixedWidth(25)
        self.__zoom_out_button.clicked.connect(self.zoom_out)

        layout = QHBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.__zoom_in_button)
        layout.addWidget(self.__zoom_out_button)
        self.setLayout(layout)


class ZoomImageDisplayWindow(ImageDisplayWindow):

    __LOG:Logger = LogHelper.logger("ZoomImageDisplayWindow")

    def __init__(self, image:Image, label, qimage_format:QImage.Format,
                screen_geometry:QRect, parent=None):
        super().__init__(image, label, qimage_format, screen_geometry, False, parent)

        self.__zoom_widget = ZoomWidget(self)
        self.__zoom_widget.zoom_in.connect(self.__handle_zoom_in)
        self.__zoom_widget.zoom_out.connect(self.__handle_zoom_out)

        self.__zoom_dock_widget = QDockWidget("Mouse", self)
        self.__zoom_dock_widget.setTitleBarWidget(QWidget(None))
        self.__zoom_dock_widget.setWidget(self.__zoom_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.__zoom_dock_widget)

    @pyqtSlot()
    def __handle_zoom_in(self):
        self._image_display.scale_image(1.5)

    @pyqtSlot()
    def __handle_zoom_out(self):
        self._image_display.scale_image(1/1.5)

