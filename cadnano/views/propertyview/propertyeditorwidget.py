# -*- coding: utf-8 -*-
"""
Attributes:
    COLOR_PATTERN (regex): Description
"""
import re
from typing import (
    List,
    Set
)

from PyQt5.QtCore import (
    Qt,
    QRect,
    QModelIndex
)
from PyQt5.QtGui import (
    QFont,
    QPalette,
    QPainter
)
from PyQt5.QtWidgets import (
    QTreeWidget,
    QHeaderView,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QStyle,
    QCommonStyle,
    QWidget,
    QUndoStack
)

from cadnano.objectinstance import ObjectInstance
from cadnano.proxies.cnenum import (
    ItemEnum,
    ViewReceiveEnum
)
from cadnano.gui.palette import getBrushObj
from cadnano.controllers import ViewRootController
from cadnano.views.pathview import pathstyles as styles

from cadnano.views.outlinerview.cnoutlineritem import CNOutlinerItem
from .oligoitem import OligoSetItem
from .nucleicacidpartitem import NucleicAcidPartSetItem
from .virtualhelixitem import VirtualHelixSetItem
from .cnpropertyitem import CNPropertyItem
from cadnano.cntypes import (
    PartT,
    DocT,
    WindowT
)

COLOR_PATTERN = re.compile("#[0-9a-f].....")
_FONT = QFont(styles.THE_FONT, 12)
_QCOMMONSTYLE = QCommonStyle()


class PropertyEditorWidget(QTreeWidget):
    """
    PropertyEditorWidget enables direct editing attributes of an
    item that is selected in the Outliner.
    """
    view_type = ViewReceiveEnum.PROPERTY

    def __init__(self, parent: QWidget = None):
        """Summary

        Args:
            parent (None, optional): Description
        """
        super(PropertyEditorWidget, self).__init__(parent)
        self._outline_view_obj_set = set()
        self._outline_view_obj_list = []
        self.are_signals_on = True
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)  # no mac focus halo
    # end def

    def undoStack(self) -> QUndoStack:
        return self._document.undoStack()
    # end def

    def configure(self, window: WindowT, document: DocT):
        """
        Args:
            window: Description
            document: Description
        """
        self._window = window
        self._document = document
        self._controller = ViewRootController(self, document)
        self._root = self.invisibleRootItem()

        # Appearance
        self.setFont(_FONT)
        # Columns
        self.setColumnCount(2)
        self.setIndentation(14)
        # Header
        self.setHeaderLabels(["Property", "Value"])
        h = self.header()
        h.resizeSection(0, 200)
        h.resizeSection(1, 100)
        h.setSectionResizeMode(QHeaderView.Interactive)
        # h.setStretchLastSection(False)

        custom_delegate = CustomStyleItemDelegate(self)
        self.setItemDelegate(custom_delegate)

        self.model().dataChanged.connect(self.dataChangedSlot)
        self.hide()

        # Add some dummy items
        # p1 = self.addDummyRow("sequence", "ATCGACTGATCG")
        # p2 = self.addDummyRow("circular",  True)
    # end def

    # def addDummyRow(self, property_name, value, parent_QTreeWidgetItem=None):
    #     if parent_QTreeWidgetItem is None:
    #         parent_QTreeWidgetItem = self.invisibleRootItem()
    #     tw_item = QTreeWidgetItem(parent_QTreeWidgetItem)
    #     tw_item.setData(0, Qt.EditRole, property_name)
    #     tw_item.setData(1, Qt.EditRole, value)
    #     tw_item.setFlags(tw_item.flags() | Qt.ItemIsEditable)
    #     return tw_item
    # end def

    ### SIGNALS ###

    ### SLOTS ###
    def outlinerItemSelectionChanged(self):
        """
        Raises:
            NotImplementedError: Description
        """
        o = self._window.outliner_widget
        for child in self.children():
            if isinstance(child, (CNPropertyItem)):
                child.disconnectSignals()

        selected_items = o.selectedItems()

        self.clear()    # remove pre-existing items
        self._outline_view_obj_set.clear()
        self._outline_view_obj_list = []
        # print("prop multiple selected:", len(selected_items))
        # if len(selected_items):
        #     print(selected_items[0])

        # get the selected item
        item_types = set([item.itemType() for item in selected_items])
        num_types = len(item_types)
        if num_types != 1:  # assume no mixed types for now
            return
        item_type = item_types.pop()
        outline_view_obj_list = [item.outlineViewObj() for item in selected_items if item.isSelected()]

        '''Workaround as items in QTreeWidget.selectedItems() may be not
        actually selected
        '''
        if len(outline_view_obj_list) == 0:
            # print("outlinerItemSelectionChanged returning2")
            return
        self._outline_view_obj_set = set(outline_view_obj_list)
        self._outline_view_obj_list = outline_view_obj_list

        # special case for parts since there is currently no part filter
        if item_type is ItemEnum.NUCLEICACID:
            pe_item = NucleicAcidPartSetItem(parent=self)
            self.show()
            return

        item = selected_items[0]
        if item.FILTER_NAME not in self._document.filter_set:
            print(item.FILTER_NAME, "not in self._document.filter_set")
            return
        if item_type is ItemEnum.OLIGO:
            pe_item = OligoSetItem(parent=self)
            self.show()
        elif item_type is ItemEnum.VIRTUALHELIX:
            pe_item = VirtualHelixSetItem(parent=self)
            self.show()
        else:
            raise NotImplementedError
    # end def

    def partAddedSlot(self, sender: PartT, model_part_instance: ObjectInstance):
        """
        Args:
            sender: Model object that emitted the signal.
            model_part_instance (ObjectInstance): The model part
        """
    # end def


    def documentChangeViewSignalingSlot(self, view_types: int):
        self.are_signals_on = True if view_types & self.view_type else False
    # end def

    def clearSelectionsSlot(self, document: DocT):
        """
        Args:
            doc: Description
        """
    # end def

    def dataChangedSlot(self, top_left: QModelIndex, bot_right: QModelIndex):
        """docstring for propertyChangedSlot

        Args:
            top_left: Description
            bot_right: Description
        """
        c_i = self.currentItem()
        if c_i is None:
            return
        if c_i == self.itemFromIndex(top_left):
            c_i.updateCNModel()

        # call this to prevent UNDO calls propagating through the Widget first
        self.outlinerItemSelectionChanged()
    # end def

    def selectedChangedSlot(self, item_dict: dict):
        """
        Args:
            item_dict: Description
        """
    # end def

    def selectionFilterChangedSlot(self, filter_name_set: Set[str]):
        """
        Args:
            filter_name_set: Description
        """
        pass
    # end def

    def preXoverFilterChangedSlot(self, filter_name: str):
        """
        Args:
            filter_name: Description
        """
        pass
    # end def

    def resetRootItemSlot(self, document: DocT):
        """
        Args:
            document: Description
        """
        self.clear()
    # end def

    ### ACCESSORS ###
    def window(self) -> WindowT:
        """
        Returns:
            model :class:`CNMainWindow`
        """
        return self._window
    # end def

    def outlineViewObjSet(self) -> Set[CNOutlinerItem]:
        return self._outline_view_obj_set
    # end def

    def outlineViewObjList(self) -> List[CNOutlinerItem]:
        return self._outline_view_obj_list
    # end def

    ### METHODS ###
    def resetDocumentAndController(self, document: DocT):
        """
        Args:
            document: model :class:`Document`
        """
        self._document = document
        self._controller = ViewRootController(self, document)
    # end def

# end class PropertyEditorWidget


class CustomStyleItemDelegate(QStyledItemDelegate):
    """Summary
    """

    def createEditor(self,  parent_qw: QWidget,
                            option: QStyleOptionViewItem,
                            model_index: QModelIndex) -> QWidget:
        """
        Args:
            parent_qw: Description
            option: Description
            model_index: Description

        Returns:
            the widget used to edit the item specified by index for editing
        """
        column = model_index.column()
        treewidgetitem = self.parent().itemFromIndex(model_index)
        if column == 0:  # Property Name
            return None
        elif column == 1:
            editor = treewidgetitem.configureEditor(parent_qw, option, model_index)
            return editor
        else:
            return QStyledItemDelegate.createEditor(self,
                                                    parent_qw,
                                                    option, model_index)
    # end def

    def updateEditorGeometry(self,  editor: QWidget,
                                    option: QStyleOptionViewItem,
                                    model_index: QModelIndex):
        """
        Args:
            editor: Description
            option: Description
            model_index: Description
        """
        column = model_index.column()
        if column == 0:
            editor.setGeometry(option.rect)
        elif column == 1:
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is bool:
                rect = QRect(option.rect)
                delta = option.rect.width() / 2 - 9
                rect.setX(option.rect.x() + delta)  # Hack to center the checkbox
                editor.setGeometry(rect)
            else:
                editor.setGeometry(option.rect)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, model_index)
    # end def

    def paint(self, painter: QPainter,
                    option: QStyleOptionViewItem,
                    model_index: QModelIndex):
        """
        Args:
            painter: Description
            option: Description
            model_index: Description
        """
        # row = model_index.row()
        column = model_index.column()
        if column == 0:  # Part Name
            option.displayAlignment = Qt.AlignVCenter
            QStyledItemDelegate.paint(self, painter, option, model_index)
        if column == 1:  # Visibility
            value = model_index.model().data(model_index, Qt.EditRole)
            data_type = type(value)
            if data_type is str:
                # print("val", value)
                if COLOR_PATTERN.search(value):
                    # print("found color")
                    element = _QCOMMONSTYLE.PE_IndicatorCheckBox
                    styleoption = QStyleOptionViewItem()
                    styleoption.palette.setBrush(QPalette.Button, getBrushObj(value))
                    styleoption.rect = QRect(option.rect)
                    _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                option.displayAlignment = Qt.AlignVCenter
                QStyledItemDelegate.paint(self, painter, option, model_index)
            elif data_type is int:
                option.displayAlignment = Qt.AlignVCenter
                QStyledItemDelegate.paint(self, painter, option, model_index)
            elif data_type is float:
                option.displayAlignment = Qt.AlignVCenter
                QStyledItemDelegate.paint(self, painter, option, model_index)
            elif data_type is bool:
                element = _QCOMMONSTYLE.PE_IndicatorCheckBox
                styleoption = QStyleOptionButton()
                styleoption.rect = QRect(option.rect)
                checked = value
                styleoption.state |= QStyle.State_On if checked else QStyle.State_Off
                styleoption.palette.setBrush(QPalette.Button, Qt.white)
                styleoption.palette.setBrush(QPalette.HighlightedText, Qt.black)
                _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
                if checked:
                    element = _QCOMMONSTYLE.PE_IndicatorMenuCheckMark
                    _QCOMMONSTYLE.drawPrimitive(element, styleoption, painter)
        else:
            QStyledItemDelegate.paint(self, painter, option, model_index)
    # end def
# end class CustomStyleItemDelegate
