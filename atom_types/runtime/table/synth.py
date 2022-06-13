from construct import Array, Int16ub
from atom_types.runtime.table.table_base import TableBase

class SynthTable(TableBase):
    def build_stream(self, stream):
        for i, row in enumerate(self.utf.rows):
            row["ControlWorkArea1"].value = i
            row["ControlWorkArea2"].value = i
        super().build_stream(stream)
    
    def update(self, index: int, waveformIndex: int):        
        try:
            self.utf.rows[index]["ReferenceItems"] = Array(2, Int16ub).build((1, waveformIndex))
        except KeyError:
            raise KeyError(f"Row '{index}' does not exist in Synth list.")
        
    def add(self, waveformIndex: int):
        rowData = {
            "ReferenceItems": Array(2, Int16ub).build((1, waveformIndex))
        }
        self.utf.rows.append(rowData)
        return len(self.utf.rows) - 1
        
    def insert(self, index: int, waveformIndex: int):
        rowData = {
            "ReferenceItems": Array(2, Int16ub).build((1, waveformIndex))
        }
        self.utf.rows.insert(index, rowData)
        
    def pop(self, index: int):
        self.utf.rows.pop(index)