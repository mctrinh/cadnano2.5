from typing import (
    Iterable,
    Tuple,
    Set
)

import numpy as np

from cadnano.proxies.cnobject import CNObject
from cadnano.cntypes import (
    NucleicAcidPartT,
    StrandT,
    StrandSetT,
    KeyT,
    ValueT,
    RectT
)

class VirtualHelix(CNObject):
    """lightweight convenience class whose properties are still stored in the
    `NucleicAcidPart`.  Having this makes it easier to write views.
    """

    def __init__(self, id_num: int, part: NucleicAcidPartT):
        super(VirtualHelix, self).__init__(part)
        self._id_num = id_num
        self._part = part
    # end def

    def __repr__(self) -> str:
        _id = str(id(self))[-4:]
        _name  = self.__class__.__name__
        return '%s_%s_%s' % (_name, self._id_num, _id)

    @property
    def editable_properties(self) -> Set[str]:
        return self._part.vh_editable_properties

    def part(self) -> NucleicAcidPartT:
        return self._part
    # end def

    def idNum(self) -> int:
        return self._id_num
    # end def

    def getProperty(self, keys: KeyT) -> ValueT:
        return self._part.getVirtualHelixProperties(self._id_num, keys)
    # end def

    def setProperty(self, keys: KeyT, values: ValueT, id_nums: Iterable[int] = None):
        if id_nums:
            part = self._part
            for id_num in id_nums:
                part.setVirtualHelixProperties(id_num, keys, values)
        else:
            return self._part.setVirtualHelixProperties(self._id_num, keys, values)
    # end def

    def getModelProperties(self) -> dict:
        return self._part.getAllVirtualHelixProperties(self._id_num)
    # end def

    def getAllPropertiesForIdNum(self, id_num: int) -> dict:
        return self._part.getAllVirtualHelixProperties(id_num)
    # end def

    def getName(self) -> str:
        return self._part.getVirtualHelixProperties(self._id_num, 'name')
    # end def

    def getColor(self) -> str:
        return self._part.getVirtualHelixProperties(self._id_num, 'color')
    # end def

    def getSize(self) -> int:
        offset, size = self._part.getOffsetAndSize(self._id_num)
        return int(size)
    # end def

    def setSize(self, new_size: int, id_nums: Iterable[int] = None):
        if id_nums:
            for id_num in id_nums:
                self._part.setVirtualHelixSize(id_num, new_size)
        else:
            return self._part.setVirtualHelixSize(self._id_num, new_size)
    # end def

    def fwdStrandSet(self) -> StrandSetT:
        return self._part.fwd_strandsets[self._id_num]
    # end def

    def revStrandSet(self) -> StrandSetT:
        return self._part.rev_strandsets[self._id_num]
    # end def

    def fwdStrand(self, idx: int) -> StrandT:
        return self._part.fwd_strandsets[self._id_num].getStrand(idx)
    # end def

    def revStrand(self, idx: int) -> StrandT:
        self._part.rev_strandsets[self._id_num].getStrand(idx)
    # end def

    def getTwistPerBase(self) -> Tuple[float, float]:
        """
        Returns:
            tuple of twist per base in degrees, eulerZ
        """
        bpr, tpr, eulerZ = self._part.getVirtualHelixProperties(self._id_num,
                                                                ['bases_per_repeat', 'turns_per_repeat', 'eulerZ'])
        return tpr*360./bpr, eulerZ

    def getAngularProperties(self) -> RectT:
        """
        Returns:
            Tuple of 'bases_per_repeat, 'bases_per_turn',
                    'twist_per_base', 'minor_groove_angle'
        """
        bpr, tpr, mga = self._part.getVirtualHelixProperties(self._id_num,
                                                             ['bases_per_repeat', 'turns_per_repeat', 'minor_groove_angle'])
        bases_per_turn = bpr / tpr
        return bpr, bases_per_turn, tpr*360./bpr, mga
    # end def

    def setZ(self, new_z: float, id_nums: Iterable[int] = None):
        m_p = self._part
        if id_nums is None:
            id_nums = [self._id_num]

        for id_num in id_nums:
            old_z = m_p.getVirtualHelixProperties(id_num, 'z')
            if new_z != old_z:
                dz = new_z - old_z
                m_p.translateVirtualHelices([id_num], 0, 0, dz, finalize=False, use_undostack=True)
    # end def

    def getZ(self, id_num: int = None) -> float:
        """Get the 'z' property of the VirtualHelix described by ID number
        'id_num'.

        If a VirtualHelix corresponding to id_num does not exist, an IndexError
        will be thrown by getVirtualHelixProperties.
        """
        if __debug__:
            assert isinstance(id_num, int) or id_num is None

        return self._part.getVirtualHelixProperties(id_num if id_num is not None
                                                    else self._id_num, 'z')

    def getAxisPoint(self, idx: int) -> np.ndarray:
        """
        Args:
            idx: index of base

        Returns:
            ``ndarray`` of :obj:`float` shape (1, 3)
        """
        return self._part.getCoordinate(self._id_num, idx)
    # end def

    def setActive(self, is_fwd: bool, idx: int):
        """Makes active the virtual helix associated with this item."""
        self._part.setActiveVirtualHelix(self._id_num, is_fwd, idx)
    # end def

    def isActive(self) -> bool:
        return self._part.isVirtualHelixActive(self._id_num)
    # end def
# end class
