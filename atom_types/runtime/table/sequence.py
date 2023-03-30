from collections import OrderedDict
from io import BytesIO
from typing import List

from construct import GreedyRange, Int16sb

from atom_types.runtime import util
from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfBlob, UtfRowCell


def build_track_index_blob(track_indices: List[int]):
    b = GreedyRange(Int16sb).build(track_indices)
    return UtfBlob("TrackIndex", BytesIO(b), 0, len(b))


class SequenceTable(TableBase):
    def __create_row(self, num_tracks: int, track_indices: List[int], command_index: int):
        # 3.10 has NumTracks as a constant (2), so we have to check to make sure it exists
        has_num_tracks = True if len(self.utf.rows) < 1 else "NumTracks" in self.utf.rows[0]
        num_tracks_row = UtfRowCell.build_tuple("NumTracks", util.i16swap(num_tracks), ValueTypeNibble.int16)

        return OrderedDict(
            ([num_tracks_row] if has_num_tracks else []) + [
                UtfRowCell.build_tuple("TrackIndex", build_track_index_blob(track_indices), ValueTypeNibble.blob),
                UtfRowCell.build_tuple("CommandIndex", util.i16swap(command_index), ValueTypeNibble.int16),
            ])

    def build_stream(self, stream):
        for i in range(len(self.utf.rows)):
            # ControlWorkArea1/2 denotes index, i.e. <SequenceId>
            index_be = util.i16swap(i)
            self.utf.rows[i]["ControlWorkArea1"] = UtfRowCell.build("ControlWorkArea1", index_be, ValueTypeNibble.int16)
            self.utf.rows[i]["ControlWorkArea2"] = UtfRowCell.build("ControlWorkArea2", index_be, ValueTypeNibble.int16)

        super().build_stream(stream)

    def update(self, index: int, num_tracks: int, track_indices: List[int], command_index: int = 1):
        try:
            has_num_tracks = True if len(self.utf.rows) < 1 else "NumTracks" in self.utf.rows[0]
            if has_num_tracks:
                self.utf.rows[index]["NumTracks"].value = util.i16swap(num_tracks)
            self.utf.rows[index]["TrackIndex"].value = build_track_index_blob(track_indices)
            self.utf.rows[index]["CommandIndex"].value = util.i16swap(command_index)
            return index
        except KeyError:
            raise KeyError(f"Row '{index}' does not exist in Sequence list.")

    def add(self, num_tracks: int, track_indices: List[int], command_index: int = 1):
        self.utf.rows.append(self.__create_row(num_tracks, track_indices, command_index))
        return len(self.utf.rows) - 1

    def insert(self, index: int, num_tracks: int, track_indices: List[int], command_index: int = 1):
        self.utf.rows.insert(index, self.__create_row(num_tracks, track_indices, command_index))

    def pop(self, index: int):
        self.utf.rows.pop(index)
