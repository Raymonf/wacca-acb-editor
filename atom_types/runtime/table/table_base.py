import io
from atom_types.runtime.utf import Utf

class TableBase:
    def __init__(self, utf):
        self.utf = utf
    
    @classmethod
    def parse_stream(cls, stream, pos=None):
        return cls(Utf.parse_stream(stream, pos))
    
    @classmethod
    def parse(cls, data):
        return cls(Utf.parse(data))
    
    @classmethod
    def parse_file(cls, filename):
        with open(filename, 'rb') as f:
            return cls.parse_stream(f)
    
    def build(self):
        stream = io.BytesIO()
        self.build_stream(stream)
        return stream
    
    def build_stream(self, stream):
        self.utf.build_stream(stream)
        
    def update(self, *args, **kwargs):
        raise NotImplementedError()
        
    def add(self, *args, **kwargs):
        raise NotImplementedError()
        
    def pop(self, *args, **kwargs):
        raise NotImplementedError()