# -*- coding: utf-8 -*-
from typing import Set

from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsItem
)
from cadnano.objectinstance import ObjectInstance
from cadnano.proxies.cnenum import (
    PartEnum,
    ViewReceiveEnum
)
from cadnano.controllers import ViewRootController
from .nucleicacidpartitem import GridNucleicAcidPartItem

from cadnano.views.gridview import GridToolManagerT
from cadnano.cntypes import (
    WindowT,
    DocT,
    NucleicAcidPartT
)

class GridRootItem(QGraphicsRectItem):
    """``GridRootItem`` is the root item in the GridView. It gets added directly
    to the path ``QGraphicsScene`` by ``CNMainWindow``.
    It receives two signals::

        ``partAddedSignal`` and ``selectedPartChangedSignal``

    via its ``ViewRootController``.

    ``GridRootItem`` must instantiate its own controller to receive signals
    from the model.

    Attributes:
        instance_items (dict): Description
        manager (TYPE): Description
        name (str): Description
        select_tool (TYPE): Description
    """
    name = 'grid'
    view_type = ViewReceiveEnum.GRID

    def __init__(self,  rect: QRectF,
                        parent: QGraphicsItem,
                        window: WindowT,
                        document: DocT):
        """
        Args:
            rect: Rectangle of this item
            parent: parent object
            window: CNMainWindow
            document: Document
        """
        super(GridRootItem, self).__init__(rect, parent)
        self._window: WindowT = window
        self._document: DocT = document
        self._controller: ViewRootController = ViewRootController(self, document)
        self.instance_items: dict = {}
        self.manager: GridToolManagerT = None
        self.select_tool: AbstractGridToolT = None
        self.are_signals_on: bool = True
        self.setFlag(QGraphicsItem.ItemHasNoContents)

    def __repr__(self):
        _id = str(id(self))[-4:]
        _name  = self.__class__.__name__
        return '%s_%s_%s' % (_name, self._id_num, _id)

    ### SIGNALS ###

    ### SLOTS ###
    def partAddedSlot(self, sender: NucleicAcidPartT,
                            part_instance: ObjectInstance):
        """Receives notification from the model that a part has been added.
        Views that subclass AbstractView should override this method.

        Args:
            sender: Model object that emitted the signal.
            part_instance: Description

        Raises:
            NotImplementedError: unknown ``part_type``
        """
        if self.are_signals_on:
            part_type = part_instance.reference().partType()
            if part_type == PartEnum.NUCLEICACIDPART:
                na_part_item = GridNucleicAcidPartItem(part_instance,
                                                       viewroot=self)
                self.instance_items[na_part_item] = na_part_item
                self.select_tool.setPartItem(na_part_item)
                na_part_item.zoomToFit()
            else:
                raise NotImplementedError("Unknown part type %s" % part_type)
    # end def

    def documentChangeViewSignalingSlot(self, view_types: int):
        self.are_signals_on = True if view_types & self.view_type else False
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

        Returns:
            TYPE: Description
        """
        # if 'virtual_helix' not in filter_name_set:
        #     self.manager.chooseCreateTool()
        # for nucleicacid_part_item in self.instance_items:
        #     nucleicacid_part_item.setSelectionFilter(filter_name_set)
    # end def

    def preXoverFilterChangedSlot(self, filter_name: str):
        """
        Args:
            filter_name: Description
        """
    # end def

    def clearSelectionsSlot(self, doc: DocT):
        """
        Args:
            doc: Description
        """
        self.select_tool.deselectItems()
        self.scene().views()[0].clearSelectionLockAndCallbacks()
    # end def

    def resetRootItemSlot(self, doc: DocT):
        """
        Args:
            doc: Description
        """
        self.select_tool.deselectItems()
        self.scene().views()[0].clearGraphicsView()
    # end def

    ### ACCESSORS ###
    def window(self) -> WindowT:
        """
        Returns:
            the :class:`CNMainWindow`
        """
        return self._window
    # end def

    ### METHODS ###
    def destroyViewItems(self):
        print("destroying grid view")
        items = list(self.instance_items.values())
        for item in items:
            item.destroyItem()
    # end def

    def removePartItem(self, part_item: GridNucleicAcidPartItem):
        """
        Args:
            part_item: Description
        """
        del self.instance_items[part_item]
    # end def

    def resetDocumentAndController(self, document: DocT):
        """
        Args:
            document: Document

        Raises:
            ImportError: Description
        """
        self._document = document
        self._controller = ViewRootController(self, document)
        if len(self.instance_items) > 0:
            raise ImportError
    # end def

    def setModifyState(self, is_on: bool):
        """
        Args:
            is_on: Description
        """
        for nucleicacid_part_item in self.instance_items.values():
            nucleicacid_part_item.setModifyState(is_on)
    # end def

    def setManager(self, manager: GridToolManagerT):
        """Set the ``manager``, and the ``select_tool``

        Args:
            manager: the Grid tool manager
        """
        self.manager = manager
        self.select_tool = manager.select_tool
    # end def
