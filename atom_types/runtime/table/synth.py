from collections import OrderedDict
from io import BytesIO

from construct import Array, Int16ub

from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime import util
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfBlob, UtfRowCell


def create_reference_items_blob(waveform_index: int):
    data = Array(2, Int16ub).build((1, waveform_index))
    return UtfBlob("ReferenceItems", BytesIO(data), 0, len(data))


def create_row(waveform_index: int):
    blob = create_reference_items_blob(waveform_index)
    return OrderedDict([
        UtfRowCell.build_tuple("ReferenceItems", blob, ValueTypeNibble.blob)
    ])


class SynthTable(TableBase):

    def build_stream(self, stream):
        for i, row in enumerate(self.utf.rows):
            # ControlWorkArea1/2 denotes index, i.e. <SynthId>
            index_be = util.i16swap(i)
            self.utf.rows[i]["ControlWorkArea1"] = UtfRowCell.build("ControlWorkArea1", index_be, ValueTypeNibble.int16)
            self.utf.rows[i]["ControlWorkArea2"] = UtfRowCell.build("ControlWorkArea2", index_be, ValueTypeNibble.int16)
        super().build_stream(stream)

    def update(self, index: int, waveform_index: int):
        try:
            self.utf.rows[index]["ReferenceItems"] = create_reference_items_blob(waveform_index)
        except KeyError:
            raise KeyError(f"Synth ID '{index}' does not exist in Synth list.")

    def add(self, waveform_index: int) -> int:
        self.utf.rows.append(create_row(waveform_index))
        return len(self.utf.rows) - 1

    def insert(self, index: int, waveform_index: int):
        self.utf.rows.insert(index, create_row(waveform_index))

    def pop(self, index: int):
        self.utf.rows.pop(index)
