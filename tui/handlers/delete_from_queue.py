from tabulate import tabulate

from tui.handlers.quit import cleanup_one
from tui.state import State
from tui.state_type import StateType
from tui.ui import Ui, UiHandler


class DeleteFromQueue(UiHandler):
    def __init__(self, ui: Ui):
        super().__init__(ui, "delete_from_queue")

    def handle(self, state: State):
        try:
            data = []
            for num, file in enumerate(self.ui.state.file_queue):
                data.append([num+1, file.orig_filename])

            print(tabulate(data, headers=["#", "Name"]))

            in_data = input("Which # to delete (or '\q' to cancel)? ").strip()
            if in_data.lower() == "\\q":
                return self.ui.set_state(StateType.MAIN_MENU)

            index = int(in_data) - 1
            if 0 < index < len(state.file_queue):
                file = state.file_queue.pop(index)
                cleanup_one(self.log, file)
                return self.ui.set_state(StateType.MAIN_MENU)
            else:
                self.log.error("Number was out of range.")
        except ValueError as e:
            self.log.error("Invalid value given.")
