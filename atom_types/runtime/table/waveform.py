from atom_types.runtime.table.table_base import TableBase

class WaveformTable(TableBase):
    def updateByAwbId(self, streamAwbId: int, numChannels: int, numSamples: int):
        try:
            index = next(filter(lambda x: x[1]["StreamAwbId"] == streamAwbId, enumerate(self.utf.rows)))[0]
            self.utf.rows[index]["numChannels"] = numChannels
            self.utf.rows[index]["numSamples"] = numSamples
        except StopIteration:
            raise KeyError(f"AWB ID '{streamAwbId}' does not exist in waveform list.")
        
    def updateByAwbIndex(self, index: int, streamAwbId: int, numChannels: int, numSamples: int):
        try:
            self.utf.rows[index]["StreamAwbId"] = streamAwbId
            self.utf.rows[index]["numChannels"] = numChannels
            self.utf.rows[index]["numSamples"] = numSamples
        except StopIteration:
            raise KeyError(f"Row '{index}' does not exist in waveform list.")
        
    # def add(self, channel: Literal['headphones', 'speakers']):
    #     if cueId in [row["CueId"] for row in self.utf.rows]:
    #         raise KeyError(f"Cue ID '{cueId}' already present in cue list.")
        
    #     rowData = {
    #         "CueId": cueId,
    #         "ReferenceIndex": referenceIndex,
    #         "Length": length
    #     }
    #     self.utf.rows.append(rowData)
    #     return len(self.utf.rows) - 1
        
    # def pop(self, cueId: int):
    #     try:
    #         index = next(filter(lambda x: x[1]["CueId"] == cueId, enumerate(self.utf.rows)))[0]
    #         self.utf.rows.pop(index)
    #     except StopIteration:
    #         raise KeyError(f"Cue ID '{cueId}' does not exist in cue list.")