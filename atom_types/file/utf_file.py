from io import BytesIO
import re
import string
from construct import *
from construct.core import *

from atom_types.file.awb_file import Awb_File_Header

ColumnTypeNibble = Enum(Nibble,
    constant = 3,
    variable = 5
)

ValueTypeNibble = Enum(Nibble,
    int8 = 0x00,
    uint8 = 0x01,
    int16 = 0x02,
    uint16 = 0x03,
    int32 = 0x04,
    uint32 = 0x05,
    int64 = 0x06,
    uint64 = 0x07,
    float = 0x08,
    double = 0x09,
    string = 0x0a,
    blob = 0x0b,
    guid = 0x0c
)

Utf_File = Struct()
def UtfField(valueTypeNibble: ValueTypeNibble, header):
    return Switch(valueTypeNibble, {
        ValueTypeNibble.int8:Int8sl,
        ValueTypeNibble.uint8:Int8ub,
        ValueTypeNibble.int16:Int16sl,
        ValueTypeNibble.uint16:Int16ub,
        ValueTypeNibble.int32:Int32sl,
        ValueTypeNibble.uint32:Int32ub,
        ValueTypeNibble.int64:Int64sl,
        ValueTypeNibble.uint64:Int64ub,
        ValueTypeNibble.float:Float32l,
        ValueTypeNibble.double:Float64l,
        ValueTypeNibble.string:Struct(
            "stringPointer" / Default(Int32ub, 0),
            "string" / Optional(If(this._parsing, Pointer(this.stringPointer + header.stringsPointer,
                CString(encoding="utf8")))),
        ),
        ValueTypeNibble.blob:Struct(
            "blobPointer" / Default(Int32ub, 0),
            "blobPointerAbsolute" / If(this._parsing, Computed(lambda ctx: ctx.blobPointer + header.blobsPointer)),
            # "blobLengthPtr" / Tell,
            "blobLength" / Default(Int32ub, 0),
            "blobSignature" / Optional(If(this._parsing, Pointer(this.blobPointer + header.blobsPointer, Bytes(4)))),
            # "signatureString" / Computed(lambda ctx: re.sub(r'[^\x30-\x7f]', '?', ctx.blobSignature.decode(encoding="ascii", errors="replace") if ctx._parsing else None)),
            # If(this._building, Probe(this.blob)),
            # "blobType" / If(this._parsing, 
            #     If(this.blobLength > 0,
            #         Pointer(this.blobPointer + header.blobsPointer,
            #             Switch(lambda ctx: ctx.blobSignature,
            #                 {
            #                     b"@UTF": Computed(lambda ctx: "utf"),
            #                     b"AFS2": Computed(lambda ctx: "awb_header")
            #                 },
            #                 default=Computed(lambda ctx: "raw")
            # )))),
            # # Probe(this.blobType),
            # "blob" / If(this._parsing,
            #     If(this.blobLength > 0,
            #         Pointer(this.blobPointer + header.blobsPointer,
            #             RawCopy(Switch(lambda ctx: ctx.blobSignature,
            #                 {
            #                     b"@UTF": LazyBound(lambda: Utf_File),
            #                     b"AFS2": Awb_File_Header
            #                 },
            #                 default=Bytes(this.blobLength)
            # ))))),
            # "blob" / If(this._parsing,
            #     If(this.blobLength > 0,
            #         Pointer(this.blobPointer + header.blobsPointer, Lazy(Bytes(this.blobLength))
            # ))),
            # "blobLength" / Pointer(this.blobLengthPtr, Rebuild(Int32ub, lambda ctx: len(ctx.blob.data) if "blob" in ctx and ctx.blob else 0)),
        ),
        ValueTypeNibble.guid:Bytes(16)
    })

Types = BitStruct(
    "column" / ColumnTypeNibble,
    "value" / ValueTypeNibble
)
    
class HeaderPointer(Adapter):
    def _decode(self, obj, context, path):
        return obj + context._.startPointer + 8
    
    def _encode(self, obj, context, path):
        return obj # This is never built, so don't bother changing the value
    
# def getStringPointer(ctx, name):
#     if not "_stringsListIo" in ctx:
#         ctx["_stringsListIo"] = io.BytesIO()
#         ctx["_stringsList"] = ListContainer()
#         ctx["_stringsListPointers"] = ListContainer()
        
#     #print(f"getStringPointer {ctx}")
#     try:
#         stringIndex = ctx["_stringsList"].index(name)
#         return ctx["_stringsListPointers"][stringIndex]
#     except ValueError:
#         #print(f"append {name}")
#         ctx["_stringsList"].append(name)
#         pointer = stream_tell(ctx["_stringsListIo"], None)
#         ctx["_stringsListPointers"].append(pointer)
#         CString(encoding="utf8")._build(name, ctx["_stringsListIo"], ctx, None)
#         return pointer

# def getBlobPointer(ctx, uniqueName, blob):
#     # print(f"getBlobPointer len:{len(blob)} name:{uniqueName}")
#     if len(blob) == 0:
#         return 0
    
#     if not "_blobsListEntries" in ctx:
#         # ctx["_blobsListIo"] = io.BytesIO()
#         ctx["_blobsListPointers"] = Container()
#         ctx["_blobsListEntries"] = Container()
    
#     #print(ctx["_blobsListPointers"].__dict__)
#     try:
#         return ctx["_blobsListPointers"][uniqueName]
#     except KeyError:
#         # pointer = stream_tell(ctx["_blobsListIo"], None)
#         # ctx["_blobsListPointers"][uniqueName] = pointer
#         # Bytes(len(blob))._build(blob, ctx["_blobsListIo"], ctx, None)
#         # return pointer
#         ctx["_blobsListEntries"][uniqueName] = blob
#         return 0
        
Utf_File_Column = Struct(
    # If(this._building, Probe(this)),
    "types" / Types,
    # If(this._building, Probe(this)),
    "namePointer" / Int32ub,
    # If(this._building, Probe(this)),
    "name" / If(this._parsing, Pointer(this.namePointer + this._.header.stringsPointer,
        CString(encoding="utf8"))),
    # If(this._building, Probe(this)),
    "constant" / If(this.types.column == ColumnTypeNibble.constant, UtfField(this.types.value, this._._.header)),
    "end" / Computed(this._index)
)
        
# RowS = Struct(
#     "types" / Types * setFoundVarColumnParam,
#     # If parsing, get the pointer value first. This needs to be regenerated at the end of building.
#     "namePointer" / IfThenElse(this._building, Pass, Int32ub),
#     "name" / IfThenElse(this._building, Pass,#Computed(lambda ctx: appendToStringsList(ctx)),
#                         Pointer(this.namePointer + this._.startPointer + this._.header.stringsPointer,
#                                 CString(encoding="utf8"))),
#     "namePointer" / If(this._building, Rebuild(Int32ub, lambda ctx: getStringPointer(ctx._, ctx.name))),
#     "constant" / If(this.types.column == ColumnTypeNibble.constant, UtfField(this.types.value)),
#     "end" / Computed(this._index)
# )

class Row(Construct):
    def __init__(self, columns):
        self.columns = columns
        super().__init__()

    def _parse(self, stream, context, path):
        columns = evaluate(self.columns, context)
        result = Container()
        for column in columns:
            # print(f"row_{evaluate(this._index, context)}:{column.name}")
            if column.types.column != ColumnTypeNibble.variable:
                continue
            result[column.name] = UtfField(column.types.value, f"row_{evaluate(this._index, context)}:{column.name}", evaluate(this.header, context))._parsereport(stream, context, path)
        return result

    # def _build(self, obj, stream, context, path):
    #     columns = evaluate(self.columns, context)
    #     result = Container()
        
    #     for column in columns:
    #         if column.types.column != ColumnTypeNibble.variable:
    #             continue
    #         # print(f"column {column.name} tell {stream_tell(stream, path)}")
    #         result[column.name] = UtfField(column.types.value, f"row_{evaluate(this._index, context)}:{column.name}", evaluate(this.header, context))._build(obj[column.name], stream, context, path)
            
    #     return result
    
# class BlobArray(Construct):
#     def __init__(self, pointers, entries, alignmentSize = 32):
#         super().__init__()
#         self.pointers = pointers
#         self.entries = entries
#         self.alignmentSize = alignmentSize

#     def _parse(self, stream, context, path):
#         return None

#     def _build(self, obj, stream, context, path):
#         alignmentSize = evaluate(self.alignmentSize, context)
#         pointers = evaluate(self.pointers, context)
#         # print(pointers)
#         entries = evaluate(self.entries, context)
        
#         def pad_stream():
#             tell = stream_tell(stream, path)
#             numPadBytes = alignmentSize - (tell % alignmentSize)
#             stream_write(stream, b"\x00" * numPadBytes, numPadBytes, path)
#             return tell + numPadBytes
        
#         pad_stream()
#         start = stream_tell(stream, path)
#         context.blobsPointer = start
#         retList = ListContainer()
        
#         firstLoop = True
#         for entryName in entries:
#             if not firstLoop:
#                 pad_stream()
#             firstLoop = False
#             pointer = stream_tell(stream, path) - start
#             pointers[entryName] = pointer
#             buildret = Bytes(len(entries[entryName]))._build(entries[entryName], stream, context, path)
#             retList.append(buildret)
            
#         return retList

Utf_File_Header = Struct(
    #Probe(lookahead=32),
    "magic" / Const(b"@UTF"),
    "size" / Rebuild(Int32ub, this._.endPointer - this._.startPointer - 8),
    "version" / Int16ub,
    "rowsPointer" / Rebuild(HeaderPointer(Int16ub), this._.rowsPointer - this._.startPointer - 8),
    "stringsPointer" / Rebuild(HeaderPointer(Int32ub), this._.stringsPointer - this._.startPointer - 8),
    "name" / If(this._parsing, Pointer(this.stringsPointer, CString("utf8"))),
    "blobsPointer" / Rebuild(HeaderPointer(Int32ub), this._.blobsPointer - this._.startPointer - 8),
    "unk" / Int32ub,
    "columnCount" / Rebuild(Int16ub, len_(this._.columns)),
    "rowSize" / Int16ub,
    "rowCount" / Rebuild(Int32ub, len_(this._.rows))
)

Utf_File = Struct(
    # If(this._building, Probe(this.header, lookahead=32)),
    "startPointer" / Tell,
    "header" / Utf_File_Header,
    # If(this._building, Probe(this.header)),
    "columnsPointer" / Tell,
    "columns" / IfThenElse(this._building, GreedyRange(Utf_File_Column), RepeatUntil(
        lambda x,lst,ctx: ctx._index + 1 == evaluate(this.header.columnCount, ctx), Utf_File_Column)),
    # Probe(this.columns),
    # If(this._building, Probe(this.columns)),
    # "rowsPointer" / Tell,
    # "rows" / RawCopy(IfThenElse(this._building,
    #     GreedyBytes, IfThenElse(lambda ctx: ctx.header.rowSize > 0 and ctx.header.rowCount > 0, RepeatUntil(
    #     lambda x,lst,ctx: ctx._index + 1 == evaluate(this.header.rowCount, ctx), Row(this.columns)), Pass))),
    # Probe(this.rows),
    # If(this._building, Probe(this.rows)),
    # "stringsPointer" / Tell,
    # "strings" / If(this._building, GreedyBytes),
    # Probe(this.strings),
    # If(this._building, Probe(this.strings)),
    # Pointer(this.stringsPointer, Probe(this.stringsPointer, lookahead=32)),
    # "blobsPointer" / Tell,
    # "blobs" / If(this._building, Rebuild(GreedyBytes, lambda ctx: ctx["blobsListIo"].getvalue() if "blobsListIo" in ctx else bytes([]))),
    # "blobs" / If(this._building, GreedyBytes),
    # Probe(this._blobsListPointers),
    # If(this._building, Probe(this.blobs)),
    # "endPointer" / Tell,
    "header" / Pointer(this.startPointer, Utf_File_Header),
    # Probe(this.header),
)