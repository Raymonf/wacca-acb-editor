from collections import OrderedDict
from typing import Literal

from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime import util
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfRowCell


def get_channel_id(channel: Literal["speaker", "headphone"]):
    return 0 if channel == "speaker" else 1

class TrackTable(TableBase):
    def __create_row(self, track_event_id: int, channel: Literal["speaker", "headphone"]):
        has_event_index = True if len(self.utf.rows) < 1 else "EventIndex" in self.utf.rows[0]
        event_index_row = UtfRowCell.build_tuple("EventIndex", util.i16swap(track_event_id), ValueTypeNibble.int16)

        return OrderedDict(
            ([event_index_row] if has_event_index else []) + [
                UtfRowCell.build_tuple("CommandIndex", util.i16swap(get_channel_id(channel)), ValueTypeNibble.int16),
            ])

    def add(self, track_event_id: int, channel: Literal["speaker", "headphone"]):
        # bruh
        self.utf.rows.append(self.__create_row(track_event_id, channel))
        return len(self.utf.rows) - 1
    
    def update(self, index: int, channel: Literal["speaker", "headphone"]):
        try:
            self.utf.rows[index]["CommandIndex"].value = util.i16swap(get_channel_id(channel))
        except KeyError:
            raise KeyError(f"Row '{index}' does not exist in Track list.")

    def insert(self, index: int, channel: Literal["speaker", "headphone"]):
        rowData = {
            "EventIndex": len(self.utf.rows) - 1,
            "CommandIndex": 0 if channel == "speaker" else 1
        }
        self.utf.rows.insert(index, rowData)
        
    def pop(self, index: int):
        self.utf.rows.pop(index)