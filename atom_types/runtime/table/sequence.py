from typing import List

from construct import GreedyRange, Int16sb
from atom_types.runtime.table.table_base import TableBase

class SequenceTable(TableBase):
    def build_stream(self, stream):
        for i in range(len(self.utf.rows)):
            self.utf.rows[i]["ControlWorkArea1"].value = i
            self.utf.rows[i]["ControlWorkArea2"].value = i
            
        super().build_stream(stream)
        
    def update(self, index: int, numTracks: int, trackIndices: List[int], commandIndex: int = 1):#, hash: Optional[bytes] = None):
        try:
            self.utf.rows[index]["NumTracks"] = numTracks
            self.utf.rows[index]["TrackIndex"] = GreedyRange(Int16sb).build(trackIndices)
            self.utf.rows[index]["CommandIndex"] = commandIndex
        except KeyError:
            raise KeyError(f"Row '{index}' does not exist in Sequence list.")
        
    def add(self, numTracks: int, trackIndices: List[int], commandIndex: int = 1):
        rowData = {
            "NumTracks": numTracks,
            "TrackIndex": GreedyRange(Int16sb).build(trackIndices),
            "CommandIndex": commandIndex
        }
        self.utf.rows.append(rowData)
        return len(self.utf.rows) - 1
        
    def insert(self, index: int, numTracks: int, trackIndices: List[int], commandIndex: int = 1):
        rowData = {
            "NumTracks": numTracks,
            "TrackIndex": GreedyRange(Int16sb).build(trackIndices),
            "CommandIndex": commandIndex
        }
        self.utf.rows.insert(index, rowData)
        
    def pop(self, index: int):
        self.utf.rows.pop(index)