from construct import *
from construct.core import *

# PointerSize = Enum(Byte,
#     uint16 = 2,
#     uint32 = 4
# )

# def AwbPointer(pointerSize: PointerSize):
#     return Switch(pointerSize, { PointerSize.uint16:Int16ul, PointerSize.uint32:Int32ul })

def AwbPointer(pointerSize):
    return BytesInteger(pointerSize, signed=False, swapped=True)

class AwbFilesArray(Construct):
    def __init__(self, alignmentSize, pointerArray: RawCopy, pointerType):
        super().__init__()
        self.pointerArray = pointerArray
        self.pointerType = pointerType
        self.alignmentSize = alignmentSize

    def _parse(self, stream, context, path):
        alignmentSize = evaluate(self.alignmentSize, context)
        pointerArray = evaluate(self.pointerArray.value, context)
        def seek_to_alignment():
            tell = stream_tell(stream, path)
            if tell % alignmentSize > 0:
                numPadBytes = alignmentSize - (tell % alignmentSize)
                stream_seek(stream, numPadBytes, 1, path)
                
        retlist = ListContainer()
        # Keep a second iterator advanced to the next element.
        # When it reaches the end we will be on the second-to-last element (the last start-pointer) of our main iterator.
        nextIter = iter(pointerArray)
        nextIter.__next__()
        for i, pointer in enumerate(pointerArray):
            try:
                nextPointer = nextIter.__next__()
                context._index = i
                stream_seek(stream, pointer, 0, path)
                seek_to_alignment()
                parsed = Lazy(Bytes(nextPointer - stream_tell(stream, path)))._parsereport(stream, context, path)
                retlist.append(parsed)
            except StopIteration:
                break
        return retlist

    def _build(self, obj, stream, context, path):
        alignmentSize = evaluate(self.alignmentSize, context)
        pointerArray = self.pointerArray
        retList = ListContainer()
        pointerList = ListContainer()
        
        def pad_stream():
            tell = stream_tell(stream, path)
            if tell % alignmentSize > 0:
                numPadBytes = alignmentSize - (tell % alignmentSize)
                stream_write(stream, b"\x00" * numPadBytes, numPadBytes, path)
            else:
                numPadBytes = 0
            return tell + numPadBytes
        
        pointerList.append(stream_tell(stream, path))
        
        # Pad until first alignment
        pad_stream()
        
        for i, e in enumerate(obj):
            e = e() if callable(e) else e
            pad_stream()
            context._index = i
            buildret = Bytes(len(e))._build(e, stream, context, path)
            retList.append(buildret)
            pointerList.append(stream_tell(stream, path))
        
        # Seek to pointer list data and overwrite with populated list
        offset = evaluate(pointerArray.offset1, context)
        fallback = stream_tell(stream, path)
        stream_seek(stream, offset, 0, path)
        Array(len(pointerList), self.pointerType)._build(pointerList, stream, context, path)
        stream_seek(stream, fallback, 0, path)
        return retList
        
class CueIdsAdapter(Adapter):
    def _decode(self, obj, context, path):
        return None

    def _encode(self, obj, context, path):
        obj = range(len(context._.files))
        return obj
        
Awb_File_Header = Struct(
    "magic" / Const(b"AFS2"),
    "unk0" / Byte,
    "pointerSize" / Int8ul,
    "unk1" / Byte,
    "unk2" / Byte,
    "count" / Rebuild(Int32ul, len_(this._.files)),
    "alignmentSize" / Int32ul,
    "cueIds" / CueIdsAdapter(Int16ul[this.count]),
    "pointers" / RawCopy(Array(this.count + 1, AwbPointer(this.pointerSize))),
)

Awb_File = Struct(
    "header" / Awb_File_Header,
    "files" / AwbFilesArray(this.header.alignmentSize, this.header.pointers, AwbPointer(this.header.pointerSize))
    
    # "pointerSize" / PointerSize,
    # "pointers" / RawCopy(Array(this.count + 1, AwbPointer(this.pointerSize))),
    # "files" / AwbFilesArray(this.alignmentSize, this.pointers, AwbPointer(this.pointerSize))
)