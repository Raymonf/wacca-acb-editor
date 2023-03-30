import io
import logging
from typing import List, Type
from construct import Array, Int16ub
from atom_types.runtime.table.cue import CueTable
from atom_types.runtime.table.cue_name import CueNameTable
from atom_types.runtime.table.sequence import SequenceTable
from atom_types.runtime.table.stream_awb import StreamAwbTable
from atom_types.runtime.table.stream_awb_header import StreamAwbAfs2Header
from atom_types.runtime.table.synth import SynthTable
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.table.track import TrackTable
from atom_types.runtime.table.track_event import TrackEventTable
from atom_types.runtime.table.waveform import WaveformTable
from atom_types.runtime.utf import Utf, UtfBlob

# Wrapped name              Internal Name       Used/Updated/Unique/RowID->RefID
# CueTable                  Cue                 Y/Y/Y/Cue(329)->Seq(329)
# CueNameTable              CueName             Y/Y/Y/Seq(329)
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
        "waveforms": WaveformTable,
        "streamAwbHeaders": StreamAwbAfs2Header
    }
    
    def parseTable(self, utf: Utf, attrName: str, columnName: str, type: Type[TableBase]):
        self.log.debug(f"Parse {type.__name__}")
        setattr(self, attrName, type.parse(utf.get(0, columnName).read()))
        
    def __init__(self, awbDirectory: str, utf: Utf):
        self.log = logging.getLogger("awb_tables")

        # Parse all tables
        for name, type in self.awb_tables.items():
            self.parseTable(utf, name, type.__name__, type)
        self.streamAwbs = StreamAwbTable.parse(awbDirectory, utf.get(0, "StreamAwbHash").read())
        
    def buildTable(self, utf: Utf, attrName: str, columnName: str, type: Type[TableBase]):
        self.log.debug(f"Build {type.__name__}")
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
    tables: AwbTables

    def __init__(self, awbDirectory: str, utf: Utf):
        self.log = logging.getLogger("acb")
        self.utf = utf
        self.awbDirectory = awbDirectory
        self.tables = AwbTables(awbDirectory, utf)
        
    def build_stream(self, stream):
        # self.sort_cue_name_table() # sort the cue name table now that we're about to build
        self.tables.buildAll(self.utf)
        super().build_stream(stream)
        
    @classmethod
    def parse_stream(cls, awbDirectory, stream, pos=None):
        return cls(awbDirectory, Utf.parse_stream(stream, pos))

    def add_song_to_awb(self, cue_name: str, awb_id: int, awb_file_id: int, num_samples: int, length_ms: int, command_index: int = 1):
        waveform_id_1 = self.tables.waveforms.add(awb_id, awb_file_id, num_samples) # HP
        waveform_id_2 = self.tables.waveforms.add(awb_id, awb_file_id, num_samples) # SP
        synth_id_1 = self.tables.synths.add(waveform_id_1)
        synth_id_2 = self.tables.synths.add(waveform_id_2)
        track_event_id_1 = self.tables.trackEvents.add(synth_id_1)
        track_event_id_2 = self.tables.trackEvents.add(synth_id_2)
        track_id_1 = self.tables.tracks.add(track_event_id_1, "headphone")
        self.log.debug(f"Add Track 1 -> event ID {track_event_id_1}, headphone")
        track_id_2 = self.tables.tracks.add(track_event_id_2, "speaker")
        self.log.debug(f"Add Track 2 -> event ID {track_event_id_2}, speaker")

        # CommandIndex usually 1, but depends on version. 0 on 3.10; 1 on 3.07.
        # 0 in 3.07 seems to be "play nothing" or something
        sequence_id = self.tables.sequences.add(2, [track_id_1, track_id_2], command_index)
        self.log.debug(f"Add Sequence -> ID {sequence_id}, track IDs [{track_id_1}, {track_id_2}]")

        cue_id = self.tables.cues.add(sequence_id, length_ms) # length = duration in ms
        self.log.debug(f"Add Cue -> ID {cue_id}, sequence ID = {sequence_id}, length in MS = {length_ms}")

        cue_name_id = self.tables.cueNames.add(cue_id, cue_name)
        self.log.debug(f"Add Cue Name '{cue_name}' -> ID {cue_name_id}, cue ID = {cue_id}")

    def update_streaming_awb_headers(self, remap: dict[str, str] = None):
        for awb_id, awb in enumerate(self.tables.streamAwbs.awbList):
            self.log.debug(f"Updating header for {awb.name}.awb (AWB ID = {awb_id})")
            # ugly ugly ugly
            # TODO: refactor?
            header = io.BytesIO()
            awb_file_count = len(awb.awb.tree.files)
            pull_bytes = 16 + (awb_file_count * 2) + ((awb_file_count + 1) * 4)
            if remap is not None and awb.name + ".awb" in remap:
                awb_path = self.awbDirectory + "/" + remap[awb.name + ".awb"]
            else:
                awb_path = self.awbDirectory + "/" + awb.name + ".awb"

            with io.open(awb_path, "rb") as awb_file:
                header.write(awb_file.read(pull_bytes))
            header.write(Int16ub.build(0)) # some padding or something
            header.seek(0) # back to beginning so we can read
            # update Header = real header size + 2 bytes
            self.tables.streamAwbHeaders.update(awb_id, UtfBlob("StreamAwbAfs2Header_NoPrepad", header, 0, pull_bytes + 2))

    def sort_cue_name_table(self):
        """Destructively sorts CueNameTable rows by CueName.
        Called after all work is done (by build_stream)."""
        self.tables.cueNames.utf.rows.sort(key=lambda x: x['CueName'].value)

    # def update_song(self, awbWaveformIndex: int, awbName: Optional[str] = None,
    #                 awbIndex: Optional[int] = None, cueName: Optional[str] = None,
    #                 audioFileSpeaker: Optional[str] = None, audioFileSpeakerSampleCount: Optional[int] = None,
    #                 audioFileHeadphone: Optional[str] = None, audioFileHeadphoneSampleCount: Optional[int] = None):
    #     if (audioFileSpeaker is None) != (audioFileSpeakerSampleCount is None) or \
    #         (audioFileHeadphone is None) != (audioFileHeadphoneSampleCount is None):
    #             raise ValueError("Audio file path and sample count arguments must be set together.")
    #
    #     if (awbName is None) != (awbIndex is None):
    #         raise ValueError("Must specify exactly one of either [awbName, awbIndex].")
    #
    #     if awbIndex is None:
    #         awbIndex = self.streamAwbs.get_awb_index_by_name(awbName)
    #     elif awbName is None:
    #         awbName = self.streamAwbs.get_awb_name_by_index(awbIndex)
    #
    #     streamAwbId = self.streamAwbs.get_stream_awb_id(awbIndex, awbWaveformIndex)
    #
    #     currentCueName = None
    #     try:
    #         currentCueName = self.cueNames.get(streamAwbId)
    #     except KeyError:
    #         print(f"update_song() Warning: StreamAwbId {streamAwbId} (AWB: {awbName}:{awbWaveformIndex}) has no corresponding cue name in ACB.")
    #
    #     if cueName is not None:
    #         if currentCueName is not None:
    #             self.cueNames.u
        
    # def add(self, referenceItems: Annotated[List[int], 2]):
    #     rowData = {
    #         "ReferenceItems": Array(2, Int16ub).build(referenceItems)
    #     }
    #     self.utf.rows.append(rowData)
    #     return len(self.utf.rows) - 1
    #
    # def insert(self, index: int, referenceItems: Annotated[List[int], 2]):
    #     rowData = {
    #         "ReferenceItems": Array(2, Int16ub).build(referenceItems)
    #     }
    #     self.utf.rows.insert(index, rowData)
        
    # def pop(self, index: int):
    #     self.utf.rows.pop(index)