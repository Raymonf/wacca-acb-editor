from io import BytesIO

from construct import Container, GreedyBytes, Lazy
from construct.core import evaluate, Bytes
from atom_types.file.awb_file import Awb_File, Awb_File_Header

class Awb:
    def __init__(self, tree: Container):
        self.tree = tree
        # self.headerUpToDate = True
    
    @classmethod
    def parse_stream(cls, stream):
        tree = Awb_File.parse_stream(stream)
        return cls(tree)
    
    @classmethod
    def parse_file(cls, filename):
        f = open(filename, 'rb')
        return cls.parse_stream(f)
    
    def build_stream(self, stream) -> None:
        Awb_File.build_stream(self.tree, stream)
    
    def build_header_stream(self, stream) -> None:
        Awb_File_Header.build_stream(self.tree.header, stream)
        
    def build_file(self, filename) -> None:
        with open(filename, 'wb') as f:
            self.build_stream(f)
    
    def getFile(self, index: int) -> bytes:
        return evaluate(self.tree.files[index])
    
    def overwriteFile(self, index: int, file) -> None:
        buf = file.read()
        self.tree.files[index] = Bytes(len(buf)).parse(buf)
        # self.headerUpToDate = False
    
    def appendFile(self, file) -> int:
        buf = file.read()
        self.tree.files.append(Bytes(len(buf)).parse(buf))
        # self.headerUpToDate = False
        return len(self.tree.files) - 1
    
    def popFile(self, index: int) -> None:
        self.tree.files.pop(index)
        # self.headerUpToDate = False