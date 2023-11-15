# -*- coding: utf-8 -*-
from cadnano.cntypes import (
    DocT
)

class ViewRootController():
    def __init__(self, view_root, model_document: DocT):
        self._view_root = view_root
        self._model_document = model_document
        self.connectSignals()
    # end def

    def connectSignals(self):
        m_d = self._model_document
        v_r = self._view_root
        m_d.documentPartAddedSignal.connect(v_r.partAddedSlot)
        m_d.documentClearSelectionsSignal.connect(v_r.clearSelectionsSlot)
        m_d.documentSelectionFilterChangedSignal.connect(v_r.selectionFilterChangedSlot)
        m_d.documentPreXoverFilterChangedSignal.connect(v_r.preXoverFilterChangedSlot)
        m_d.documentViewResetSignal.connect(v_r.resetRootItemSlot)
        m_d.documentChangeViewSignalingSignal.connect(v_r.documentChangeViewSignalingSlot)
    # end def

    def disconnectSignals(self):
        m_d = self._model_document
        v_r = self._view_root
        m_d.documentPartAddedSignal.disconnect(v_r.partAddedSlot)
        m_d.documentClearSelectionsSignal.disconnect(v_r.clearSelectionsSlot)
        m_d.documentSelectionFilterChangedSignal.disconnect(v_r.selectionFilterChangedSlot)
        m_d.documentPreXoverFilterChangedSignal.disconnect(v_r.preXoverFilterChangedSlot)
        m_d.documentViewResetSignal.disconnect(v_r.resetRootItemSlot)
        m_d.documentChangeViewSignalingSignal.disconnect(v_r.documentChangeViewSignalingSlot)
    # end def
