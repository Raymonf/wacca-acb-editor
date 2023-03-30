from collections import OrderedDict

from atom_types.runtime import util
from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfRowCell


def create_row(cue_id: int, reference_index: int, length_ms: int):
    return OrderedDict([
        UtfRowCell.build_tuple("CueId", util.i32swap(cue_id), ValueTypeNibble.int32),
        UtfRowCell.build_tuple("ReferenceIndex", util.i16swap(reference_index), ValueTypeNibble.int16),
        UtfRowCell.build_tuple("Length", util.i32swap(length_ms), ValueTypeNibble.int32),
    ])


class CueTable(TableBase):
    def __search(self, cue_id: int):
        try:
            cue_id_be = util.i32swap(cue_id)
            return next(filter(lambda x: x[1]["CueId"].value == cue_id_be, enumerate(self.utf.rows)))[0]
        except StopIteration:
            # Note that this is not the index of the cue, but the value of the CueId column.
            raise KeyError(f"Cue ID '{cue_id}' does not exist in Cue list.")

    def __get_next_cue_id(self):
        cueId = 0
        if len(self.utf.rows) > 0:
            # grab last row and start adding until we hit an unused cue ID
            # the value in the parsed row structure is big-endian read in as little-endian
            # we need to swap endianness to compare
            cueId = util.i32swap(self.utf.rows[-1]["CueId"].value) + 1
            while util.i32swap(cueId) in [r["CueId"].value for r in self.utf.rows]:
                cueId = cueId + 1
        return cueId

    def update(self, cue_id: int, reference_index: int, length: int):
        index = self.__search(cue_id)
        self.utf.rows[index]["ReferenceIndex"].value = util.i16swap(reference_index)
        self.utf.rows[index]["Length"].value = util.i32swap(length)

    def add(self, reference_index: int, length_ms: int):
        cue_id = self.__get_next_cue_id()
        self.utf.rows.append(create_row(cue_id, reference_index, length_ms))
        return len(self.utf.rows) - 1

    def pop(self, cue_id: int):
        index = self.__search(cue_id)
        self.utf.rows.pop(index)
