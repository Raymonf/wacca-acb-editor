from dataclasses import dataclass
import hashlib
from io import BytesIO
from typing import Optional, OrderedDict, Union
from construct import Container, Lazy
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.awb import Awb
from atom_types.runtime.utf import Utf, UtfBlob
from pathlib import Path

class StreamAwbTable(TableBase):
    @dataclass
    class AwbInfo:
        name: str
        awb: Awb
        modified: bool = False
    
    def get_awb_path(self, name, rebuild=False):
        if rebuild:
            return (Path(self.awbDirectory) / "rebuild" / name).with_suffix(".awb")
        else:
            return (Path(self.awbDirectory) / name).with_suffix(".awb")
    
    def parse_awb(self, name):
        awbPath = self.get_awb_path(name)
        awb = Awb.parse_file(awbPath)
        self.awbList.append(self.AwbInfo(name, awb))
        self.awbListIndexByName[name] = len(self.awbList) - 1
        
    def build_awb(self, awb: Awb, name):
        awbPath = self.get_awb_path(name, True)
        awb.build_file(awbPath)
        with open(awbPath, "rb") as f:
            md5 = hashlib.md5()
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.digest()
        
    # Calculate the global waveform ID by adding the file counts of preceding AWBs
    def get_stream_awb_id(self, awbIndex: int, awbWaveformIndex: int):
        streamAwbId = 0
        for i in range(awbIndex):
            streamAwbId += len(self.awbs[i].awb.files)
        streamAwbId += awbWaveformIndex
        return streamAwbId
        
    def __init__(self, utf: Utf, awbDirectory: str):
        self.utf = utf
        self.awbDirectory = awbDirectory
        self.awbList = []
        self.awbListIndexByName = {}
        
        for row in self.utf.rows:
            self.parse_awb(row["Name"].value)
    
    def build_stream(self, stream):
        for i, row in enumerate(self.utf.rows):
            if self.awbList[i].modified:
                print(row["Name"].value)
                hash = self.build_awb(self.awbList[i].awb, row["Name"].value)
                row["Hash"] = UtfBlob("Hash", BytesIO(hash), 0, 16)
        super().build_stream(stream)
        
    @classmethod
    def parse_stream(cls, awbDirectory, stream, pos=None):
        return cls(Utf.parse_stream(stream, pos), awbDirectory)
    
    @classmethod
    def parse(cls, awbDirectory, data):
        return cls(Utf.parse(data), awbDirectory)

    def update_awb(self, index: int, name: str):
        try:
            self.utf.rows[index]["Name"] = name
        except KeyError:
            raise KeyError(f"Row '{index}' does not exist in Stream AWB list.")

    def add_awb_by_name(self, name: str):#, blob: UtfBlob):
        if name in [row["Name"] for row in self.utf.rows]:
            raise KeyError(f"AWB named '{name}' already exists in Stream AWB list.")

        self.parse_awb(name)
        rowData = Container({
            "Name": name
        })
        self.utf.rows.append(rowData)
        return len(self.utf.rows) - 1

    def pop_awb_by_name(self, name: str):
        try:
            index = self.awbListIndexByName[name]
            self.awbList.pop(index)
            self.awbListIndexByName.pop(name)
            self.utf.rows.pop(index)
        except KeyError:
            raise KeyError(f"AWB named '{name}' does not exist in Stream AWB list.")
        
    def pop_awb_by_index(self, index: int):
        try:
            self.awbList.pop(index)
            self.awbListIndexByName.pop(index)
            self.utf.rows.pop(index)
        except KeyError:
            raise KeyError(f"Row '{index}' does not exist in Stream AWB list.")
        
    def get_awb_index_by_name(self, name: str):
        try:
            return self.awbListIndexByName[name]
        except KeyError:
            raise KeyError(f"AWB named '{name}' does not exist in Stream AWB list.")
        
    def get_awb_name_by_index(self, index: int):
        try:
            return self.utf.rows[index]["Name"]
        except KeyError:
            raise KeyError(f"Row index '{index}' does not exist in Stream AWB list.")
        
    def update_waveform(self, awbName: str, waveformIndex: int, waveformData: Union[Lazy, bytes]):
        try:
            index = next(filter(lambda x: x[1]["Name"] == awbName, enumerate(self.utf.rows)))[0]
            try:
                self.awbList[index].files[waveformIndex] = waveformData
            except KeyError:
                raise KeyError(f"Waveform index '{waveformIndex}' does not exist in AWB named {awbName}.")
        except StopIteration:
            raise KeyError(f"AWB named '{awbName}' does not exist in Stream AWB list.")
        
    def append_waveform(self, awbName: str, waveformData: Union[Lazy, bytes]):
        try:
            index = next(filter(lambda x: x[1]["Name"] == awbName, enumerate(self.utf.rows)))[0]
            self.awbList[index].files.append(waveformData)
        except StopIteration:
            raise KeyError(f"AWB named '{awbName}' does not exist in Stream AWB list.")
        
    def insert_waveform(self, awbName: str, waveformIndex: int, waveformData: Union[Lazy, bytes]):
        try:
            index = next(filter(lambda x: x[1]["Name"] == awbName, enumerate(self.utf.rows)))[0]
            self.awbList[index].files.insert(waveformIndex, waveformData)
        except StopIteration:
            raise KeyError(f"AWB named '{awbName}' does not exist in Stream AWB list.")
        
    def pop_waveform(self, awbName: str, waveformIndex: int):
        try:
            index = next(filter(lambda x: x[1]["Name"] == awbName, enumerate(self.utf.rows)))[0]
            try:
                self.awbList[index].files.pop(waveformIndex)
            except KeyError:
                raise KeyError(f"Waveform index '{waveformIndex}' does not exist in AWB named {awbName}.")
        except StopIteration:
            raise KeyError(f"AWB named '{awbName}' does not exist in Stream AWB list.")