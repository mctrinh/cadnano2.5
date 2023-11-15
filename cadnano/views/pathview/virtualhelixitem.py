# -*- coding: utf-8 -*-
from typing import (
    Tuple,
    List
)
from math import (
    floor,
    atan2,
    sqrt
)

from PyQt5.QtCore import (
    QPointF,
    QRectF,
    Qt
)
from PyQt5.QtGui import (
    QPainterPath,
    QMouseEvent
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent
)

from cadnano import util
from cadnano.controllers import VirtualHelixItemController
from cadnano.gui.palette import (
    newPenObj,
    getColorObj,
    # getBrushObj,
    # getNoBrush
)
from cadnano.views.abstractitems import AbstractVirtualHelixItem
from .strand.stranditem import StrandItem
from .strand.xoveritem import XoverNode3
from .virtualhelixhandleitem import VirtualHelixHandleItem
from . import pathstyles as styles
from . import (
    PathNucleicAcidPartItemT,
    PathRootItemT
)
from cadnano.cntypes import (
    Vec2T,
    GraphicsViewT,
    WindowT,
    StrandT,
    StrandSetT,
    KeyT,
    ValueT
)

_BASE_WIDTH = styles.PATH_BASE_WIDTH
_VH_XOFFSET = styles.VH_XOFFSET


def v2DistanceAndAngle(a: Vec2T, b: Vec2T) -> Vec2T:
    """
    Args:
        a: Description
        b: Description

    Returns:
        distance and angle tuple
    """
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = sqrt(dx*dx + dy*dy)
    angle = atan2(dy, dx)
    return dist, angle


class PathVirtualHelixItem(AbstractVirtualHelixItem, QGraphicsPathItem):
    """VirtualHelixItem for PathView

    Attributes:
        drag_last_position (QPointF): Description
        FILTER_NAME (str): Description
        handle_start (QPointF): Description
        is_active (bool): Description
    """
    FILTER_NAME = "virtual_helix"

    def __init__(self, id_num: int, part_item: PathNucleicAcidPartItemT):
        """
        Args:
            id_num: VirtualHelix ID number. See `NucleicAcidPart` for
                description and related methods.
            part_item: Description
        """
        AbstractVirtualHelixItem.__init__(self, id_num, part_item)
        QGraphicsPathItem.__init__(self, parent=part_item.proxy())
        self._viewroot: PathRootItemT = part_item._viewroot
        self._getActiveTool = part_item._getActiveTool
        self._controller = VirtualHelixItemController(self, self._model_part, False, True)

        self._handle = VirtualHelixHandleItem(self, part_item)
        self._last_strand_set = None
        self._last_idx = None
        self.setFlag(QGraphicsItem.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        # self.setBrush(getNoBrush())
        # self.setBrush(getBrushObj(styles.BLUE_FILL, alpha=32))

        view = self.view()
        view.levelOfDetailChangedSignal.connect(self.levelOfDetailChangedSlot)
        should_show_details = view.shouldShowDetails()

        pen = newPenObj(styles.MINOR_GRID_STROKE, styles.MINOR_GRID_STROKE_WIDTH)
        pen.setCosmetic(should_show_details)
        self.setPen(pen)

        self.is_active = False

        self.refreshPath()
        self.setAcceptHoverEvents(True)  # for pathtools
        self.setZValue(styles.ZPATHHELIX)

        self._right_mouse_move = False
        self.drag_last_position = self.handle_start = self.pos()

    # end def

    ### SIGNALS ###

    ### SLOTS indirectly called from the part ###

    def levelOfDetailChangedSlot(self, is_cosmetic: bool):
        """Not connected to the model, only the QGraphicsView

        Args:
            is_cosmetic: Description
        """
        pen = self.pen()
        pen.setCosmetic(is_cosmetic)
        # print("levelOfDetailChangedSlot", is_cosmetic, pen.width())
        # if is_cosmetic:
        #     pass
        # else:
        #     pass
        self.setPen(pen)
    # end def

    def strandAddedSlot(self, strandset: StrandSetT, strand: StrandT):
        """Instantiates a :class:`StrandItem` upon notification that the model
        has a new :class:`Strand`.  The :class:`StrandItem` is responsible for
        creating its own controller for communication with the model, and for
        adding itself to its parent (which is *this* :class:`VirtualHelixItem`,
        i.e. 'self').

        Args:
            strandset: Model object that emitted the signal.
            strand: Description
        """
        if self._viewroot.are_signals_on:
            StrandItem(strand, self)
    # end def

    def virtualHelixRemovedSlot(self):
        '''Slot wrapper for ``destroyItem()``
        '''
        return self.destroyItem()
    # end def

    def destroyItem(self):
        '''Remove this object and references to it from the view
        '''
        print("Destroying PathVirtualHelixItem")
        strand_item_list = self.getStrandItems()
        for item in strand_item_list:
            item.destroyItem()
        self.view().levelOfDetailChangedSignal.disconnect(self.levelOfDetailChangedSlot)
        self._controller.disconnectSignals()
        self._controller = None

        scene = self.scene()
        self._handle.destroyItem()
        scene.removeItem(self)
        self._part_item = None
        self._model_part = None
        self._getActiveTool = None
        self._handle = None
        self._viewroot = None
    # end def

    def virtualHelixPropertyChangedSlot(self, keys: KeyT, values: ValueT):
        """
        Args:
            keys: Description
            values: Description
        """
        for key, val in zip(keys, values):
            if key == 'is_visible':
                if val:
                    self.show()
                    self._handle.show()
                    self.showXoverItems()
                else:
                    self.hideXoverItems()
                    self.hide()
                    self._handle.hide()
                    return
            if key == 'z':
                part_item = self._part_item
                z = part_item.convertToQtZ(val)
                if self.x() != z:
                    self.setX(z)
                    """ The handle is selected, so deselect to
                    accurately position then reselect
                    """
                    vhi_h = self._handle
                    vhi_h.tempReparent()
                    vhi_h.setX(z - _VH_XOFFSET)
                    # if self.isSelected():
                    #     print("ImZ", self.idNum())
                    part_item.updateXoverItems(self)
                    vhi_h_selection_group = self._viewroot.vhiHandleSelectionGroup()
                    vhi_h_selection_group.addToGroup(vhi_h)
            elif key == 'eulerZ':
                self._handle.rotateWithCenterOrigin(val)
                # self._prexoveritemgroup.updatePositionsAfterRotation(value)
            ### GEOMETRY PROPERTIES ###
            elif key == 'repeat_hint':
                pass
                # self.updateRepeats(int(val))
            elif key == 'bases_per_repeat':
                pass
                # self.updateBasesPerRepeat(int(val))
            elif key == 'turns_per_repeat':
                # self.updateTurnsPerRepeat(int(val))
                pass
            ### RUNTIME PROPERTIES ###
            elif key == 'neighbors':
                # this means a virtual helix in the slice view has moved
                # so we need to clear and redraw the PreXoverItems just in case
                if self.isActive():
                    self._part_item.setPreXoverItemsVisible(self)
        self.refreshPath()
    # end def

    def showXoverItems(self):
        """
        """
        for item in self.childItems():
            if isinstance(item, XoverNode3):
                item.showXover()
    # end def

    def getStrandItems(self) -> List[StrandItem]:
        strand_item_list: List[StrandItems] = []
        for item in self.childItems():
            if isinstance(item, StrandItem):
                strand_item_list.append(item)
        return strand_item_list
    # end def

    def hideXoverItems(self):
        """
        """
        for item in self.childItems():
            if isinstance(item, XoverNode3):
                item.hideXover()
    # end def

    ### ACCESSORS ###
    def viewroot(self) -> PathRootItemT:
        """
        Returns:
            :class:`PathRootItem`
        """
        return self._viewroot
    # end def

    def handle(self) -> VirtualHelixHandleItem:
        """
        Returns:
            :class:`VirtualHelixHandleItem`
        """
        return self._handle
    # end def

    def window(self) -> WindowT:
        """
        Returns:
            :class:`CNMainWindow`
        """
        return self._part_item.window()
    # end def

    def view(self) -> GraphicsViewT:
        return self._viewroot.scene().views()[0]
    # end def

    ### DRAWING METHODS ###
    def upperLeftCornerOfBase(self, idx: int, strand: StrandT) -> Vec2T:
        """
        Args:
            idx: the base index within the virtual helix
            strand: Description

        Returns:
            Tuple of upperLeftCornerOfBase
        """
        x = idx * _BASE_WIDTH
        y = 0 if strand.isForward() else _BASE_WIDTH
        return x, y
    # end def

    def upperLeftCornerOfBaseType(self, idx: int, is_fwd: bool) -> Vec2T:
        """
        Args:
            idx (int): the base index within the virtual helix
            is_fwd: Description

        Returns:
            Tuple of upperLeftCornerOfBase
        """
        x = idx * _BASE_WIDTH
        y = 0 if is_fwd else _BASE_WIDTH
        return x, y
    # end def

    def refreshPath(self):
        """Returns a :class:`QPainterPath` object for the minor grid lines.
        The path also includes a border outline and a midline for
        dividing scaffold and staple bases.
        """
        bw = _BASE_WIDTH
        bw2 = 2 * bw
        part = self.part()
        path = QPainterPath()
        sub_step_size = part.subStepSize()
        _, canvas_size = self._model_part.getOffsetAndSize(self._id_num)
        # border
        path.addRect(0, 0, bw * canvas_size, 2 * bw)
        # minor tick marks
        for i in range(canvas_size):
            x = round(bw * i)
            if i % sub_step_size == 0:
                # path.moveTo(x - .5, 0)
                # path.lineTo(x - .5, bw2)
                # path.lineTo(x - .25, bw2)
                # path.lineTo(x - .25, 0)
                # path.lineTo(x, 0)
                # path.lineTo(x, bw2)
                # path.lineTo(x + .25, bw2)
                # path.lineTo(x + .25, 0)
                # path.lineTo(x + .5, 0)
                # path.lineTo(x + .5, bw2)

                # path.moveTo(x - .5, 0)
                # path.lineTo(x - .5, bw2)
                path.moveTo(x - .25, bw2)
                path.lineTo(x - .25, 0)
                path.lineTo(x, 0)
                path.lineTo(x, bw2)
                path.lineTo(x + .25, bw2)
                path.lineTo(x + .25, 0)

                # path.moveTo(x-.5, 0)
                # path.lineTo(x-.5, 2 * bw)
                # path.lineTo(x+.5, 2 * bw)
                # path.lineTo(x+.5, 0)

            else:
                path.moveTo(x, 0)
                path.lineTo(x, 2 * bw)

        # staple-scaffold divider
        path.moveTo(0, bw)
        path.lineTo(bw * canvas_size, bw)

        self.setPath(path)
    # end def

    def resize(self):
        """Called by part on resize.
        """
        self.refreshPath()
    # end def

    ### PUBLIC SUPPORT METHODS ###
    def activate(self):
        """
        """
        pen = self.pen()
        pen.setColor(getColorObj(styles.MINOR_GRID_STROKE_ACTIVE))
        self.setPen(pen)
        self.is_active = True
    # end def

    def deactivate(self):
        """
        """
        pen = self.pen()
        pen.setColor(getColorObj(styles.MINOR_GRID_STROKE))
        self.setPen(pen)
        self.is_active = False
    # end def

    ### EVENT HANDLERS ###
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Parses a :meth:`mousePressEvent` to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event: Description
        """
        # 1. Check if we are doing a Z translation
        if event.button() == Qt.RightButton:
            viewroot = self._viewroot
            current_filter_set = viewroot.selectionFilterSet()
            if self.FILTER_NAME in current_filter_set and self.part().isZEditable():
                self._right_mouse_move = True
                self.drag_last_position = event.scenePos()
                self.handle_start = self.pos()
            return

        self.scene().views()[0].addToPressList(self)
        strand_set, idx = self.baseAtPoint(event.pos())
        self._model_part.setActiveVirtualHelix(self._id_num, strand_set.isForward(), idx)
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MousePress"

        if hasattr(self, tool_method_name):
            self._last_strand_set, self._last_idx = strand_set, idx
            getattr(self, tool_method_name)(strand_set, idx, event.modifiers())
        else:
            event.setAccepted(False)
    # end def

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """Parses a :meth:`mouseMoveEvent` to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event: Description
        """
        # 1. Check if we are doing a Z translation
        if self._right_mouse_move:
            MOVE_THRESHOLD = 0.01   # ignore small moves
            new_pos = event.scenePos()
            delta = new_pos - self.drag_last_position
            dx = int(floor(delta.x() / _BASE_WIDTH))*_BASE_WIDTH
            x = self.handle_start.x() + dx
            if abs(dx) > MOVE_THRESHOLD or dx == 0.0:
                old_x = self.x()
                self.setX(x)
                vhi_h = self._handle
                vhi_h.tempReparent()
                vhi_h.setX(x - _VH_XOFFSET)
                self._part_item.updateXoverItems(self)
                dz = self._part_item.convertToModelZ(x - old_x)
                self._model_part.translateVirtualHelices([self.idNum()],
                                                         0, 0, dz, False,
                                                         use_undostack=False)
                return
        # 2. Forward event to tool
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseMove"
        if hasattr(self, tool_method_name):
            strand_set, idx = self.baseAtPoint(event.pos())
            if self._last_strand_set != strand_set or self._last_idx != idx:
                self._last_strand_set, self._last_idx = strand_set, idx
                getattr(self, tool_method_name)(strand_set, idx)
        else:
            event.setAccepted(False)
    # end def

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """Called in the event of doing a Z translation drag

        Args:
            event: Description
        """
        if self._right_mouse_move and event.button() == Qt.RightButton:
            MOVE_THRESHOLD = 0.01   # ignore small moves
            self._right_mouse_move = False
            delta = self.pos() - self.handle_start
            dz = delta.x()
            if abs(dz) > MOVE_THRESHOLD:
                dz = self._part_item.convertToModelZ(dz)
                self._model_part.translateVirtualHelices([self.idNum()],
                                                         0, 0, dz, True,
                                                         use_undostack=True)
    # end def

    def customMouseRelease(self, event: QMouseEvent):
        """Parses a GraphicsView :meth:`mouseReleaseEvent` to extract strand_set
         and base index, forwarding them to approproate tool method as necessary.

        Args:
            event: Description
        """
        tool = self._getActiveTool()
        tool_method_name = tool.methodPrefix() + "MouseRelease"
        if hasattr(self, tool_method_name):
            getattr(self, tool_method_name)(self._last_strand_set, self._last_idx)
        else:
            event.setAccepted(False)
    # end def

    ### COORDINATE UTILITIES ###
    def baseAtPoint(self, pos: QPointF) -> Tuple[StrandSetT, int]:
        """Returns the (Strandset, index) under the location x, y or None.

        It shouldn't be possible to click outside a pathhelix and still call
        this function. However, this sometimes happens if you click exactly
        on the top or bottom edge, resulting in a negative y value.

        Args:
            pos: Description
        """
        x, y = pos.x(), pos.y()
        part = self._model_part
        id_num = self._id_num
        base_idx = int(floor(x / _BASE_WIDTH))
        min_base, max_base = 0, part.maxBaseIdx(id_num)
        if base_idx < min_base or base_idx >= max_base:
            base_idx = util.clamp(base_idx, min_base, max_base)
        if y < 0:
            y = 0  # HACK: zero out y due to erroneous click
        strand_type = floor(y * 1. / _BASE_WIDTH)   # 0 for fwd, 1 for rev
        strand_type = int(util.clamp(strand_type, 0, 1))
        strand_set = part.getStrandSets(id_num)[strand_type]
        return (strand_set, base_idx)
    # end def

    def keyPanDeltaX(self) -> float:
        """How far a single press of the left or right arrow key should move
        the scene (in scene space)
        """
        dx = self._part_item.part().stepSize() * _BASE_WIDTH
        return self.mapToScene(QRectF(0, 0, dx, 1)).boundingRect().width()
    # end def

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Args:
            event: Description
        """
        self._part_item.updateStatusBar("")
    # end def

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        """Parses a :meth:`hoverMoveEvent` to extract strand_set and base index,
        forwarding them to approproate tool method as necessary.

        Args:
            event: Description
        """
        base_idx = int(floor(event.pos().x() / _BASE_WIDTH))
        loc = "%d[%d]" % (self._id_num, base_idx)
        self._part_item.updateStatusBar(loc)

        active_tool = self._getActiveTool()
        tool_method_name = active_tool.methodPrefix() + "HoverMove"
        if hasattr(self, tool_method_name):
            is_fwd, idx_x, idx_y = active_tool.baseAtPoint(self, event.pos())
            getattr(self, tool_method_name)(is_fwd, idx_x, idx_y)
    # end def

    ### TOOL METHODS ###
    def createToolMousePress(self, strand_set: StrandSetT, idx: int, modifiers):
        """:meth:`Strand.getDragBounds`

        Args:
            strand_set: Description
            idx: the base index within the virtual helix
        """
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        if modifiers & Qt.ShiftModifier:
            bounds = strand_set.getBoundsOfEmptyRegionContaining(idx)
            ret = strand_set.createStrand(*bounds)
            print("creating strand {} was successful: {}".format(bounds, ret))
            return
        active_tool = self._getActiveTool()
        if not active_tool.isDrawingStrand():
            active_tool.initStrandItemFromVHI(self, strand_set, idx)
            active_tool.setIsDrawingStrand(True)
    # end def

    def selectToolMousePress(self, strand_set: StrandSetT, idx: int, modifiers):
        pass

    def createToolMouseMove(self, strand_set: StrandSetT, idx: int):
        """:meth:`Strand.getDragBounds`

        Args:
            strand_set: Description
            idx: the base index within the virtual helix
        """
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.updateStrandItemFromVHI(self, strand_set, idx)
    # end def

    def createToolMouseRelease(self, strand_set: StrandSetT, idx: int):
        """:meth:`Strand.getDragBounds`

        Args:
            strand_set: Description
            idx: the base index within the virtual helix
        """
        # print("%s: %s[%s]" % (util.methodName(), strand_set, idx))
        active_tool = self._getActiveTool()
        if active_tool.isDrawingStrand():
            active_tool.setIsDrawingStrand(False)
            active_tool.attemptToCreateStrand(self, strand_set, idx)
    # end def

    def createToolHoverMove(self, is_fwd: bool, idx_x: int, idx_y: int):
        """Create the strand is possible.

        Args:
            is_fwd: Description
            idx_x: Description
            idx_y: Description
        """
        active_tool = self._getActiveTool()
        if not active_tool.isFloatingXoverBegin():
            temp_xover = active_tool.floatingXover()
            temp_xover.updateFloatingFromVHI(self, is_fwd, idx_x, idx_y)
    # end def
