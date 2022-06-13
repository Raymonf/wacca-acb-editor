from atom_types.runtime.table.table_base import TableBase

class CueTable(TableBase):
    def update(self, cueId: int, referenceIndex: int, length: int):
        try:
            index = next(filter(lambda x: x[1]["CueId"] == cueId, enumerate(self.utf.rows)))[0]
            self.utf.rows[index]["ReferenceIndex"] = referenceIndex
            self.utf.rows[index]["Length"] = length
        except StopIteration:
            raise KeyError(f"Cue ID '{cueId}' does not exist in Cue list.")
        
    def add(self, cueId: int, referenceIndex: int, length: int):
        if cueId in [row["CueId"] for row in self.utf.rows]:
            raise KeyError(f"Cue ID '{cueId}' already present in Cue list.")
        
        rowData = {
            "CueId": cueId,
            "ReferenceIndex": referenceIndex,
            "Length": length
        }
        self.utf.rows.append(rowData)
        return len(self.utf.rows) - 1
        
    def pop(self, cueId: int):
        try:
            index = next(filter(lambda x: x[1]["CueId"] == cueId, enumerate(self.utf.rows)))[0]
            self.utf.rows.pop(index)
        except StopIteration:
            raise KeyError(f"Cue ID '{cueId}' does not exist in Cue list.")