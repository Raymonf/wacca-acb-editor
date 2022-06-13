from atom_types.runtime.table.table_base import TableBase

class CueNameTable(TableBase):
    def update(self, cueId: int, referenceIndex: int, length: int):
        try:
            index = next(filter(lambda x: x[1]["CueId"] == cueId, enumerate(self.utf.rows)))[0]
            self.utf.rows[index]["ReferenceIndex"] = referenceIndex
            self.utf.rows[index]["Length"] = length
        except StopIteration:
            raise KeyError(f"Cue ID '{cueId}' does not exist in Cue Name list.")
        
    def upsert(self, cueId: int, referenceIndex: int, length: int):
        try:
            index = next(filter(lambda x: x[1]["CueId"] == cueId, enumerate(self.utf.rows)))[0]
            self.utf.rows[index]["ReferenceIndex"] = referenceIndex
            self.utf.rows[index]["Length"] = length
        except StopIteration:
            self.add()
        
    def add(self, cueName: str, cueIndex: int):
        if cueName in [row["CueName"] for row in self.utf.rows]:
            raise KeyError(f"Cue name '{cueName}' already present in Cue Name list.")
        
        rowData = {
            "CueName": cueName,
            "CueIndex": cueIndex
        }
        self.utf.rows.append(rowData)
        return len(self.utf.rows) - 1
        
    def pop(self, cueName):
        try:
            index = next(filter(lambda x: x[1]["CueName"] == cueName, enumerate(self.utf.rows)))[0]
            self.utf.rows.pop(index)
        except StopIteration:
            raise KeyError(f"Cue name '{cueName}' does not exist in Cue Name list.")
        
    def get(self, cueIndex):
        try:
            index = next(filter(lambda x: x[1]["CueIndex"] == cueIndex, enumerate(self.utf.rows)))[0]
            return self.utf.rows[index]["CueName"]
        except StopIteration:
            raise KeyError(f"Cue index '{cueIndex}' does not exist in Cue Name list.")