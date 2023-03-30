from collections import OrderedDict

from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfRowCell


class StreamAwbAfs2Header(TableBase):
    def update(self, awbPortId: int, newHeader):
        size = len(self.utf.rows)
        if size > awbPortId:
            self.utf.rows[awbPortId]["Header"].value = newHeader
        else:
            """Untested after refactor."""
            print(f"-> [Untested] Adding new AWB ID {awbPortId}")
            if size != awbPortId:
                raise KeyError("Invalid AWB port ID. You need to call sequentially starting from 0.")
            row = OrderedDict([
                UtfRowCell.build_tuple("Header", newHeader,
                                       ValueTypeNibble.blob),
            ])
            self.utf.rows.append(row)
