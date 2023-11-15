from cadnano.proxies.cnproxy import UndoCommand
from cadnano import util
from cadnano.cntypes import (
    OligoT
)

class ApplySequenceCommand(UndoCommand):
    def __init__(self, oligo: OligoT, sequence: str):
        super(ApplySequenceCommand, self).__init__("apply sequence")
        self._oligo = oligo
        self._new_sequence = sequence
        self._old_sequence = oligo.sequence()
    # end def

    def redo(self):
        olg = self._oligo
        n_s = None if self._new_sequence is None else ''.join(self._new_sequence)
        n_s_original = self._new_sequence
        oligo_list = [olg]
        for strand in olg.strand5p().generator3pStrand():
            used_seq, n_s = strand.setSequence(n_s)
            # get the compliment ahead of time
            used_seq = None if used_seq is None else util.comp(used_seq)
            for comp_strand in strand.getComplementStrands():
                comp_strand.setComplementSequence(used_seq, strand)
                oligo_list.append(comp_strand.oligo())
            # end for
            # as long as the new Applied Sequence is not None
            if n_s is None and n_s_original is not None:
                break
        # end for
        for oligo in oligo_list:
            oligo.oligoSequenceAddedSignal.emit(oligo)
    # end def

    def undo(self):
        olg = self._oligo
        o_s = None if self._old_sequence is None else ''.join(self._old_sequence)

        oligo_list = [olg]

        for strand in olg.strand5p().generator3pStrand():
            used_seq, o_s = strand.setSequence(o_s)

            # get the compliment ahead of time
            used_seq = None if used_seq is None else util.comp(used_seq)
            for comp_strand in strand.getComplementStrands():
                comp_strand.setComplementSequence(used_seq, strand)
                oligo_list.append(comp_strand.oligo())
            # end for
        # for

        for oligo in oligo_list:
            oligo.oligoSequenceAddedSignal.emit(oligo)
    # end def
# end class
