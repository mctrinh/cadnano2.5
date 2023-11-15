# -*- coding: utf-8 -*-
from typing import (
    List,
    Tuple
)

from PyQt5.QtCore import (
    Qt,
    QPointF
)
from PyQt5.QtGui import (
    QPainterPath,
    QColor
)
from PyQt5.QtWidgets import (
    QGraphicsPathItem,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent
)

from cadnano.fileio.lattice import (
    HoneycombDnaPart,
    SquareDnaPart
)
from cadnano.gui.palette import (
    getPenObj,
    getBrushObj,
    getNoPen
)
from cadnano.proxies.cnenum import (
    GridEnum,
    EnumType
)
from cadnano.views.gridview import GridNucleicAcidPartItemT
from cadnano.views.gridview.tools import (
    SelectGridToolT,
    CreateGridToolT
)
from cadnano.cntypes import (
    RectT
)
from . import gridstyles as styles

_RADIUS = styles.GRID_HELIX_RADIUS
_ZVALUE = styles.ZGRIDHELIX + 1
HIGHLIGHT_WIDTH = styles.GRID_HELIX_MOD_HILIGHT_WIDTH
DELTA = (HIGHLIGHT_WIDTH - styles.GRID_HELIX_STROKE_WIDTH)/2.


class GridItem(QGraphicsPathItem):
    """Summary

    Attributes:
        allow_snap: Description
        bounds: Description
        dots: Description
        draw_lines: Description
        grid_type: Description
        part_item: Description
        points: Description
    """

    def __init__(self,  part_item: GridNucleicAcidPartItemT,
                        grid_type: EnumType):
        """Summary

        Args:
            part_item: Description
            grid_type: Description
        """
        super(GridItem, self).__init__(parent=part_item)
        self.part_item = part_item
        dot_size = 0.5
        self.dots: Tuple[float, float] = (dot_size, dot_size / 2)
        self.allow_snap: bool = part_item.window().action_vhelix_snap.isChecked()
        self.draw_lines: bool = True
        self.points: List[GridPoint] = []

        color = QColor(Qt.blue)
        color.setAlphaF(0.1)
        self.setPen(color)
        self.setGridType(grid_type)
    # end def

    def destroyItem(self):
        print("destroying gridView GridItem")
        scene = self.scene()
        for point in self.points:
            point.destroyItem()
        self.points = None
        scene.removeItem(self)
    # end def

    def updateGrid(self):
        """Summary

        Returns:
            TYPE: Description
        """
        part_item = self.part_item
        part = part_item.part()
        radius = part.radius()
        self.bounds = bounds = part_item.bounds()
        self.removePoints()
        if self.grid_type == GridEnum.HONEYCOMB:
            self.doHoneycomb(part_item, radius, bounds)
        elif self.grid_type == GridEnum.SQUARE:
            self.doSquare(part_item, radius, bounds)
        else:
            self.setPath(QPainterPath())
    # end def

    def setGridType(self, grid_type: EnumType):
        """Summary

        Args:
            grid_type: Description
        """
        self.grid_type = grid_type
        self.updateGrid()
    # end def

    def setGridAppearance(self, draw_lines):
        # TODO[NF]:  Docstring
        self.draw_lines = draw_lines
        self.updateGrid()

    def doHoneycomb(self,   part_item: GridNucleicAcidPartItemT,
                            radius: float,
                            bounds: RectT):
        """
        Args:
            part_item: Description
            radius: Description
            bounds: Description
        """
        doLattice = HoneycombDnaPart.latticeCoordToModelXY
        doPosition = HoneycombDnaPart.positionToLatticeCoordRound
        isEven = HoneycombDnaPart.isEvenParity
        x_l, x_h, y_l, y_h = bounds
        x_l = x_l + HoneycombDnaPart.PAD_GRID_XL
        x_h = x_h + HoneycombDnaPart.PAD_GRID_XH
        y_h = y_h + HoneycombDnaPart.PAD_GRID_YL
        y_l = y_l + HoneycombDnaPart.PAD_GRID_YH
        dot_size, half_dot_size = self.dots
        sf = part_item.scale_factor
        points = self.points
        row_l, col_l = doPosition(radius, x_l, -y_l, False, False, scale_factor=sf)
        row_h, col_h = doPosition(radius, x_h, -y_h, True, True, scale_factor=sf)
        # print(row_l, row_h, col_l, col_h)

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines
        for i in range(row_l, row_h):
            for j in range(col_l, col_h+1):
                x, y = doLattice(radius, i, j, scale_factor=sf)
                if draw_lines:
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                """ +x is Left and +y is down
                origin of ellipse is Top Left corner so we subtract half in X
                and subtract in y
                """
                pt = GridPoint(x - half_dot_size,
                               -y - half_dot_size,
                               dot_size, self)
                pt.setPen(getPenObj(Qt.blue, 1.0))
                points.append(pt)
            is_pen_down = False
        # end for i
        # DO VERTICAL LINES
        if draw_lines:
            for j in range(col_l, col_h+1):
                # print("newcol")
                for i in range(row_l, row_h):
                    x, y = doLattice(radius, i, j, scale_factor=sf)
                    if is_pen_down and not isEven(i, j):
                        path.lineTo(x, -y)
                        is_pen_down = False
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                is_pen_down = False
            # end for j
        self.setPath(path)
    # end def

    def doSquare(self,  part_item: GridNucleicAcidPartItemT,
                        radius: float,
                        bounds: RectT):
        """
        Args:
            part_item: Description
            radius: Description
            bounds: Description
        """
        doLattice = SquareDnaPart.latticeCoordToModelXY
        doPosition = SquareDnaPart.positionToLatticeCoordRound
        x_l, x_h, y_l, y_h = bounds
        dot_size, half_dot_size = self.dots
        sf = part_item.scale_factor
        points = self.points
        row_l, col_l = doPosition(radius, x_l, -y_l, scale_factor=sf)
        row_h, col_h = doPosition(radius, x_h, -y_h, scale_factor=sf)
        # print(row_l, row_h, col_l, col_h)

        path = QPainterPath()
        is_pen_down = False
        draw_lines = self.draw_lines

        for i in range(row_l, row_h + 1):
            for j in range(col_l, col_h + 1):
                x, y = doLattice(radius, i, j, scale_factor=sf)
                if draw_lines:
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                """+x is Left and +y is down
                origin of ellipse is Top Left corner so we subtract half in X
                and subtract in y
                """
                pt = GridPoint(x - half_dot_size,
                               -y - half_dot_size,
                               dot_size, self)
                pt.setPen(getPenObj(Qt.blue, 1.0))
                points.append(pt)
            is_pen_down = False  # pen up
        # DO VERTICAL LINES
        if draw_lines:
            for j in range(col_l, col_h + 1):
                for i in range(row_l, row_h + 1):
                    x, y = doLattice(radius, i, j, scale_factor=sf)
                    if is_pen_down:
                        path.lineTo(x, -y)
                    else:
                        is_pen_down = True
                        path.moveTo(x, -y)
                is_pen_down = False  # pen up
        self.setPath(path)
    # end def

    def removePoints(self):
        """Summary
        """
        points = self.points
        scene = self.scene()
        while points:
            scene.removeItem(points.pop())
    # end def
# end class


class GridPoint(QGraphicsEllipseItem):
    """
    Attributes:
        clickarea (ClickArea): Description
        grid (GridItem): Description
        offset (float): Description
    """
    def __init__(self,  x: float, y: float, diameter: float,
                        parent_grid: GridItem):
        """
        Args:
            x:
            y:
            diameter:
            parent_grid:
        """
        super(GridPoint, self).__init__(0., 0.,
                                        diameter, diameter, parent=parent_grid)
        self.offset: float = diameter / 2
        self.grid: GridItem = parent_grid

        self.clickarea = ClickArea(diameter, parent=self)

        self.setPos(x, y)
        self.setZValue(_ZVALUE)
    # end def

    def destroyItem(self):
        self.grid = None
        self.clickarea.destroyItem()
        self.clickarea = None
        self.scene().removeItem(self)
    # end def

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handler for user mouse press.

        Args:
            event: Contains item, scene, and screen coordinates of the the
                event, and previous event.
        """
        if self.grid.allow_snap:
            part_item = self.grid.part_item
            tool = part_item._getActiveTool()
            if tool.FILTER_NAME not in part_item.part().document().filter_set:
                return
            tool_method_name = tool.methodPrefix() + "MousePress"
            if hasattr(self, tool_method_name):
                getattr(self, tool_method_name)(tool, part_item, event)
        else:
            QGraphicsEllipseItem.mousePressEvent(self, event)
    # end def

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        """Summary

        Args:
            event: Description
        """
        self.setBrush(getBrushObj(styles.ACTIVE_GRID_DOT_COLOR))
        self.setPen(getPenObj(styles.ACTIVE_GRID_DOT_COLOR, 1.0))
        part_item = self.grid.part_item
        part_item._getActiveTool()
        # tool.setHintPos(self.scenePos())
    # end def

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        """
        Args:
            event: Description
        """
        self.setBrush(getBrushObj(styles.DEFAULT_GRID_DOT_COLOR))
        self.setPen(getPenObj(styles.DEFAULT_GRID_DOT_COLOR, 1.0))
    # end def

    def selectToolMousePress(self,  tool: SelectGridToolT,
                                    part_item: GridNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        """
        Args:
            tool: :class:`SelectGridTool`
            part_item: :class:`GridNucleicAcidPartItem`
            event: the mouse event
        """
        part = part_item.part()
        part.setSelected(True)
        # print("GridPoint MousePress for select")
        alt_event = GridEvent(self, self.offset)
        tool.selectOrSnap(part_item, alt_event, event)
        return QGraphicsEllipseItem.mousePressEvent(self, event)
    # end def

    def createToolMousePress(self,  tool: CreateGridToolT,
                                    part_item: GridNucleicAcidPartItemT,
                                    event: QGraphicsSceneMouseEvent):
        """
        Args:
            tool: :class:`CreateGridTool`
            part_item: :class:`GridNucleicAcidPartItem`
            event: the mouse event
        """
        part = part_item.part()
        part.setSelected(True)
        alt_event = GridEvent(self, self.offset)
        part_item.createToolMousePress(tool, event, alt_event)
    # end def
# end class

class ClickArea(QGraphicsEllipseItem):
    """
    Attributes:
        parent_obj: Description
    """
    _RADIUS = styles.GRID_HELIX_RADIUS

    def __init__(self, diameter: float, parent: GridPoint):
        nd = 2*self._RADIUS
        offset = -0.5*nd + diameter/2
        super(ClickArea, self).__init__(offset, offset, nd, nd, parent=parent)
        self.parent_obj = parent
        self.setPen(getNoPen())
    # end def

    def destroyItem(self):
        self.parent_obj = None
        self.scene().removeItem(self)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        return self.parent_obj.mousePressEvent(event)
# end class

class GridEvent(object):
    """
    Attributes:
        grid_pt (GridPoint): The grid point
        offset (QPointF): the offset
    """
    def __init__(self, grid_pt: GridPoint, offset: float):
        """
        Args:
            grid_pt: The grid point
            offset: the offset
        """
        self.grid_pt = grid_pt
        self.offset = QPointF(offset, offset)

    def scenePos(self) -> QPointF:
        """Scene position, with offset.

        Returns:
            Scene position, with offset.
        """
        return self.grid_pt.scenePos() + self.offset

    def pos(self) -> QPointF:
        """Local position, with offset.

        Returns:
            local position with offset
        """
        return self.grid_pt.pos() + self.offset
# end class
