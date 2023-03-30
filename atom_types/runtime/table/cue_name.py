from collections import OrderedDict

from atom_types.runtime import util
from atom_types.file.utf_file import ValueTypeNibble
from atom_types.runtime.table.table_base import TableBase
from atom_types.runtime.utf import UtfRowCell


class CueNameTable(TableBase):
    def __search_name(self, cue_name: str) -> int:
        try:
            return next(filter(lambda x: x[1]["CueName"].value == cue_name, enumerate(self.utf.rows)))[0]
        except StopIteration:
            raise KeyError(f"Cue name '{cue_name}' does not exist in Cue Name list.")

    def __search_cue_index(self, cue_index: int) -> int:
        try:
            cue_index_be = util.i16swap(cue_index)
            return next(filter(lambda x: x[1]["CueIndex"].value == cue_index_be, enumerate(self.utf.rows)))[0]
        except StopIteration:
            raise KeyError(f"Cue index '{cue_index}' does not exist in Cue Name list.")

    def update(self, search_cue_name: str, new_cue_index: int):
        """Updates the Cue index based on Cue name.

        :param: search_cue_name: Cue name to search for
        :param: new_cue_index: New index of the Cue in CueTable (NOT 'CueId')
        """
        index = self.__search_name(search_cue_name)
        # self.utf.rows[index]["CueName"].value = cue_name
        self.utf.rows[index]["CueIndex"].value = util.i16swap(new_cue_index)

    def update_by_cue_index(self, search_cue_index: int, new_cue_name: str):
        """Updates the Cue name based on Cue index.

        :param: search_cue_index: Index of the Cue in CueTable (NOT 'CueId') to search for
        :param: new_cue_name: New Cue name
        """
        index = self.__search_cue_index(search_cue_index)
        self.utf.rows[index]["CueName"].value = new_cue_name

    def add(self, cue_index: int, cue_name: str):
        """Adds a new row to the Cue Name list.

        :param: cue_index: Index of the Cue in CueTable (NOT 'CueId')
        :param: cue_name: Unique name to associate with the Cue
        """
        if cue_name in [row["CueName"].value for row in self.utf.rows]:
            raise KeyError(f"Cue name '{cue_name}' already present in Cue Name list.")
        row = OrderedDict([
            UtfRowCell.build_tuple("CueName", cue_name, ValueTypeNibble.string),
            UtfRowCell.build_tuple("CueIndex", util.i16swap(cue_index), ValueTypeNibble.int16),
        ])
        self.utf.rows.append(row)
        return len(self.utf.rows) - 1

    def pop(self, cue_name: str):
        """Removes a Cue Name from the list.

        :param: cue_name: Cue Name to remove
        """
        index = self.__search_name(cue_name)
        self.utf.rows.pop(index)

    def get_by_name(self, cue_name: str):
        index = self.__search_name(cue_name)
        return self.utf.rows[index]

    def get_by_cue_index(self, cue_index: int):
        index = self.__search_cue_index(cue_index)
        return self.utf.rows[index]
