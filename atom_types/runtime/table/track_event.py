from construct import Byte, Default, FocusedSeq
from construct.core import Int16sb
from atom_types.runtime.table.table_base import TableBase

class TrackEventTable(TableBase):
    TrackEventCommand = FocusedSeq("waveformIndex",
        "unk0" / Default(Int16sb, 2000),
        "unk1" / Default(Byte, 4),
        "unk2" / Default(Int16sb, 2),
        "waveformIndex" / Int16sb,
        "unk3" / Default(Byte, 0),
        "unk4" / Default(Int16sb, 0)
    )

    def add(self, waveformIndex: int):
        self.utf.rows.append({"Command": self.TrackEventCommand.build(waveformIndex)})
        return len(self.utf.rows) - 1
        
    def pop(self, index: int):
        self.utf.rows.pop(index)