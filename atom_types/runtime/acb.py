
from collections import namedtuple
from io import BytesIO
from typing import List, Optional, Type
from typing_extensions import Annotated

from construct import Array, Bytes, Int16ub
from atom_types.runtime.table.cue import CueTable
from atom_types.runtime.table.cue_name import CueNameTable
from atom_types.runtime.table.sequence import SequenceTable
from atom_types.runtime.table.stream_awb import StreamAwbTable
from atom_types.runtime.table.synth import SynthTable
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.table.track import TrackTable
from atom_types.runtime.table.track_event import TrackEventTable
from atom_types.runtime.table.waveform import WaveformTable

from atom_types.runtime.utf import Utf, UtfBlob
from atom_types.runtime.awb import Awb
from atom_types.file.awb_file import Awb_File_Header

# Wrapped name              Internal Name       Used/Updated/Unique/RowID->RefID
# CueTable                  Cue                 Y/Y/Y/Cue(329)->Seq(329)
# CueNameTable              CueName             Y/Y/Y/Cue(329)
# WaveformTable             Waveform            Y/Y/Y/Wav(652)->Awb
# AisacTable                                    N
# GraphTable                                    N
# GlobalAisacReferenceTable                     N
# AisacNameTable                                N
# SynthTable                Synth               Y/Y/Y/Synth(656)->Wav(652) (ReferenceItems use Wav Ids; there are some duplicates that look accidental)
# SeqCommandTable           SequenceCommand     Y/N?
# TrackTable                Track               Y/Y/Y/Track(656)->Synth(656) (Controls audio target output via CommandIndex column)
# SequenceTable             Sequence            Y/Y/Y/Seq(329)->Track(656) (Seems to control grouping of the audio track files)
# AisacControlNameTable                         N
# AutoModulationTable                           N
# StreamAwbTocWorkOld                           N
# AwbFile                                       N
# CueLimitWorkTable                             N
# AcbGuid                                       Y/N
# StreamAwbHash             StreamAwb           Y/Y/Y (Contains AWB filenames and hashes)
# StreamAwbTocWork_Old                          N
# StringValueTable          Strings             Y/N
# OutsideLinkTable                              N
# BlockSequenceTable                            N
# BlockTable                                    N
# EventTable                                    N
# ActionTrackTable                              N
# AcfReferenceTable         AcfReference        Y/N
# WaveformExtensionDataTable WaveformExtensionData Y/N
# BeatSyncInfoTable                             N
# TrackCommandTable                             Y/N
# SynthCommandTable                             N
# TrackEventTable           TrackEvent          Y/Y/Y/Track(656)
# SeqParameterPalletTable                       N
# TrackParameterPalletTable                     N
# SynthParameterPalletTable                     N
# SoundGeneratorTable                           N
# PaddingArea                                   N
# StreamAwbTocWork                              Y/N/N (A mystery. A large block of 0s with a non-fixed random-seeming size)
# StreamAwbAfs2Header       StreamAwbHeader     Y/Y/N

class AwbTables:
    awb_tables = {
        "cueNames": CueNameTable,
        "cues": CueTable,
        "sequences": SequenceTable,
        "synths": SynthTable,
        "trackEvents": TrackEventTable,
        "tracks": TrackTable,
        "waveforms": WaveformTable
    }
    
    def parseTable(self, utf: Utf, attrName: str, columnName: str, type: Type[TableBase]):
        print(f"Parse {type.__name__}")
        setattr(self, attrName, type.parse(utf.get(0, columnName).read()))
        
    def __init__(self, awbDirectory: str, utf: Utf):
        # Parse all tables
        for name, type in self.awb_tables.items():
            self.parseTable(utf, name, type.__name__, type)
        self.streamAwbs = StreamAwbTable.parse(awbDirectory, utf.get(0, "StreamAwbHash").read())
        
    def buildTable(self, utf: Utf, attrName: str, columnName: str, type: Type[TableBase]):
        print(f"Build {type.__name__}")
        stream = getattr(self, attrName).build()
        blob = UtfBlob(columnName, stream, 0, len(stream.getbuffer()))
        utf.set(0, columnName, blob)
        
    def buildAll(self, utf: Utf):
        for name, type in self.awb_tables.items():
            self.buildTable(utf, name, type.__name__, type)
        stream = self.streamAwbs.build()
        blob = UtfBlob("StreamAwbHash", stream, 0, len(stream.getbuffer()))
        utf.set(0, "StreamAwbHash", blob)
    
class Acb(TableBase):
    def __init__(self, awbDirectory: str, utf: Utf):
        self.utf = utf
        self.awbDirectory = awbDirectory
        self.tables = AwbTables(awbDirectory, utf)
        
    def build_stream(self, stream):
        self.tables.buildAll(self.utf)
        super().build_stream(stream)
        
    @classmethod
    def parse_stream(cls, awbDirectory, stream, pos=None):
        return cls(awbDirectory, Utf.parse_stream(stream, pos))
    
    def update_song(self, awbWaveformIndex: int, awbName: Optional[str] = None,
                    awbIndex: Optional[int] = None, cueName: Optional[str] = None,
                    audioFileSpeaker: Optional[str] = None, audioFileSpeakerSampleCount: Optional[int] = None,
                    audioFileHeadphone: Optional[str] = None, audioFileHeadphoneSampleCount: Optional[int] = None):
        if (audioFileSpeaker is None) != (audioFileSpeakerSampleCount is None) or \
            (audioFileHeadphone is None) != (audioFileHeadphoneSampleCount is None):
                raise ValueError("Audio file path and sample count arguments must be set together.")
            
        if (awbName is None) != (awbIndex is None):
            raise ValueError("Must specify exactly one of either [awbName, awbIndex].")
        
        if awbIndex is None:
            awbIndex = self.streamAwbs.get_awb_index_by_name(awbName)
        elif awbName is None:
            awbName = self.streamAwbs.get_awb_name_by_index(awbIndex)
        
        streamAwbId = self.streamAwbs.get_stream_awb_id(awbIndex, awbWaveformIndex)
        
        currentCueName = None
        try:
            currentCueName = self.cueNames.get(streamAwbId)
        except KeyError:
            print(f"update_song() Warning: StreamAwbId {streamAwbId} (AWB: {awbName}:{awbWaveformIndex}) has no corresponding cue name in ACB.")
        
        if cueName is not None:
            if currentCueName is not None:
                self.cueNames.u
        
    def add(self, referenceItems: Annotated[List[int], 2]):
        rowData = {
            "ReferenceItems": Array(2, Int16ub).build(referenceItems)
        }
        self.utf.rows.append(rowData)
        return len(self.utf.rows) - 1
        
    def insert(self, index: int, referenceItems: Annotated[List[int], 2]):
        rowData = {
            "ReferenceItems": Array(2, Int16ub).build(referenceItems)
        }
        self.utf.rows.insert(index, rowData)
        
    def pop(self, index: int):
        self.utf.rows.pop(index)