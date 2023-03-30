from collections import OrderedDict

from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime import util
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfRowCell


class WaveformTable(TableBase):
    # def updateByAwbId(self, streamAwbId: int, numChannels: int, numSamples: int):
    #     try:
    #         index = next(filter(lambda x: x[1]["StreamAwbId"] == streamAwbId, enumerate(self.utf.rows)))[0]
    #         self.utf.rows[index]["numChannels"] = numChannels
    #         self.utf.rows[index]["numSamples"] = numSamples
    #     except StopIteration:
    #         raise KeyError(f"AWB ID '{streamAwbId}' does not exist in waveform list.")
    #
    # def updateByAwbIndex(self, index: int, streamAwbId: int, numChannels: int, numSamples: int):
    #     try:
    #         self.utf.rows[index]["StreamAwbId"] = streamAwbId
    #         self.utf.rows[index]["numChannels"] = numChannels
    #         self.utf.rows[index]["numSamples"] = numSamples
    #     except StopIteration:
    #         raise KeyError(f"Row '{index}' does not exist in waveform list.")

    def add(self, awbId: int, awbFileId: int, numSamples: int, numChannels: int = 2, loop: bool = True):
        # TODO: this might not work out of the box for 3.10?
        # looks like they're all LoopFlag = 1 and NumChannels = 2 at first glance
        row = OrderedDict([
            UtfRowCell.build_tuple("NumChannels", numChannels, ValueTypeNibble.int8),
            UtfRowCell.build_tuple("LoopFlag", 1 if loop else 0, ValueTypeNibble.int8),
            UtfRowCell.build_tuple("NumSamples", util.i32swap(numSamples), ValueTypeNibble.int32),
            UtfRowCell.build_tuple("ExtensionData", -1, ValueTypeNibble.int16),
            UtfRowCell.build_tuple("StreamAwbPortNo", util.i16swap(awbId), ValueTypeNibble.int16),
            UtfRowCell.build_tuple("StreamAwbId", util.i16swap(awbFileId), ValueTypeNibble.int16)
        ])
        self.utf.rows.append(row)
        return len(self.utf.rows) - 1

    def pop(self, index: int):
        self.utf.rows.pop(index)
