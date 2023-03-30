from __future__ import annotations
import io
from typing import OrderedDict
from construct import Bytes, CString, Container, GreedyBytes, ListContainer, Pointer

from atom_types.runtime import util
from atom_types.file.utf_file import Utf_File, UtfField, ValueTypeNibble, ColumnTypeNibble


# class FieldOrigin:
#     def __init__(self, column: str, row=None):
#         self.column = column
#         self.row = row # None if the column type is Constant

#     def __eq__(self, other) -> bool:
#         return self.column == other.column and self.row == other.row

#     def __hash__(self) -> int:
#         return hash(repr(self))

# class UtfBlob:
#     class Type(Enum):
#         RAW = auto()
#         UTF = auto()
#         AWB_HEADER = auto()

#         @classmethod
#         def from_signature(cls, value: bytes):
#             options = {
#                 b"@UTF": cls.UTF,
#                 b"AFS2": cls.AWB_HEADER
#             }
#             if value in options:
#                 return options[value]
#             else:
#                 return cls.RAW

#     def __init__(self, data: bytes, type: Type):
#         self.data = data
#         self.type = type

# class UtfBlobLocation:
#     def __init__(self, stream, pos, size) -> None:
#         self.stream = stream
#         self.pos = pos
#         self.size = size

def pad_stream_to_alignment(stream, alignment):
    tell = stream.tell()
    numPadBytes = alignment - (tell % alignment)
    stream.write(b"\x00" * numPadBytes)
    return tell + numPadBytes


class UtfBlob:
    def __init__(self, columnName, stream, pos, length):
        self.stream = stream
        self.pos = pos
        self.length = length
        self.columnName = columnName

        signature = self.read(4)
        if (b"UTF" in signature or b"AFS2" in signature or
                columnName == "AcfMd5Hash" or columnName == "AcbGuid" or columnName == "StreamAwbTocWork"):
            self.shouldPrepad = True
            # self.postPadding = 4 - (length % 4) if length % 4 else 0
        else:
            self.shouldPrepad = False
            # self.postPadding = 0

        # hack
        if columnName == "StreamAwbAfs2Header_NoPrepad":
            self.shouldPrepad = False
        # print(f"signature: {signature}, columnName: {columnName}, prepad: {self.shouldPrepad}")

    def read(self, length=None):
        originalPos = self.stream.tell()
        self.stream.seek(self.pos)
        data = self.stream.read(length or self.length)
        self.stream.seek(originalPos)
        return data

    def build_stream(self, outStream):
        if self.shouldPrepad:
            # print(f"prepadding {self.columnName}")
            pad_stream_to_alignment(outStream, 32)
        pointer = outStream.tell()
        self.stream.seek(self.pos)
        Bytes(self.length).build_stream(self.stream.read(self.length), outStream)
        return pointer

    def build(self):
        stream = io.BytesIO()
        self.build_stream(stream)
        return stream


class UtfColumn:
    def __init__(self, name: str, types, constant):
        self.name = name
        self.types = types
        self.constant = constant


class UtfRowCell:
    def __init__(self, column, value):
        self.column = column
        self.value = value

    @classmethod
    def build(cls, name: str, value, value_type: ValueTypeNibble, column_type: ColumnTypeNibble = ColumnTypeNibble.variable) -> UtfRowCell:
        types = Container(column=column_type, value=value_type)
        column = UtfColumn(name, types, None)
        return cls(column, value)

    @classmethod
    def build_tuple(cls, name: str, value, value_type: ValueTypeNibble, column_type: ColumnTypeNibble = ColumnTypeNibble.variable) -> (str, UtfRowCell):
        return name, cls.build(name, value, value_type, column_type)


class Utf:
    def __init__(self, name, columns, rows, tree: Container):
        self.name = name
        self.columns = columns
        self.rows = rows
        self.tree = tree

    @classmethod
    def parse(cls, data):
        stream = io.BytesIO(data)
        return cls.parse_stream(stream)

    @classmethod
    def parse_stream(cls, stream, pos=None):
        if pos:
            stream.seek(pos)

        tree = Utf_File.parse_stream(stream)
        runtimeColumns = OrderedDict()
        runtimeRows = []

        def make_runtime_value(columnName, valueType, field):
            if valueType == "string" and field.string:
                return field.string
            elif valueType == "blob":
                if "blobLength" in field and field.blobLength:
                    return UtfBlob(columnName, stream, field.blobPointerAbsolute, field.blobLength)
                else:
                    return None
            else:
                return field

        for column in tree.columns:
            if column.types.column == "constant":
                colValue = make_runtime_value(column.name, column.types.value, column.constant)
            else:
                colValue = None
            runtimeColumns[column.name] = UtfColumn(column.name, column.types, colValue)

        if tree.header.rowSize > 0 and tree.header.rowCount > 0:
            for i in range(tree.header.rowCount):
                runtimeRows.append(OrderedDict())
                for column in runtimeColumns.values():
                    if column.types.column == "variable":
                        field = UtfField(column.types.value, tree.header).parse_stream(stream)
                        rowValue = make_runtime_value(column.name, column.types.value, field)

                        # these are big-endian :(
                        if column.name in ["ControlWorkArea1", "ControlWorkArea2"]:
                            bigEndianValue = util.i16swap(rowValue)
                            # print(f"{column.name}: {rowValue} -> {bigEndianValue}")
                            rowValue = bigEndianValue

                        runtimeRows[i][column.name] = UtfRowCell(column, rowValue)

        name = Pointer(tree.header.stringsPointer, CString(encoding="utf8")).parse_stream(stream)
        return cls(name, runtimeColumns, runtimeRows, tree)

    @classmethod
    def parse_file(cls, filename):
        with open(filename, 'rb') as f:
            return cls.parse_stream(f)

    def build(self):
        stream = io.BytesIO()
        self.build_stream(stream)
        return stream

    def build_stream(self, stream):
        stringsIo = io.BytesIO()
        stringToPointer = OrderedDict()
        variableColumns = tuple([column for column in self.columns.values() if column.types.column == "variable"])
        blobValues = []  # (runtimeBlob, treeBlob)

        def get_string_pointer(string: str):
            try:
                return stringToPointer[string]
            except KeyError:
                pointer = stringsIo.tell()
                CString(encoding="utf8").build_stream(string, stringsIo)
                return pointer

        def make_tree_value(type, value, blobPointer=0, blobLength=0):
            if type == "string":
                if "string" in value:
                    value = value.string
                if not value:
                    value = ""
                return {'stringPointer': get_string_pointer(value)}
            elif type == "blob":
                return {'blobPointer': blobPointer, 'blobLength': blobLength}
            else:
                return value

        def build_utf_field(valueType, obj):
            UtfField(valueType, self.tree.header).build_stream(obj, stream)

        def build_pointer_laden_area():
            file = Utf_File.build_stream(self.tree, stream)

            if variableColumns:
                self.tree.rowsPointer = stream.tell()
                for i in range(len(self.rows)):
                    for column in variableColumns:
                        build_utf_field(column.types.value, self.tree.rows[i][column.name])

        # Propagate column deletion
        for i, name in [(i, column.name) for (i, column) in enumerate(self.tree.columns)]:
            if name not in self.columns:
                self.tree.columns.pop(i)

        treeColumnNames = [column.name for column in self.tree.columns]
        # Propagate column addition
        for name, column in self.columns.items():
            if name not in treeColumnNames:
                newColumn = Container()
                newColumn["name"] = name
                newColumn["types"] = column.types
                self.tree.columns.append(newColumn)

        # This mapping will be valid from now on, so cache it
        nameToTreeColumnMapping = {
            name: [treeCol for treeCol in self.tree.columns if treeCol.name == name][0]
            for name in self.columns
        }

        # First-pass update of data in tree
        get_string_pointer(self.name)
        for name, column in self.columns.items():
            treeColumn = nameToTreeColumnMapping[name]
            treeColumn.namePointer = get_string_pointer(name)
            treeColumn.types = column.types
            if column.types.column == "constant":
                treeColumn.constant = make_tree_value(column.types.value, column.constant)
                if column.types.value == "blob":
                    blobValues.append((column.constant, treeColumn.constant))

        self.tree.rows = ListContainer()  # Wipe rows in tree
        if variableColumns:
            for i, row in enumerate(self.rows):
                treeRow = Container()
                for column in variableColumns:
                    treeRow[column.name] = make_tree_value(column.types.value, row[column.name].value)
                    if column.types.value == "blob":
                        blobValues.append((row[column.name].value, treeRow[column.name]))
                self.tree.rows.append(treeRow)

        # Write out first pass
        start = stream.tell()
        self.tree.rowsPointer = 8  # Dummy
        self.tree.stringsPointer = 8  # Dummy
        self.tree.blobsPointer = 8  # Dummy
        self.tree.endPointer = 8  # Dummy
        build_pointer_laden_area()

        # Write out strings and blobs
        self.tree.stringsPointer = stream.tell()
        GreedyBytes.build_stream(stringsIo.getvalue(), stream)
        firstLoop = True
        blobsPointer = stream.tell()
        for (runtimeBlob, treeBlob) in blobValues:
            if not runtimeBlob:
                treeBlob["blobLength"] = 0
                treeBlob["blobPointer"] = 0
                continue
            treeBlob["blobLength"] = runtimeBlob.length  # + runtimeBlob.postPadding
            absolutePointer = runtimeBlob.build_stream(stream)
            if firstLoop:
                blobsPointer = absolutePointer
                firstLoop = False
            treeBlob["blobPointer"] = absolutePointer - blobsPointer

        self.tree.blobsPointer = blobsPointer
        # Always pad file to multiple of 4 bytes, except the top level which is padded to 32 with a minimum of 1 byte
        size = stream.tell() - start
        if self.name == "Header":
            # Pad top-level acb to 32 byte boundary with a minimum of 1 byte
            postPadding = 32 - (stream.tell() % 32)
            Bytes(postPadding).build_stream(b"\x00" * postPadding, stream)
        else:
            if size % 4:
                postPadding = 4 - (size % 4)
                Bytes(postPadding).build_stream(b"\x00" * postPadding, stream)
        self.tree.endPointer = stream.tell()

        # Write out second pass to insert blob pointers
        stream.seek(start)
        build_pointer_laden_area()
        stream.seek(self.tree.endPointer)

    def get(self, row: int, columnName: str):
        column = self.columns[columnName]
        if column.types.column == "constant":
            return column.constant
        else:
            return self.rows[row][columnName].value

    def set(self, row: int, columnName: str, value, constant=False):
        column = self.columns[columnName]
        if column.types.column == "constant" and not constant:
            raise ValueError(
                f"set() used on constant field '{columnName}' but argument 'constant' is {constant}. Set 'constant' to True to set as constant.")
        elif column.types.column == "variable" and constant:
            raise ValueError(
                f"set() used on non-constant field '{columnName}' but argument 'constant' is {constant}. Set 'constant' to False to set as variable.")

        if constant:
            column.constant = value
        else:
            self.rows[row][columnName].value = value

    def add_row(self, rowData: OrderedDict):
        for name in self.columns:
            if name not in rowData:
                raise ValueError(f"Variable column '{name}' missing from row data.", rowData)

        self.rows.append(rowData)

    def delete_row(self, row: int):
        self.rows.pop(row)
