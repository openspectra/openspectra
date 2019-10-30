#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.

import itertools
import time
from enum import Enum
from math import floor
from typing import List

from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QObject, QTimer, QSize, pyqtSlot, QRect, QPoint
from PyQt5.QtGui import QPalette, QImage, QPixmap, QMouseEvent, QResizeEvent, QCloseEvent, QPaintEvent, QPainter, \
    QPolygon, QCursor, QColor, QBrush, QPainterPath, QPolygonF
from PyQt5.QtWidgets import QScrollArea, QLabel, QSizePolicy, QMainWindow, QDockWidget, QWidget, QPushButton, \
    QHBoxLayout, QApplication, QStyle

import numpy as np
from numpy import ma

from openspectra.image import Image, BandDescriptor
from openspectra.openspecrtra_tools import RegionOfInterest
from openspectra.utils import LogHelper, Logger, Singleton


class ColorPicker(metaclass=Singleton):

    def __init__(self):
        self.__colors = [Qt.red, Qt.green, Qt.blue, Qt.cyan, Qt.yellow,
            Qt.magenta, Qt.gray, Qt.darkRed, Qt.darkGreen, Qt.darkBlue,
            Qt.darkCyan, Qt.darkMagenta, Qt.darkYellow, Qt.darkGray,
            Qt.lightGray]
        self.__index = 0

    def current_color(self) -> QColor:
        return self.__colors[self.__index]

    def next_color(self) -> QColor:
        self.__index += 1
        if self.__index >= len(self.__colors):
            self.reset()
        return self.__colors[self.__index]

    def reset(self):
        self.__index = 0


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


class RegionDisplayItem(QObject):

    toggled = pyqtSignal(QObject)
    closed = pyqtSignal(QObject)

    def __init__(self, x_zoom_factor: float, y_zoom_factor:float, color:QColor, is_on:bool,
            painter_path:QPainterPath=None, points:List[QPoint]=None):
        super().__init__(None)
        self.__x_zoom_factor = x_zoom_factor
        self.__y_zoom_factor = y_zoom_factor
        self.__color = color
        self.__is_on = is_on
        self.__painter_path = painter_path
        self.__points = points

    def painter_path(self) -> QPainterPath:
        return self.__painter_path

    def points(self) -> List[QPoint]:
        return self.__points

    def append_points(self, points:List[QPoint]):
        self.__points.extend(points)

    def color(self) -> QColor:
        return self.__color

    def is_on(self) -> bool:
        return self.__is_on

    def set_is_on(self, is_on:bool):
        self.__is_on = is_on
        self.toggled.emit(self)

    def close(self):
        self.closed.emit(self)

    def x_zoom_factor(self) -> float:
        return self.__x_zoom_factor

    def y_zoom_factor(self) -> float:
        return self.__y_zoom_factor


class WindowCloseEvent(QObject):

    def __init__(self, target:QMainWindow):
        super().__init__(None)
        self.__target = target

    def target(self) -> QMainWindow:
        return self.__target


class AreaSelectedEvent(QObject):

    def __init__(self, region:RegionOfInterest, display_item:RegionDisplayItem):
        super().__init__(None)
        self.__region = region
        self.__display_item = display_item

    def region(self) -> RegionOfInterest:
        return self.__region

    def display_item(self) -> RegionDisplayItem:
        return self.__display_item


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
        self.setText(" sample: {0} line: {1}".format(
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

    def set_zoom_label(self, new_zoom_factor:float):
        self.__factor_label.setText("{:5.2f}".format(new_zoom_factor))


class ReversePixelCalculator():
    """For a given pixel selected on a zoomed in image get_points returns
    all of the pixels that should be drawn on the zoomed image to cover
    the same area as would be in the 1 to 1 image"""

    __LOG: Logger = LogHelper.logger("ReversePixelCalculator")

    def __init__(self, x_size:int, y_size:int, x_zoom_factor:float, y_zoom_factor:float):
        if x_zoom_factor < 1.0 or y_zoom_factor < 1.0:
            raise ValueError("Zoom factors should be at least 1.0 or greater")

        self.update_params(x_size, y_size, x_zoom_factor, y_zoom_factor)

    def update_params(self, x_size:int, y_size:int, x_zoom_factor:float, y_zoom_factor:float):
        self.__x_max = x_size
        self.__y_max = y_size
        self.__x_zoom = x_zoom_factor
        self.__y_zoom = y_zoom_factor

    def get_points(self, x:int, y:int) -> List[QPoint]:
        if x >= self.__x_max:
            raise ValueError("x value must be less than {0}".format(self.__x_max))

        if y >= self.__y_max:
            raise ValueError("y value must be less than {0}".format(self.__y_max))

        x_mapped = floor(x/self.__x_zoom)
        y_mapped = floor(y/self.__y_zoom)

        x_min = x_max = x
        x_val = x - 1
        while floor(x_val/self.__x_zoom) == x_mapped:
            x_min = x_val
            x_val = x_val - 1

        x_val = x + 1
        while floor(x_val/self.__x_zoom) == x_mapped:
            x_max = x_val
            x_val = x_val + 1

        y_min = y_max = y
        y_val = y - 1
        while floor(y_val/self.__y_zoom) == y_mapped:
            y_min = y_val
            y_val = y_val - 1

        y_val = y + 1
        while floor(y_val/self.__y_zoom) == y_mapped:
            y_max = y_val
            y_val = y_val + 1

        point_list:List[QPoint] = list()
        for x_point in range(x_min, x_max + 1):
            for y_point in range(y_min, y_max + 1):
                point_list.append(QPoint(x_point, y_point))

        ReversePixelCalculator.__LOG.debug("x_map: {0}, y_map: {1}, x_min: {2}, x_max: {3}, y_min: {4}, y_max: {5}".
            format(x_mapped, y_mapped, x_min, x_max, y_min, y_max))

        return point_list


# TODO this performs poorly for large and/or highly zoomed images
# TODO remove?  Anything interesting to be learned???
class ReversePixelMap():

    __LOG: Logger = LogHelper.logger("ReversePixelMap")

    # TODO perhaps use viewport's cooridinates to create the map for performance reasons???
    def __init__(self, x_size:int, y_size:int, x_zoom_factor:float, y_zoom_factor:float):
        if x_zoom_factor <= 1.0 or y_zoom_factor <= 1.0:
            raise ValueError("Zoom factors should be greater than 1.0")

        start_time = time.perf_counter_ns()

        pixel_map = np.indices((x_size, y_size))
        pixel_map[0] = np.floor(pixel_map[0] / x_zoom_factor).astype(np.int16)
        pixel_map[1] = np.floor(pixel_map[1] / y_zoom_factor).astype(np.int16)
        self.__pixel_map = np.moveaxis(pixel_map, 0, 2)

        end_time = time.perf_counter_ns()
        ReversePixelMap.__LOG.debug("Pixel map created in {0} ms".format((end_time - start_time) / 10**6))

    def __get_pixels(self, adjusted_x:int, adjusted_y:int) -> np.ndarray:
        """Get the zoomed in pixels that map back to a 1 to 1 pixel"""
        adj_pixel = np.array([adjusted_x, adjusted_y])
        mask = (self.__pixel_map == adj_pixel).all(2)
        pixel_list = np.transpose(mask.nonzero())
        return pixel_list

    def get_points(self, adjusted_x:int, adjusted_y:int) -> List[QPoint]:
        result = list()
        pixel_list = self.__get_pixels(adjusted_x, adjusted_y)
        for pixel in pixel_list:
            result.append(QPoint(pixel[0], pixel[1]))

        return result


class ImageLabel(QLabel):

    __LOG:Logger = LogHelper.logger("ImageLabel")

    class Action(Enum):
        Nothing = 0
        Dragging = 1
        Drawing = 2
        Picking = 3

    # TODO on double click we get both clicked and doubleClicked
    # TODO decide if we need both and fix
    area_selected = pyqtSignal(AreaSelectedEvent)
    left_clicked = pyqtSignal(AdjustedMouseEvent)
    right_clicked = pyqtSignal(AdjustedMouseEvent)
    double_clicked = pyqtSignal(AdjustedMouseEvent)
    mouse_move = pyqtSignal(AdjustedMouseEvent)
    locator_moved = pyqtSignal(ViewLocationChangeEvent)

    def __init__(self, image_descriptor:BandDescriptor, location_rect:bool=True,
            pixel_select:bool=False, parent=None):
        super().__init__(parent)

        # Install our event filter
        self.installEventFilter(self)

        # Image descriptor
        self.__descriptor = image_descriptor

        # mouse location
        self.__last_mouse_loc:QPoint = None

        # Parameters related to the image size
        self.__initial_size:QSize = None
        self.__width_scale_factor = 1.0
        self.__height_scale_factor = 1.0

        # Cursors we'll use
        self.__default_cursor = self.cursor()
        self.__drag_cursor = QCursor(Qt.ClosedHandCursor)
        self.__draw_cursor = QCursor(Qt.CrossCursor)
        self.__pick_cursor = QCursor(Qt.PointingHandCursor)

        # Initialize the locator if we have one
        if location_rect:
            # Initial size doesn't really matter,
            # it will get adjusted based on the zoom window size
            self.__locator_rect = QRect(0, 0, 50, 50)
        else:
            self.__locator_rect = None

        # The list of regions of interest
        self.__region_display_items:List[RegionDisplayItem] = list()

        # Color picker for region of interest displays
        self.__color_picker = ColorPicker()

        # Polygon selection items
        self.__polygon:QPolygon = None
        self.__polygon_bounds:QRect = None

        # Pixel selection items
        self.__pixel_select:bool = pixel_select
        self.__pixel_mapper:ReversePixelCalculator = None
        self.__pixel_list:np.ndarray = None
        self.__region_display_item = None

        self.__current_action = ImageLabel.Action.Nothing

        self.__overlay_pixmap:QPixmap = None
        self.__overlay_image:QImage = None

    def has_locator(self) -> bool:
        return self.__locator_rect is not None

    def locator_position(self) -> QPoint:
        assert self.__locator_rect is not None
        return self.__unscale_point(self.__locator_rect.center())

    def set_locator_position(self, postion:QPoint):
        # calls to this method should always be in 1 to 1 coordinates
        if self.has_locator():
            #TODO put contraints on it?
            new_position: QPoint = self.__scale_point(postion)
            ImageLabel.__LOG.debug("setting locator position: {0}, scaled pos: {1}", postion, new_position)
            self.__locator_rect.moveCenter(new_position)
            self.update()

    def locator_size(self) -> QSize:
        assert self.__locator_rect is not None
        return self.__unscale_size(self.__locator_rect.size())

    def set_locator_size(self, size:QSize):
        # calls to this method should always be in 1 to 1 coordinates
        if self.has_locator():
            #TODO constraints?
            new_size: QSize = self.__scale_size(size)
            ImageLabel.__LOG.debug("setting locator size: {0}, scaled size: {1}", size, new_size)
            self.__locator_rect.setSize(new_size)
            self.update()

    @pyqtSlot(AreaSelectedEvent)
    def add_selected_area(self, event:AreaSelectedEvent):
        display_item = event.display_item()
        display_item.toggled.connect(self.__handle_region_toggled)
        display_item.closed.connect(self.__handle__region_closed)
        self.__region_display_items.append(display_item)
        self.update()

    # TODO make private handler?
    def remove_all_regions(self):
        self.__region_display_items.clear()
        self.__clear_selected_area()
        self.__color_picker.reset()
        self.update()

    def setPixmap(self, pixel_map:QPixmap):
        locator_size:QSize = None
        locator_position:QPoint = None

        # If zoom changed we need to end any pixel selecting in progress
        if self.__current_action == ImageLabel.Action.Picking:
            self.__end_pixel_select()

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

        # scale and set overlay image if there is one
        self.__set_scaled_overlay()

        # reset locator if we have one
        if self.has_locator():
            self.set_locator_size(locator_size)
            self.set_locator_position(locator_position)

        # If there's a pixel mapper update it too
        if self.__pixel_mapper is not None:
            self.__pixel_mapper.update_params(
                    self.pixmap().size().width(), self.pixmap().size().height(),
                    self.__width_scale_factor, self.__height_scale_factor)

        self.setMinimumSize(size)
        self.setMaximumSize(size)

    def set_overlay_image(self, image:QImage):
        """The passed pixmap should be at 1 to 1 scale and the same size
        as this label's display image"""
        # Verify size match
        if image.size() != self.__initial_size:
            raise ValueError("Images must be the same size")

        self.__overlay_image = image
        self.__set_scaled_overlay()
        self.update()

    def __set_scaled_overlay(self):
        if self.__overlay_image is not None:
            self.__overlay_pixmap = QPixmap.fromImage(self.__overlay_image)

            # scale is correctly based on our scaling
            if self.__overlay_pixmap.size() != self.pixmap().size():
                self.__overlay_pixmap = self.__overlay_pixmap.scaled(self.pixmap().size(),
                    Qt.KeepAspectRatio, Qt.FastTransformation)

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
                self.__last_mouse_loc is not None and self.__locator_rect is not None:
            # ImageLabel.__LOG.debug("dragging mouse move event, pos: {0}, size: {1}", event.pos(), self.pixmap().size())
            center = self.__locator_rect.center()
            center += event.pos() - self.__last_mouse_loc
            self.__locator_rect.moveCenter(center)
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
        adjust_mouse_event = self.__create_adjusted_mouse_event(event)

        ImageLabel.__LOG.debug("mousePressEvent left: {0} or right: {1}, adj pos: {2}",
            event.button() == Qt.LeftButton, event.button() == Qt.RightButton,
            adjust_mouse_event.pixel_pos())

        # Check if we're selecting pixels and if so do it
        self.__select_pixel(adjust_mouse_event)

        self.right_clicked.emit(adjust_mouse_event)
        self.update()

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
            self.__get_select_polygon()
            self.update()

        elif self.__current_action == ImageLabel.Action.Picking and event.button() == Qt.LeftButton:
            self.__end_pixel_select()
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
                # TODO this has to account for scaling - no I don't think so now????
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

    def paintEvent(self, paint_event:QPaintEvent):
        # first render the image
        super().paintEvent(paint_event)
        # not sure why but it seems we need to create the painter each time
        painter = QPainter(self)
        brush:QBrush = QBrush(Qt.SolidPattern)

        # draw the polgon that is in the process of being created
        if self.__polygon is not None:
            painter.setPen(self.__color_picker.current_color())
            brush.setColor(self.__color_picker.current_color())
            path:QPainterPath = QPainterPath()
            path.addPolygon(QPolygonF(self.__polygon))
            path.closeSubpath()
            painter.fillPath(path, brush)

            # TODO probabaly don't need, only for debugging?
            if self.__current_action == ImageLabel.Action.Drawing:
                self.__polygon_bounds = self.__polygon.boundingRect()
                painter.drawRect(self.__polygon_bounds)

        # draw locator in red if present
        painter.setPen(Qt.red)
        if self.__locator_rect is not None:
            painter.drawRect(self.__locator_rect)

        # paint the selected regions scaling each one appropriately
        for region_item in self.__region_display_items:
            # ImageLabel.__LOG.debug("Region: {0}, is on: {1}", region_item.color(), region_item.is_on())
            if region_item.is_on():
                painter.scale(self.__width_scale_factor/region_item.x_zoom_factor(),
                    self.__height_scale_factor/region_item.y_zoom_factor())
                painter.setPen(region_item.color())
                brush.setColor(region_item.color())

                if region_item.painter_path() is not None:
                    painter.fillPath(region_item.painter_path(), brush)
                elif region_item.points() is not None:
                    for point in region_item.points():
                        painter.drawPoints(point)

                painter.resetTransform()

        # TODO location will be mouse driven,
        #  TODO size will default to 25% of image and be adjustable via menu
        if self.__overlay_pixmap is not None:
            x = 100 * self.__height_scale_factor
            y = 250 * self.__width_scale_factor
            painter.drawPixmap(x, y, self.__overlay_pixmap, x, y,
                floor(self.__initial_size.width() * self.__width_scale_factor * .25),
                floor(self.__initial_size.height() * self.__height_scale_factor * .25))

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
        new_size:QSize = QSize(size)
        if self.__width_scale_factor != 1.0:
            new_size.setWidth(floor(new_size.width() / self.__width_scale_factor))

        if self.__height_scale_factor != 1.0:
            new_size.setHeight(floor(new_size.height() / self.__height_scale_factor))

        return new_size

    def __clear_selected_area(self):
        self.__polygon_bounds = None
        self.__polygon = None
        self.update()

    @pyqtSlot(RegionDisplayItem)
    def __handle__region_closed(self, target:RegionDisplayItem):
        if target in self.__region_display_items:
            self.__region_display_items.remove(target)
            self.update()
        else:
            ImageLabel.__LOG.warning("Call to remove non-existent region ignored")

    @pyqtSlot(RegionDisplayItem)
    def __handle_region_toggled(self, target:RegionDisplayItem):
        self.update()

    def __select_pixel(self, adjusted_mouse_event:AdjustedMouseEvent):
        ImageLabel.__LOG.debug("__select_pixel called with current action: {0}".format(self.__current_action))
        if self.__current_action == ImageLabel.Action.Nothing and self.__pixel_select:
            self.__current_action = ImageLabel.Action.Picking
            self.setCursor(self.__pick_cursor)

            # Create of update the pixel mapper
            if self.__pixel_mapper is None:
                self.__pixel_mapper = ReversePixelCalculator(
                    self.pixmap().size().width(), self.pixmap().size().height(),
                    self.__width_scale_factor, self.__height_scale_factor)
            else:
                self.__pixel_mapper.update_params(
                    self.pixmap().size().width(), self.pixmap().size().height(),
                    self.__width_scale_factor, self.__height_scale_factor)

            # Create a RegionDisplayItem and wire it up
            color = self.__color_picker.current_color()
            self.__region_display_item = RegionDisplayItem(self.__width_scale_factor, self.__height_scale_factor,
                color, True, points=self.__pixel_mapper.get_points(
                    adjusted_mouse_event.mouse_event().x(), adjusted_mouse_event.mouse_event().y()))
            self.__region_display_item.closed.connect(self.__handle__region_closed)
            self.__region_display_item.toggled.connect(self.__handle_region_toggled)

            # Add it to the list of RegionDisplayItems
            self.__region_display_items.append(self.__region_display_item)

            # Create a new pixel list and add the selected adjusted pixel to list being
            # gathered for the RegionOfInterest
            self.__pixel_list = np.array([adjusted_mouse_event.pixel_x(), adjusted_mouse_event.pixel_y()]).reshape(1, 2)

        elif self.__current_action == ImageLabel.Action.Picking and self.__region_display_item is not None:
            # We're already in the process of selecting pixels so append to the RegionDisplayItems
            self.__region_display_item.append_points(self.__pixel_mapper.get_points(
                adjusted_mouse_event.mouse_event().x(), adjusted_mouse_event.mouse_event().y()))

            # And append to the pixel list
            self.__pixel_list = np.append(self.__pixel_list,
                np.array([adjusted_mouse_event.pixel_x(), adjusted_mouse_event.pixel_y()]).reshape(1, 2),
                axis=0)

    def __end_pixel_select(self):
        self.__current_action = ImageLabel.Action.Nothing
        self.setCursor(self.__default_cursor)
        self.__get_selected_pixels()

    def __get_selected_pixels(self):
        if len(self.__pixel_list) > 0:
            # Create region of interest.  The collection of points has already been
            # converted to 1 to 1 space.
            region = RegionOfInterest(np.array(self.__pixel_list), 1.0, 1.0,
                self.__initial_size.height(), self.__initial_size.width(), self.__descriptor)

            self.__pixel_list = None

            self.area_selected.emit(AreaSelectedEvent(region, self.__region_display_item))
            self.__color_picker.next_color()
            self.__region_display_item = None

    def __get_select_polygon(self):
        if self.__polygon_bounds is not None:
            if self.__polygon_bounds.size().height() > 1 and \
               self.__polygon_bounds.size().width() > 1:

                # point_list = self.__path.data()
                # for point in point_list:
                #     ImageLabel.__LOG.debug("Polygon point: {0}", point)

                x1, y1, x2, y2 = self.__polygon_bounds.getCoords()
                ImageLabel.__LOG.debug("Selected coords, x1: {0}, y1: {1}, x2: {2}, y2: {3}, size: {4}",
                    x1, y1, x2, y2, self.__polygon_bounds.size())

                # can get negative x1 & y1 if user drags off image to the left or top
                if x1 < 0 : x1 = 0
                if y1 < 0 : y1 = 0

                # testing showed lower and right edges seemed to clip at the
                # correct last pixels but make sure that doesn't change
                image_size = self.pixmap().size()
                ImageLabel.__LOG.debug("Image w: {0}, h: {1}", image_size.width(), image_size.height())
                if x2 > image_size.width() - 1 : x2 = image_size.width() - 1
                if y2 > image_size.height() - 1 : y2 = image_size.height() - 1

                # create an array of pixel locations contained by the
                # adjusted bounding rectangle coordinates
                x_range = ma.arange(x1, x2 + 1)
                y_range = ma.arange(y1, y2 + 1)
                points = ma.array(list(itertools.product(x_range, y_range)))

                # check to see which points also fall inside of the polygon
                for i in range(len(points)):
                    point = QPoint(points[i][0], points[i][1])
                    if not self.__polygon.containsPoint(point, Qt.WindingFill):
                        points[i] = ma.masked
                        # ImageLabel.__LOG.debug("Point out: {0}", point)

                ImageLabel.__LOG.debug("Points size: {0}, count: {1}", points.size, points.count())

                # make sure we haven't masked all the elements
                if points.count() > 0:
                    # extract the non-masked points and reshape the result back to a list of pairs
                    points = points[~points.mask].reshape(floor(points.count() / 2), 2)

                    ImageLabel.__LOG.debug("Final points shape: {0}, size: {1}, count: {2}",
                        points.shape, points.size, points.count())

                    # capture the region of interest and save to the map
                    region = RegionOfInterest(points,
                        self.__width_scale_factor, self.__height_scale_factor,
                        self.__initial_size.height(), self.__initial_size.width(), self.__descriptor)
                    color = self.__color_picker.current_color()

                    # Save the final version of the polygon as a QPainterPath it's more
                    # efficient for reuse and has more flexible painting options
                    painter_path = QPainterPath()
                    painter_path.addPolygon(QPolygonF(self.__polygon))
                    painter_path.closeSubpath()

                    display_item = RegionDisplayItem(self.__width_scale_factor, self.__height_scale_factor,
                        color, True, painter_path)
                    display_item.closed.connect(self.__handle__region_closed)
                    display_item.toggled.connect(self.__handle_region_toggled)
                    self.__region_display_items.append(display_item)

                    self.area_selected.emit(AreaSelectedEvent(region, display_item))
                    self.__color_picker.next_color()
                    self.__clear_selected_area()

                else:
                    ImageLabel.__LOG.debug("No points found in region, size: {0}", self.__polygon_bounds.size())
                    self.__clear_selected_area()
            else:
                ImageLabel.__LOG.debug("Zero dimension polygon rejected, size: {0}", self.__polygon_bounds.size())
                self.__clear_selected_area()

    def __pressed(self):
        # ImageLabel.__LOG.debug("press called, last_mouse_loc: {0}", self.__last_mouse_loc)
        if self.__last_mouse_loc is not None:
            if self.__locator_rect is not None and self.__locator_rect.contains(self.__last_mouse_loc):
                self.__current_action = ImageLabel.Action.Dragging
                self.setCursor(self.__drag_cursor)
                # ImageLabel.__LOG.debug("press called, drag start")
            elif self.__width_scale_factor >= 1.0 or self.__height_scale_factor >= 1.0:
                # need to limit region selection to scale factors greater than 1.0
                # or else we end up with a region whose pixel coverage is sparse
                self.__current_action = ImageLabel.Action.Drawing
                self.setCursor(self.__draw_cursor)
                self.__color_picker.current_color()
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

    area_selected = pyqtSignal(AreaSelectedEvent)
    left_clicked = pyqtSignal(AdjustedMouseEvent)
    right_clicked = pyqtSignal(AdjustedMouseEvent)
    mouse_move = pyqtSignal(AdjustedMouseEvent)
    image_resized = pyqtSignal(ImageResizeEvent)
    viewport_changed = pyqtSignal(ViewChangeEvent)
    locator_moved = pyqtSignal(ViewLocationChangeEvent)
    viewport_scrolled = pyqtSignal(ViewLocationChangeEvent)

    def __init__(self, image:Image, qimage_format:QImage.Format=QImage.Format_Grayscale8,
            location_rect:bool=True, pixel_select:bool=False, parent=None):
        super().__init__(parent)

        # TODO make settable prop?
        self.__margin_width = 4
        self.__margin_height = 4

        # TODO do we need to hold the data itself?
        self.__image = image
        self.__qimage_format = qimage_format

        self.__image_label = ImageLabel(self.__image.descriptor(), location_rect, pixel_select, self)
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

    def get_image(self) -> QImage:
        """Return a copy of our image"""
        return QImage(self.__qimage)

    def set_overlay_image(self, image:QImage):
        self.__image_label.set_overlay_image(image)

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

    def remove_all_regions(self):
        self.__image_label.remove_all_regions()

    def scale_image(self, factor:float):
        """Changes the scale relative to the original image size maintaining aspect ratio.
        The image is reset from the original QImage each time to prevent degradation"""
        ImageDisplay.__LOG.debug("scaling image by: {0}", factor)
        pix_map = QPixmap.fromImage(self.__qimage)
        if factor != 1.0:
            new_size = self.__image_size * factor
            # Use Qt.FastTransformation so pixels can be distinguished when zoomed in
            pix_map = pix_map.scaled(new_size, Qt.KeepAspectRatio, Qt.FastTransformation)

        self.__pix_map = pix_map
        self.__set_pixmap()

    def scale_to_size(self, new_size:QSize):
        """Scale the image to the given size maintaining aspect ratio. See http://doc.qt.io/qt-5/qpixmap.html#scaled
        for information about how the aspect ratio is handled using Qt.KeepAspectRatio
        Do not call repeatedly without a call to reset_size as image will blur with repeated scaling"""

        # Use Qt.FastTransformation so pixels can be distinguished when zoomed in
        self.__pix_map = self.__pix_map.scaled(new_size, Qt.KeepAspectRatio, Qt.FastTransformation)
        ImageDisplay.__LOG.debug("scaling to size: {0}", new_size)
        self.__set_pixmap()

    def scale_to_height(self, height:int):
        """Scale the image to the given height maintaining aspect ratio.
        Do not call repeatedly without a call to reset_size as image will blur with repeated scaling"""

        if self.__image_label.has_locator():
            ImageDisplay.__LOG.debug("scale_to_height locator size: {0}, pos: {1}", self.__image_label.locator_size(), self.__image_label.locator_position())

        # Use Qt.FastTransformation so pixels can be distinguished when zoomed in
        self.__pix_map = self.__pix_map.scaledToHeight(height, Qt.FastTransformation)
        ImageDisplay.__LOG.debug("scaling to height: {0}", height)
        self.__set_pixmap()

    def scale_to_width(self, width:int):
        """Scale the image to the given width maintaining aspect ratio.
        Do not call repeatedly without a call to reset_size as image will blur with repeated scaling"""

        # Use Qt.FastTransformation so pixels can be distinguished when zoomed in
        self.__pix_map = self.__pix_map.scaledToWidth(width, Qt.FastTransformation)
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

    def add_selected_area(self, area:AreaSelectedEvent):
        self.__image_label.add_selected_area(area)

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
    area_selected = pyqtSignal(AreaSelectedEvent)
    closed = pyqtSignal(WindowCloseEvent)

    def __init__(self, image:Image, label:str, qimage_format:QImage.Format,
                screen_geometry:QRect, location_rect:bool=True, pixel_select:bool=False, parent=None):
        super().__init__(parent)
        # TODO do we need to hold the data itself?
        self.__image = image
        self.__image_label = label
        self._image_display = ImageDisplay(self.__image, qimage_format, location_rect, pixel_select, self)
        self.__init_ui()

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

    def __init_ui(self):
        self.setWindowTitle(self.__image_label)

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

    def __get_image(self) -> QImage:
        return self._image_display.get_image()

    def __set_overlay_image(self, image:QImage):
        self._image_display.set_overlay_image(image)

    def image_label(self) -> str:
        return self.__image_label

    @pyqtSlot(AreaSelectedEvent)
    def handle_region_selected(self, event:AreaSelectedEvent):
        """Handle area select events from another associated window"""
        self._image_display.add_selected_area(event)

    # TODO add arg type hint when 3.6 support is done
    def link_window(self, window):
        """window should be an ImageDisplayWindow"""
        if isinstance(window, ImageDisplayWindow) and window != self:
            ImageDisplayWindow.__LOG.debug("Linking window {}, to window {}", self, window)
            # basically we need to exchange images
            self.__set_overlay_image(window.__get_image())
            window.__set_overlay_image(self.__get_image())

            # TODO need to be able to update it in response to an image adjustment

        elif window == self:
            ImageDisplayWindow.__LOG.error("Cannot link a window to itself")
        else:
            ImageDisplayWindow.__LOG.error("Window to link must an ImageDisplayWindow")

    def remove_all_regions(self):
        self._image_display.remove_all_regions()

    def refresh_image(self):
        self._image_display.refresh_image()

    def closeEvent(self, event:QCloseEvent):
        MainImageDisplayWindow.__LOG.debug("About to emit closed...")
        self.closed.emit(WindowCloseEvent(self))
        # accepting hides the window
        event.accept()

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
        super().__init__(image, label, qimage_format, screen_geometry, False, True, parent)

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
        # limit zoom out to going back to 1 to 1
        if self.__zoom_factor < 1.0:
            self.__zoom_factor = 1.0
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

    view_location_changed = pyqtSignal(ViewLocationChangeEvent)

    def __init__(self, image:Image, label, qimage_format:QImage.Format,
                screen_geometry:QRect, parent=None):
        super().__init__(image, label, qimage_format, screen_geometry, True, False, parent)
        self._image_display.right_clicked.connect(self.__handle_right_click)
        self._image_display.image_resized.connect(self.__handle_image_resize)
        self._image_display.locator_moved.connect(self.__handle_location_changed)

        # Prevents context menus from showing on right click
        # Only way I could find to prevent the dock widget context menu from
        # appearing on right click event even though it doesn't seem
        # it actually makes up to this window
        self.setContextMenuPolicy(Qt.PreventContextMenu)

        self.__calculate_sizes()

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

    # TODO don't need?
    def resizeEvent(self, event:QResizeEvent):
        size = event.size()
        # MainImageDisplayWindow.__LOG.debug("Resizing to w: {0}, h: {1}", size.width(), size.height())
