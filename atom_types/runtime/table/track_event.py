from collections import OrderedDict
from io import BytesIO

from construct import Byte, Default, FocusedSeq
from construct.core import Int16sb

from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfBlob, UtfRowCell


class TrackEventTable(TableBase):
    TrackEventCommand = FocusedSeq("synthIndex",
                                   "tlv_code" / Default(Int16sb, 2000),
                                   "tlv_size" / Default(Byte, 4),
                                   "tlv_type" / Default(Int16sb, 2),
                                   "synthIndex" / Int16sb,
                                   "unk1" / Default(Byte, 0),
                                   "unk2" / Default(Int16sb, 0)
                                   )

    def add(self, synth_id: int):
        command = self.TrackEventCommand.build(synth_id)
        command_blob = UtfBlob("Command", BytesIO(command), 0, len(command))
        row = OrderedDict([
            UtfRowCell.build_tuple("Command", command_blob, ValueTypeNibble.blob),
        ])
        self.utf.rows.append(row)
        return len(self.utf.rows) - 1

    def pop(self, index: int):
        self.utf.rows.pop(index)
