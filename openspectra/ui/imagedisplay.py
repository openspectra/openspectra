#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

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

    def __init__(self, event:QMouseEvent, x_scale:float, y_scale:float):
        super().__init__(None)
        self.__event = event
        self.__pixel_x = floor(event.x() * x_scale)
        self.__pixel_y = floor(event.y() * y_scale)
        self.__pixel_pos = (self.__pixel_x, self.__pixel_y)

    def mouse_event(self) -> QMouseEvent:
        return self.__event

    def pixel_x(self) -> int:
        return self.__pixel_x

    def pixel_y(self) -> int:
        return self.__pixel_y

    def pixel_pos(self) -> (int, int):
        return self.__pixel_pos


class AdjustedAreaSelectedEvent(QObject):

    def __init__(self, x_points:np.ndarray,  x_scale:float,
            y_points:np.ndarray, y_scale:float):
        super().__init__(None)
        self.__x_points = np.floor(x_points * x_scale).astype(np.int16)
        self.__y_points = np.floor(y_points * y_scale).astype(np.int16)

    def x_points(self) -> np.ndarray:
        return self.__x_points

    def y_points(self) -> np.ndarray:
        return self.__y_points


class ImageResizeEvent(QObject):

    def __init__(self, image_size:QSize, viewport_size:QSize):
        super().__init__(None)
        self.__image_size = image_size
        self.__viewport_size = viewport_size

    def image_size(self) -> QSize:
        return self.__image_size

    def viewport_size(self) -> QSize:
        return self.__viewport_size


class ViewZoomChangeEvent(QObject):

    def __init__(self, factor:float, size:QSize):
        super().__init__(None)
        self.__factor = factor
        self.__size = size

    def factor(self) -> float:
        return self.__factor

    def size(self) -> QSize:
        return self.__size


class ViewLocationChangeEvent(QObject):

    def __init__(self, center:QPoint):
        super().__init__(None)
        self.__center = center

    def center(self) -> QPoint:
        return self.__center

    def scale(self, scale_factor:float):
        self.__center *= scale_factor


class ViewChangeEvent(QObject):

    def __init__(self, center:QPoint, size:QSize):
        super().__init__(None)
        self.__center = center
        self.__size = size

    def size(self) -> QSize:
        return self.__size

    def center(self) -> QPoint:
        return self.__center

    def scale(self, scale_factor:float):
        self.__center *= scale_factor
        self.__size *= scale_factor


class MouseCoordinates(QLabel):

    __LOG:Logger = LogHelper.logger("MouseCoordinates")

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(AdjustedMouseEvent)
    def on_mouse_move(self, event:AdjustedMouseEvent):
        # users are accustom to screen coordinates being 1 based
        self.setText(" x: {0} y: {1}".format(
            event.pixel_x() + 1, event.pixel_y() + 1))


class ZoomWidget(QWidget):

    zoom_in = pyqtSignal()
    zoom_out = pyqtSignal()
    reset_zoom = pyqtSignal()

    def __init__(self, parent=None, initial_zoom:float=1.0):
        super().__init__(parent)

        self.__zoom_in_button = QPushButton("+")
        self.__zoom_in_button.setFixedHeight(15)
        self.__zoom_in_button.setFixedWidth(15)
        self.__zoom_in_button.clicked.connect(self.zoom_in)

        self.__zoom_reset_button = QPushButton("1")
        self.__zoom_reset_button.setFixedHeight(15)
        self.__zoom_reset_button.setFixedWidth(15)
        self.__zoom_reset_button.clicked.connect(self.reset_zoom)

        self.__zoom_out_button = QPushButton("-")
        self.__zoom_out_button.setFixedHeight(15)
        self.__zoom_out_button.setFixedWidth(15)
        self.__zoom_out_button.clicked.connect(self.zoom_out)

        self.__factor_label = QLabel()
        self.__factor_label.setFixedHeight(12)
        self.__factor_label.setFixedWidth(40)
        self.set_zoom_label(initial_zoom)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__zoom_in_button)
        layout.addWidget(self.__zoom_reset_button)
        layout.addWidget(self.__zoom_out_button)
        layout.addWidget(self.__factor_label)
        self.setLayout(layout)

    def __del__(self):
        self.__factor_label = None
        self.__zoom_out_button = None
        self.__zoom_in_button = None

    def set_zoom_label(self, new_zoom_factor:float):
        self.__factor_label.setText("{:5.2f}".format(new_zoom_factor))


class ImageLabel(QLabel):

    __LOG:Logger = LogHelper.logger("ImageLabel")

    class Action(Enum):
        Nothing = 0
        Dragging = 1
        Drawing = 2

    # TODO on double click we get both clicked and doubleClicked
    # TODO decide if we need both and fix
    area_selected = pyqtSignal(AdjustedAreaSelectedEvent)
    left_clicked = pyqtSignal(AdjustedMouseEvent)
    right_clicked = pyqtSignal(AdjustedMouseEvent)
    double_clicked = pyqtSignal(AdjustedMouseEvent)
    mouse_move = pyqtSignal(AdjustedMouseEvent)
    locator_moved = pyqtSignal(ViewLocationChangeEvent)

    def __init__(self, location_rect:bool=True, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)

        self.__last_mouse_loc:QPoint = None
        self.__initial_size:QSize = None
        self.__width_scale_factor = 1.0
        self.__height_scale_factor = 1.0

        self.__default_cursor = self.cursor()
        self.__drag_cursor = QCursor(Qt.ClosedHandCursor)
        self.__draw_cursor = QCursor(Qt.CrossCursor)

        if location_rect:
            # Initial size doesn't really matter,
            # it will get adjusted based on the zoom window size
            self.__rect = QRect(0, 0, 50, 50)
        else:
            self.__rect = None

        self.__dragging = False

        self.__polygon:QPolygon = None
        self.__polygon_bounds:QRect = None
        self.__drawing = False

        self.__current_action = ImageLabel.Action.Nothing

    def __del__(self):
        ImageLabel.__LOG.debug("ImageLabel.__del__ called...")
        self.__polygon_bounds = None
        self.__polygon = None

        self.__rect = None

        self.__default_cursor = None
        self.__drag_cursor = None
        self.__draw_cursor = None

        self.__last_mouse_loc = None

    def has_locator(self) -> bool:
        return self.__rect is not None

    def locator_position(self) -> QPoint:
        assert self.__rect is not None
        return self.__unscale_point(self.__rect.center())

    def set_locator_position(self, postion:QPoint):
        # calls to this method should always be in 1 to 1 coordinates
        if self.has_locator():
            #TODO put contraints on it?
            new_position: QPoint = self.__scale_point(postion)
            ImageLabel.__LOG.debug("setting locator position: {0}, scaled pos: {1}", postion, new_position)
            self.__rect.moveCenter(new_position)
            self.update()

    def locator_size(self) -> QSize:
        assert self.__rect is not None
        return self.__unscale_size(self.__rect.size())

    def set_locator_size(self, size:QSize):
        # calls to this method should always be in 1 to 1 coordinates
        if self.has_locator():
            #TODO constraints?
            new_size: QSize = self.__scale_size(size)
            ImageLabel.__LOG.debug("setting locator size: {0}, scaled size: {1}", size, new_size)
            self.__rect.setSize(new_size)
            self.update()

    def clear_selected_area(self):
        self.__polygon_bounds = None
        self.__polygon = None
        self.update()

    def setPixmap(self, pixel_map:QPixmap):
        locator_size:QSize = None
        locator_position:QPoint = None

        if self.has_locator():
            locator_size = self.locator_size()
            locator_position = self.locator_position()

        super().setPixmap(pixel_map)
        ImageLabel.__LOG.debug("super().setPixmap called")
        size = self.pixmap().size()

        if self.__initial_size is not None:
            self.__width_scale_factor = size.width() / self.__initial_size.width()
            self.__height_scale_factor = size.height() / self.__initial_size.height()
            ImageLabel.__LOG.debug("setting image size: {0}, scale factor w: {1}, h: {2}",
                size, self.__width_scale_factor, self.__height_scale_factor)

        # reset locator
        if self.has_locator():
            self.set_locator_size(locator_size)
            self.set_locator_position(locator_position)

        self.setMinimumSize(size)
        self.setMaximumSize(size)

    def changeEvent(self, event:QEvent):
        ImageLabel.__LOG.debug("ImageLabel.changeEvent called...")
        if event.type() == QEvent.ParentChange and self.pixmap() is not None \
                and self.__initial_size is None:
            self.__initial_size = self.pixmap().size()

    def mouseMoveEvent(self, event:QMouseEvent):
        if self.__current_action == ImageLabel.Action.Drawing and self.__polygon is not None:
            # ImageLabel.__LOG.debug("drawing mouse move event, pos: {0}, size: {1}", event.pos(), self.pixmap().size())
            self.__polygon << event.pos()
            self.update()
        elif self.__current_action == ImageLabel.Action.Dragging and \
                self.__last_mouse_loc is not None and self.__rect is not None:
            # ImageLabel.__LOG.debug("dragging mouse move event, pos: {0}, size: {1}", event.pos(), self.pixmap().size())
            center = self.__rect.center()
            center += event.pos() - self.__last_mouse_loc
            self.__rect.moveCenter(center)
            self.__last_mouse_loc = event.pos()
            self.locator_moved.emit(ViewLocationChangeEvent(self.__unscale_point(center)))
            self.update()
        else:
            # don't emit pixel locations when drawing or dragging.  It doesn't
            # really make sense and for some reason when the mouse is held down
            # we get event even after we are no longer on the image creating
            # out of range problems
            # ImageLabel.__LOG.debug("mouse move event, pos: {0}, size: {1}", event.pos(), self.pixmap().size())
            adjusted_move = self.__create_adjusted_mouse_event(event)
            self.mouse_move.emit(adjusted_move)

    def mousePressEvent(self, event:QMouseEvent):
        # only expect right clicks here due to event filter
        ImageLabel.__LOG.debug("mousePressEvent left: {0} or right: {1}",
            event.button() == Qt.LeftButton, event.button() == Qt.RightButton)
        self.right_clicked.emit(self.__create_adjusted_mouse_event(event))

    def mouseReleaseEvent(self, event:QMouseEvent):
        ImageLabel.__LOG.debug("mouseReleaseEvent left: {0} or right: {1}",
            event.button() == Qt.LeftButton, event.button() == Qt.RightButton)

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

        # Then it's a left click
        elif self.__last_mouse_loc is not None:
            self.left_clicked.emit(self.__create_adjusted_mouse_event(event))

        self.__last_mouse_loc = None

    def mouseDoubleClickEvent(self, event:QMouseEvent):
        ImageLabel.__LOG.debug("mouseDoubleClickEvent")
        self.double_clicked.emit(self.__create_adjusted_mouse_event(event))

    # TODO don't need??
    def resize(self, size:QSize):
        ImageLabel.__LOG.debug("Resizing to w: {0}, h: {1}", size.width(), size.height())
        super().resize(size)

    def eventFilter(self, object:QObject, event:QEvent):
        if isinstance(event, QMouseEvent):
            image_size:QSize = self.pixmap().size()
            if event.x() >= image_size.width() or event.y() >= image_size.height():
                # suppress mouse events outside the image,
                # can happen when mouse button is held while moving mouse
                return True

            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # TODO this has to account for scaling
                self.__last_mouse_loc = event.pos()
                QTimer.singleShot(300, self.__pressed)
                # event was handled
                return True

            # Mask right clicks from the mouse release handler
            if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.RightButton:
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

    def __scale_point(self, point:QPoint) -> QPoint:
        new_point:QPoint = QPoint(point)
        if self.__width_scale_factor != 1.0:
            new_point.setX(floor(new_point.x() * self.__width_scale_factor))

        if self.__height_scale_factor != 1.0:
            new_point.setY(floor(new_point.y() * self.__height_scale_factor))

        return new_point

    def __scale_size(self, size:QSize) -> QSize:
        new_size: QSize = QSize(size)
        if self.__width_scale_factor != 1.0:
            new_size.setWidth(floor(new_size.width() * self.__width_scale_factor))

        if self.__height_scale_factor != 1.0:
            new_size.setHeight(floor(new_size.height() * self.__height_scale_factor))

        return new_size

    def __unscale_point(self, point:QPoint) -> QPoint:
        new_point:QPoint = QPoint(point)
        if self.__width_scale_factor != 1.0:
            new_point.setX(floor(new_point.x() / self.__width_scale_factor))

        if self.__height_scale_factor != 1.0:
            new_point.setY(floor(new_point.y() / self.__height_scale_factor))

        return new_point

    def __unscale_size(self, size:QSize) -> QSize:
        new_size: QSize = QSize(size)
        if self.__width_scale_factor != 1.0:
            new_size.setWidth(floor(new_size.width() / self.__width_scale_factor))

        if self.__height_scale_factor != 1.0:
            new_size.setHeight(floor(new_size.height() / self.__height_scale_factor))

        return new_size

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

            # take only the points that were inside the polygon
            x = x[~x.mask]
            y = y[~y.mask]
            self.area_selected.emit(AdjustedAreaSelectedEvent(
                x, 1 / self.__width_scale_factor, y, 1 / self.__height_scale_factor))

    def __pressed(self):
        # ImageLabel.__LOG.debug("press called, last_mouse_loc: {0}", self.__last_mouse_loc)
        if self.__last_mouse_loc is not None:
            if self.__rect is not None and self.__rect.contains(self.__last_mouse_loc):
                self.__current_action = ImageLabel.Action.Dragging
                self.setCursor(self.__drag_cursor)
                # ImageLabel.__LOG.debug("press called, drag start")
            else:
                self.__current_action = ImageLabel.Action.Drawing
                self.setCursor(self.__draw_cursor)
                self.__polygon = QPolygon()
                # ImageLabel.__LOG.debug("press called, draw start")

    def __create_adjusted_mouse_event(self, event:QMouseEvent):
        # TODO seems to be a bit off for large images when scaled down to fit???
        # TODO not sure this can work when scaling < 1??
        return AdjustedMouseEvent(event, 1 / self.__width_scale_factor, 1 / self.__height_scale_factor)

    # TODO Get aspect ratio here?
    # def setPixmap(self, qPixmap:QPixmap):
    #     super().setPixmap(qPixmap)

    # def heightForWidth(self, width):
    #     print("heightForWidth with: ", width)
    #     return int(width * self.__ratio)

    # TODO I suspect these don't do anyting becuase they are for layouts to use I think
    # def sizeHint(self):
    #     if self.pixmap() is not None:
    #         return self.pixmap().size()

    # TODO I suspect these don't do anyting becuase they are for layouts to use I think
    # def minimumSizeHint(self):
    #     if self.pixmap() is not None:
    #         return self.pixmap().size()

    # def minimumHeight(self):
    #     return self.__perferred_size.height()

    # def minimumSize(self):
    #     return self.__perferred_size

    # TODO remove is not used
    def resizeEvent(self, event:QResizeEvent):
        ImageLabel.__LOG.debug("Resize to {0}, maxSize: {1}, minSize: {2}, minSizeHint: {3}",
            event.size(), self.maximumSize(), self.minimumSize(), self.minimumSizeHint())


class ImageDisplay(QScrollArea):

    __LOG:Logger = LogHelper.logger("ImageDisplay")

    area_selected = pyqtSignal(AdjustedAreaSelectedEvent)
    left_clicked = pyqtSignal(AdjustedMouseEvent)
    right_clicked = pyqtSignal(AdjustedMouseEvent)
    mouse_move = pyqtSignal(AdjustedMouseEvent)
    image_resized = pyqtSignal(ImageResizeEvent)
    viewport_changed = pyqtSignal(ViewChangeEvent)
    locator_moved = pyqtSignal(ViewLocationChangeEvent)
    viewport_scrolled = pyqtSignal(ViewLocationChangeEvent)

    def __init__(self, image:Image, qimage_format:QImage.Format=QImage.Format_Grayscale8,
            location_rect:bool=True, parent=None):
        super().__init__(parent)

        # TODO make settable prop?
        self.__margin_width = 4
        self.__margin_height = 4

        # TODO do we need to hold the data itself?
        self.__image = image
        self.__qimage_format = qimage_format

        self.__image_label = ImageLabel(location_rect, self)
        self.__image_label.setBackgroundRole(QPalette.Base)
        self.__image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.__image_label.setMouseTracking(True)
        self.__image_label.area_selected.connect(self.area_selected)
        self.__image_label.left_clicked.connect(self.left_clicked)
        self.__image_label.right_clicked.connect(self.right_clicked)
        self.__image_label.double_clicked.connect(self.__double_click_handler)
        self.__image_label.mouse_move.connect(self.mouse_move)
        self.__image_label.locator_moved.connect(self.locator_moved)

        self.__last_scrollbar_action:int = -1
        self.horizontalScrollBar().valueChanged.connect(self.__handle_horizontal_bar_changed)
        self.horizontalScrollBar().actionTriggered.connect(self.__handle_bar_action)
        self.verticalScrollBar().valueChanged.connect(self.__handle_vertical_bar_changed)
        self.verticalScrollBar().actionTriggered.connect(self.__handle_bar_action)

        self.setBackgroundRole(QPalette.Dark)
        self.__display_image()

    def __del__(self):
        # TODO ??
        ImageDisplay.__LOG.debug("ImageDisplay.__del__ called...")
        self.__pix_map = None
        self.__qimage = None
        self.__image_size = None
        self.__image_label = None
        self.__image = None

    @pyqtSlot(int)
    def __handle_bar_action(self, action:int):
        # Action are triggered by user interactions with the scroll bars so capture
        # the action when it happens so we can use it to filter scroll bar value changed events
        # ImageDisplay.__LOG.debug("bar action handled: {0}", action)
        self.__last_scrollbar_action = action

    @pyqtSlot(int)
    def __handle_horizontal_bar_changed(self, value:int):
        # Events here when the user moves the scrollbar or we call setValue() on the scrollbar
        # Only emit if the an action was set meaning it came from a user interaction rather than a call to setValue
        # ImageDisplay.__LOG.debug("Horiz scroll change to: {0}, last action: {1}", value, self.__last_scrollbar_action)
        if self.__last_scrollbar_action != -1:
            self.viewport_scrolled.emit(ViewLocationChangeEvent(self.get_view_center()))
            self.__last_scrollbar_action = -1

    @pyqtSlot(int)
    def __handle_vertical_bar_changed(self, value:int):
        # Events here when the user moves the scrollbar or we call setValue() on the scrollbar
        # Only emit if the an action was set meaning it came from a user interaction rather than a call to setValue
        # ImageDisplay.__LOG.debug("Vert scroll change to: {0}, last action: {1}", value, self.__last_scrollbar_action)
        if self.__last_scrollbar_action != -1:
            self.viewport_scrolled.emit(ViewLocationChangeEvent(self.get_view_center()))
            self.__last_scrollbar_action = -1

    def __display_image(self):
        # height and width of the image in pixels or the 1 to 1 size
        image_height, image_width = self.__image.image_shape()
        self.__image_size = QSize(image_width, image_height)

        self.__qimage:QImage = QImage(self.__image.image_data(), self.__image_size.width(),
            self.__image_size.height(), self.__image.bytes_per_line(), self.__qimage_format)

        self.__pix_map:QPixmap = QPixmap.fromImage(self.__qimage)
        self.__image_label.setPixmap(self.__pix_map)
        self.setWidget(self.__image_label)

        # small margins to give a little extra room so the cursor doesn't change too soon.
        self.setViewportMargins(self.__margin_width, self.__margin_height,
            self.__margin_width, self.__margin_height)

        self.show()

    # TODO not sure we need this but keep it for the example for now
    @pyqtSlot(AdjustedMouseEvent)
    def __double_click_handler(self, event:AdjustedMouseEvent):
        # TODO remove?
        ImageDisplay.__LOG.debug("Double clicked x: {0} y: {1}",
            event.pixel_x() + 1, event.pixel_y() + 1)

    def __set_pixmap(self):
        self.__image_label.setPixmap(self.__pix_map)
        new_size = self.__pix_map.size()
        ImageDisplay.__LOG.debug("setting image size: {0}", new_size)
        self.resize(new_size)
        self.image_resized.emit(ImageResizeEvent(new_size, self.viewport().size()))

    def __update_scroll_bars(self, old_viewport_size:QSize, new_viewport_size:QSize):
        doc_width = self.__image_label.size().width()
        if new_viewport_size.width() > doc_width:
            # doing this eliminates flicker when viewport is larger than doc
            if self.horizontalScrollBar().maximum() != 0:
                self.horizontalScrollBar().setMaximum(0)
        elif old_viewport_size.width() != new_viewport_size.width():
            new_max_width =  doc_width - new_viewport_size.width()
            new_horiz_step = doc_width - new_max_width

            ImageDisplay.__LOG.debug("Resizing horizontal scroll max to {0}, step {1}, doc size {2}",
                new_max_width, new_horiz_step, self.__image_label.size().width())
            self.horizontalScrollBar().setPageStep(new_horiz_step)
            self.horizontalScrollBar().setMaximum(new_max_width)

        doc_height = self.__image_label.height()
        if new_viewport_size.height() > doc_height:
            if self.verticalScrollBar().maximum() != 0:
                self.verticalScrollBar().setMaximum(0)
        elif old_viewport_size.height() != new_viewport_size.height():
            new_max_height = doc_height - new_viewport_size.height()
            new_vert_step = doc_height - new_max_height

            ImageDisplay.__LOG.debug("Resizing vertical scroll max to {0}, step {1}, doc size {2}",
                new_max_height, new_vert_step, self.__image_label.size().width())
            self.verticalScrollBar().setPageStep(new_vert_step)
            self.verticalScrollBar().setMaximum(new_max_height)

    def get_view_center(self) -> QPoint:
        # x is horizontal scroll bar, y is vertical scroll bar
        x = floor(self.horizontalScrollBar().pageStep()/2) + self.horizontalScrollBar().value()
        y = floor(self.verticalScrollBar().pageStep()/2) + self.verticalScrollBar().value()
        return QPoint(x, y)

    def center_in_viewport(self, center:QPoint):
        # x is horizontal scroll bar, y is vertical scroll bar
        new_x = center.x()
        new_y = center.y()
        if 0 < new_x <= self.__image_label.size().width() and \
                0 < new_y <= self.__image_label.size().height():
            h_val = new_x - floor(self.horizontalScrollBar().pageStep()/2)
            if h_val < 0:
                h_val = 0

            v_val = new_y - floor(self.verticalScrollBar().pageStep()/2)
            if v_val < 0:
                v_val = 0

            self.horizontalScrollBar().setValue(h_val)
            self.verticalScrollBar().setValue(v_val)

    def locator_position(self) -> QPoint:
        return self.__image_label.locator_position()

    def set_locator_position(self, postion:QPoint):
        self.__image_label.set_locator_position(postion)

    def locator_size(self) -> QSize:
        return self.__image_label.locator_size()

    def set_locator_size(self, size:QSize):
        self.__image_label.set_locator_size(size)

    def refresh_image(self):
        # TODO do I need to del the old QImage & QPixmap object???
        # TODO I think they should be garbage collected once the ref is gone?
        self.__display_image()

    def clear_selected_area(self):
        self.__image_label.clear_selected_area()

    def scale_image(self, factor:float):
        """Changes the scale relative to the original image size maintaining aspect ratio.
        The image is reset from the original QImage each time to prevent degradation"""
        ImageDisplay.__LOG.debug("scaling image by: {0}", factor)
        pix_map = QPixmap.fromImage(self.__qimage)
        if factor != 1.0:
            new_size = self.__image_size * factor
            pix_map = pix_map.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.__pix_map = pix_map
        self.__set_pixmap()

    def scale_to_size(self, new_size:QSize):
        """Scale the image to the given size maintaining aspect ratio. See http://doc.qt.io/qt-5/qpixmap.html#scaled
        for information about how the aspect ratio is handled using Qt.KeepAspectRatio
        Do not call repeatedly without a call to reset_size as image will blur with repeated scaling"""
        self.__pix_map = self.__pix_map.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        ImageDisplay.__LOG.debug("scaling to size: {0}", new_size)
        self.__set_pixmap()

    def scale_to_height(self, height:int):
        """Scale the image to the given height maintaining aspect ratio.
        Do not call repeatedly without a call to reset_size as image will blur with repeated scaling"""

        if self.__image_label.has_locator():
            ImageDisplay.__LOG.debug("scale_to_height locator size: {0}, pos: {1}", self.__image_label.locator_size(), self.__image_label.locator_position())

        self.__pix_map = self.__pix_map.scaledToHeight(height, Qt.SmoothTransformation)
        ImageDisplay.__LOG.debug("scaling to height: {0}", height)
        self.__set_pixmap()

    def scale_to_width(self, width:int):
        """Scale the image to the given width maintaining aspect ratio.
        Do not call repeatedly without a call to reset_size as image will blur with repeated scaling"""
        self.__pix_map = self.__pix_map.scaledToWidth(width, Qt.SmoothTransformation)
        ImageDisplay.__LOG.debug("scaling to width: {0}", width)
        self.__set_pixmap()

    def reset_size(self):
        """reset the image size to 1 to 1"""
        # Reload the image, repeated scaling blurs the image
        if self.__image_label.has_locator():
            ImageDisplay.__LOG.debug("reset_size locator size: {0}, pos: {1}", self.__image_label.locator_size(),
                self.__image_label.locator_position())

        self.__pix_map = QPixmap.fromImage(self.__qimage)
        self.__set_pixmap()

    def original_image_width(self) -> int:
        """image width in pixels at 1 to 1"""
        return self.__image_size.width()

    def image_width(self) -> int:
        """current image width"""
        return self.__pix_map.size().width()

    def original_image_height(self) -> int:
        """image height in pixels at 1 to 1"""
        return self.__image_size.height()

    def image_height(self) -> int:
        """current image height"""
        return self.__pix_map.size().height()

    def margin_width(self) -> int:
        return self.__margin_width

    def margin_height(self) -> int:
        return self.__margin_height

    def resize(self, size:QSize):
        ImageDisplay.__LOG.debug("Resizing widget to: {0}", size)
        # This adjust my size and the display widget and causes the scroll bars to update properly
        self.widget().resize(size)
        ImageDisplay.__LOG.debug("After resize widget my size: {0}, viewport: {1}, widget: {2}",
            self.size(), self.viewport().size(), self.widget().size())

    def resizeEvent(self, event:QResizeEvent):
        # Note that this only triggers on a user resize of the containing window, not when image size changes
        # It gets resize events from the framework when the user changes the window size before the Window gets it
        # old size and event size here are viewport sizes
        ImageDisplay.__LOG.debug("resizeEvent old size: {0}, new size: {1}", event.oldSize(), event.size())
        ImageDisplay.__LOG.debug("resizeEvent viewport size: {0}", self.viewport().size())

        # adjust the scrollbars
        self.__update_scroll_bars(event.oldSize(), event.size())
        self.viewport_changed.emit(ViewChangeEvent(self.get_view_center(), event.size()))

    # TODO test only
    def size(self):
        ImageDisplay.__LOG.debug("ImageLabel size: {0}", self.__image_label.size())
        return super().size()


class ImageDisplayWindow(QMainWindow):

    __LOG:Logger = LogHelper.logger("ImageDisplayWindow")

    pixel_selected = pyqtSignal(AdjustedMouseEvent)
    mouse_moved = pyqtSignal(AdjustedMouseEvent)
    area_selected = pyqtSignal(AdjustedAreaSelectedEvent)

    def __init__(self, image:Image, label, qimage_format:QImage.Format,
                screen_geometry:QRect, location_rect:bool=True, parent=None):
        super().__init__(parent)
        # TODO do we need to hold the data itself?
        self.__image = image
        self._image_display = ImageDisplay(self.__image, qimage_format, location_rect, self)
        self.__init_ui(label)

        self._margin_width = self._image_display.margin_width()
        self._margin_height = self._image_display.margin_height()
        ImageDisplayWindow.__LOG.debug("margin_width: {0}, margin_height {1}", self._margin_width, self._margin_height)

        self._scroll_bar_width = QApplication.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        ImageDisplayWindow.__LOG.debug("scroll_bar_width: {0}", self._scroll_bar_width)

        self._title_bar_height = QApplication.style().pixelMetric(QStyle.PM_TitleBarHeight)
        ImageDisplayWindow.__LOG.debug("title_bar_height: {0}", self._title_bar_height)

        self._frame_width = QApplication.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        ImageDisplayWindow.__LOG.debug("frame_width: {0}", self._frame_width)

        self._screen_geometry = screen_geometry
        ImageDisplayWindow.__LOG.debug("screen geometry: {0}", self._screen_geometry)

    def __init_ui(self, label):
        self.setWindowTitle(label)

        self.setCentralWidget(self._image_display)
        self._image_display.setAlignment(Qt.AlignHCenter)

        self._mouse_widget = QDockWidget("Mouse", self)
        self._mouse_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self._mouse_widget.setTitleBarWidget(QWidget(None))
        self._mouse_viewer = MouseCoordinates()
        # TODO make height configurable???
        # set to fixed height so we know how to layout the image display window
        self._mouse_viewer.setFixedHeight(16)

        self._image_display.mouse_move.connect(self._mouse_viewer.on_mouse_move)
        self._image_display.left_clicked.connect(self.pixel_selected)
        self._image_display.mouse_move.connect(self.mouse_moved)
        self._image_display.area_selected.connect(self.area_selected)

        self._mouse_widget.setWidget(self._mouse_viewer)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._mouse_widget)

    def __del__(self):
        # TODO???
        ImageDisplayWindow.__LOG.debug("ImageDisplayWindow.__del__ called...")
        self._title_bar_height = None
        self._margin_height = None
        self._margin_width = None
        self._frame_width = None
        self._scroll_bar_width = None

        self._image_display = None
        self.__image = None
        #TODO self.____mouseWidget = None Or does the window system handle this?
        self._screen_geometry = None

    @pyqtSlot()
    def handle_stats_closed(self):
        self._image_display.clear_selected_area()

    def refresh_image(self):
        self._image_display.refresh_image()

    # TODO remove if not needed
    # def resizeEvent(self, event:QResizeEvent):
        # size = event.size()
        # size -= QSize(10, 20)
        # self.__image_display.resize(size)


class ZoomImageDisplayWindow(ImageDisplayWindow):

    __LOG:Logger = LogHelper.logger("ZoomImageDisplayWindow")

    zoom_changed = pyqtSignal(ViewZoomChangeEvent)
    location_changed = pyqtSignal(ViewLocationChangeEvent)
    view_changed = pyqtSignal(ViewChangeEvent)

    def __init__(self, image:Image, label, qimage_format:QImage.Format,
            screen_geometry:QRect, parent=None):
        super().__init__(image, label, qimage_format, screen_geometry, False, parent)

        self.__last_display_center:QPoint = None

        self._image_display.image_resized.connect(self.__handle_image_resize)
        self._image_display.viewport_changed.connect(self.__handle_view_changed)
        self._image_display.viewport_scrolled.connect(self.__handle_image_scroll)

        # TODO for testing only, remove if not used otherwise
        self._image_display.right_clicked.connect(self.__handle_right_click)

        self.__zoom_factor = 1.0
        self.__zoom_widget = ZoomWidget(self, self.__zoom_factor)
        self.__zoom_widget.zoom_in.connect(self.__handle_zoom_in)
        self.__zoom_widget.zoom_out.connect(self.__handle_zoom_out)
        self.__zoom_widget.reset_zoom.connect(self.__handle_zoom_reset)

        self.__zoom_dock_widget = QDockWidget("Mouse", self)
        self.__zoom_dock_widget.setTitleBarWidget(QWidget(None))
        self.__zoom_dock_widget.setWidget(self.__zoom_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.__zoom_dock_widget)

        # TODO make it so min size provides a veiwport of 150 x 150
        self.__minimum_size = QSize(150, 150)
        self.setMinimumSize(self.__minimum_size)

        # TODO temporarily initial size setting, figure out a more sensible way to determine initial size
        self.__nom_size = QSize(400, 350)
        self.resize(self.__nom_size)

        self.__zoom_widget.setFixedHeight(17)
        # TODO forcing to above 17 makes it looks better but now viewport is off by 7 but it looks like it 17
        self.__dock_height = self.__zoom_widget.height()
        ZoomImageDisplayWindow.__LOG.debug("zoom widget height: {0}", self.__dock_height)

    @pyqtSlot()
    def __handle_zoom_in(self):
        # TODO multiplier should be settable
        self.__last_display_center = self._image_display.get_view_center() / self.__zoom_factor
        self.__zoom_factor *= 1.5
        self.__set_zoom()

    @pyqtSlot()
    def __handle_zoom_out(self):
        # TODO multiplier should be settable
        self.__last_display_center = self._image_display.get_view_center() / self.__zoom_factor
        self.__zoom_factor *= 1/1.5
        self.__set_zoom()

    @pyqtSlot()
    def __handle_zoom_reset(self):
        self.__last_display_center = self._image_display.get_view_center() / self.__zoom_factor
        self.__zoom_factor = 1.0
        self.__set_zoom()

    @pyqtSlot(ImageResizeEvent)
    def __handle_image_resize(self, event:ImageResizeEvent):
        """Receives notice of the new image size"""
        ZoomImageDisplayWindow.__LOG.debug("image resize event, new size: {0}, last center: {1}, new viewport size: {2}",
            event.image_size(), self.__last_display_center, event.viewport_size())
        if self.__last_display_center is not None:
            new_center:QPoint = self.__last_display_center * self.__zoom_factor
            ZoomImageDisplayWindow.__LOG.debug("new center: {0}", new_center)
            self._image_display.center_in_viewport(new_center)
            self.zoom_changed.emit(ViewZoomChangeEvent(self.__zoom_factor, event.viewport_size()/self.__zoom_factor))

    # TODO for testing only, remove if not used otherwise
    @pyqtSlot(AdjustedMouseEvent)
    def __handle_right_click(self, event:AdjustedMouseEvent):
        ZoomImageDisplayWindow.__LOG.debug("My size: {0}", self.size())
        ZoomImageDisplayWindow.__LOG.debug("ImageDisplay size: {0}", self._image_display.size())
        ZoomImageDisplayWindow.__LOG.debug("ImageDisplay.viewport size: {0}", self._image_display.viewport().size())

    def __handle_view_changed(self, event:ViewChangeEvent):
        # Handle when viewport is resized
        event.scale(1 / self.__zoom_factor)
        self.view_changed.emit(event)

    @pyqtSlot(ViewLocationChangeEvent)
    def __handle_image_scroll(self, event:ViewLocationChangeEvent):
        # Handle when scrollbars move
        ZoomImageDisplayWindow.__LOG.debug("image scroll handled, center: {0}", event.center())
        event.scale(1 / self.__zoom_factor)
        self.location_changed.emit(event)

    def __set_zoom(self):
        self._image_display.scale_image(self.__zoom_factor)
        self.__zoom_widget.set_zoom_label(self.__zoom_factor)

    # TODO this didn't quite work, height was off by 7 pixels, fix or remove
    # TODO perhaps there's a better way to choose an initial size???
    # def __size_for_viewport_size(self, size:QSize):
    #     ZoomImageDisplayWindow.__LOG.debug("sizing for viewport size: {0}", size)
    #     new_width = size.width() + self._frame_width * 2 + self._margin_width * 2
    #     if self._image_display.image_width() > size.width():
    #         new_width += self._scroll_bar_width
    #
    #     new_height = size.height() + self._title_bar_height + self.__dock_height + \
    #                  self._margin_height * 2 + self._frame_width * 2
    #     if self._image_display.height() > size.height():
    #         new_height += self._scroll_bar_width
    #
    #     if new_width > self._screen_geometry.width():
    #         # TODO then what? adjust it
    #         pass
    #
    #     if new_width > self.__minimum_size.width():
    #         # TODO then what? adjust it
    #         pass
    #
    #     if new_height > self._screen_geometry.height():
    #         # TODO then what??  adjust it
    #         pass
    #
    #     if new_height > self.__minimum_size.height():
    #         # TODO then what??  adjust it
    #         pass
    #
    #     new_size = QSize(new_width, new_height)
    #     ZoomImageDisplayWindow.__LOG.debug("window size needed: {0}", new_size)
    #     self.resize(new_size)

    def __center_in_viewport(self, center:QPoint):
        # TODO Logging here is huge overkill
        # ZoomImageDisplayWindow.__LOG.debug("centering view to: {0}", center)
        self._image_display.center_in_viewport(center)

    @pyqtSlot(ViewLocationChangeEvent)
    def handle_location_changed(self, event:ViewLocationChangeEvent):
        # Handles when the locator is moved in the main window
        self.__center_in_viewport(event.center() * self.__zoom_factor)

    # TODO for testing only, remove if not used otherwise
    def resizeEvent(self, event:QResizeEvent):
        ZoomImageDisplayWindow.__LOG.debug("Resize to {0}", event.size())


class MainImageDisplayWindow(ImageDisplayWindow):

    __LOG:Logger = LogHelper.logger("MainImageDisplayWindow")

    closed = pyqtSignal()
    view_location_changed = pyqtSignal(ViewLocationChangeEvent)

    def __init__(self, image:Image, label, qimage_format:QImage.Format,
                screen_geometry:QRect, parent=None):
        super().__init__(image, label, qimage_format, screen_geometry, True, parent)
        self._image_display.right_clicked.connect(self.__handle_right_click)
        self._image_display.image_resized.connect(self.__handle_image_resize)
        self._image_display.locator_moved.connect(self.__handle_location_changed)

        # Prevents context menus from showing on right click
        # Only way I could find to prevent the dock widget context menu from
        # appearing on right click event even though it doesn't seem
        # it actually makes up to this window
        self.setContextMenuPolicy(Qt.PreventContextMenu)

        self.__calculate_sizes()

    def __del__(self):
        self.__fit_to_size = None
        self.__oversize_height = None
        self.__oversize_width = None
        self.__mouse_viewer_height = None

    def __calculate_sizes(self):
        self.__mouse_viewer_height = self._mouse_viewer.height()
        MainImageDisplayWindow.__LOG.debug("mouse_viewer_height: {0}", self.__mouse_viewer_height)

        self.__oversize_width = self._screen_geometry.width() - self._frame_width * 2
        self.__oversize_height = self._screen_geometry.height() - self._title_bar_height

        # figure out how much screen space we have for size image to fit
        fit_height = self._screen_geometry.height() - self._title_bar_height - \
                     self.__mouse_viewer_height - self._frame_width * 2 - self._margin_height * 2
        fit_width = self._screen_geometry.width() - self._frame_width * 2 - self._margin_width * 2

        # This is the image size we'll ask for when we want to fit to available screen
        self.__fit_to_size = QSize(fit_width, fit_height)
        MainImageDisplayWindow.__LOG.debug("fit w: {0}, h: {1}", self.__fit_to_size.width(), self.__fit_to_size.height())

        self.__init_size()

    def __init_size(self):
        MainImageDisplayWindow.__LOG.debug("self._image_display.image_width(): {0}", self._image_display.original_image_width())
        MainImageDisplayWindow.__LOG.debug("self._image_display.image_height(): {0}", self._image_display.original_image_height())
        self.__set_for_image_size(QSize(self._image_display.original_image_width(), self._image_display.original_image_height()))
        self.__is_one_to_one = True

    def __set_for_image_size(self, size:QSize):
        MainImageDisplayWindow.__LOG.debug("Setting size for image size: {0}", size)
        self.__no_scroll_width = size.width() + self._frame_width * 2 + self._margin_width * 2
        self.__scroll_width = self.__no_scroll_width + self._scroll_bar_width

        self.__no_scroll_height = size.height() + self._frame_width * 2 + self._margin_height * 2 + self.__mouse_viewer_height
        self.__scroll_height = self.__no_scroll_height + self._scroll_bar_width

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
        self.resize(min_width, min_height)

    @pyqtSlot(AdjustedMouseEvent)
    def __handle_right_click(self, event:AdjustedMouseEvent):
        MainImageDisplayWindow.__LOG.debug("Got right click!")
        if self.__is_one_to_one:
            self.__is_one_to_one = False
            if self._image_display.height() > self.__fit_to_size.height() and self._image_display.width() > self.__fit_to_size.width():
                self._image_display.scale_to_size(self.__fit_to_size)
            elif self._image_display.height() > self.__fit_to_size.height():
                self._image_display.scale_to_height(self.__fit_to_size.height())
            elif self._image_display.width() > self.__fit_to_size.width():
                self._image_display.scale_to_width(self.__fit_to_size.width())
            else:
                self.__is_one_to_one = True
        else:
            self._image_display.reset_size()
            self.__is_one_to_one = True

    @pyqtSlot(ImageResizeEvent)
    def __handle_image_resize(self, event:ImageResizeEvent):
        MainImageDisplayWindow.__LOG.debug("image resize event, new image size: {0}, viewport size: {1}",
            event.image_size(), event.viewport_size())
        self.__set_for_image_size(event.image_size())
        MainImageDisplayWindow.__LOG.debug("window new size: {0}", self.size())

    @pyqtSlot(ViewZoomChangeEvent)
    def __handle_zoom_changed(self, event:ViewZoomChangeEvent):
        # Handle a zoom change in the zoom window
        MainImageDisplayWindow.__LOG.debug("new zoom factor: {0}, size: {1}", event.factor(), event.size())
        current_location = self._image_display.locator_position()
        self._image_display.set_locator_size(event.size())
        self._image_display.set_locator_position(current_location)

    @pyqtSlot(ViewLocationChangeEvent)
    def __handle_zoom_window_location_changed(self, event:ViewLocationChangeEvent):
        # Handle image being scrolled in the zoom window
        self._image_display.set_locator_position(event.center())

    @pyqtSlot(ViewLocationChangeEvent)
    def __handle_location_changed(self, event:ViewLocationChangeEvent):
        # Handle locator moves in my ImageDisplay
        # TODO if nothing else needs to be done, hook signal to signal, logging is huge overkill here
        # MainImageDisplayWindow.__LOG.debug("handle view location to: {0}", event.center())
        self.view_location_changed.emit(event)

    @pyqtSlot(ViewChangeEvent)
    def __handle_view_changed(self, event:ViewChangeEvent):
        MainImageDisplayWindow.__LOG.debug("handle view changed to size: {0}, loc: {1}", event.size(), event.center())
        self._image_display.set_locator_size(event.size())
        self._image_display.set_locator_position(event.center())

    def connect_zoom_window(self, window:ZoomImageDisplayWindow):
        window.zoom_changed.connect(self.__handle_zoom_changed)
        window.location_changed.connect(self.__handle_zoom_window_location_changed)
        window.view_changed.connect(self.__handle_view_changed)
        self.view_location_changed.connect(window.handle_location_changed)

    def closeEvent(self, event:QCloseEvent):
        self.closed.emit()
        # accepting hides the window
        event.accept()
        # TODO Qt::WA_DeleteOnClose - set to make sure it's deleted???

    # TODO don't need?
    def resizeEvent(self, event:QResizeEvent):
        size = event.size()
        # MainImageDisplayWindow.__LOG.debug("Resizing to w: {0}, h: {1}", size.width(), size.height())
