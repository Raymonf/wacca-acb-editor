from tui.state import State
from tui.state_type import StateType
from tui.ui import Ui, UiHandler

from tabulate import tabulate


class MainMenu(UiHandler):
    def __init__(self, ui: Ui):
        super().__init__(ui, "main_menu")

    def handle(self, state: State):
        print("Main Menu")

        if state.acb_path is None:
            print("No ACB file is selected.")
        else:
            print(f"ACB file path: {state.acb_path}")
        print("----")
        print("* p: print current file queue")
        print("* a: add a song to the current file queue")
        print("* d: delete a song from the current file queue")
        print("----")
        print("* c: choose active acb file")
        print("* w: open and write to active acb file")
        print("* q or quit")

        response = input("Input a mode: ").strip().lower().split(' ')
        if len(response) < 1:
            return

        match response[0]:
            case "p":
                return self.print_file_queue()
            case "a":
                return self.ui.set_state(StateType.QUEUE_SONG)
            case "d":
                return self.ui.set_state(StateType.DELETE_FROM_QUEUE)

            case "c":
                return self.ui.set_state(StateType.CHOOSE_ACB)
            case "w":
                return self.ui.set_state(StateType.WRITE_ACB)
            case "q":
                return self.ui.set_state(StateType.QUIT)

    def print_file_queue(self):
        data = []
        for num, file in enumerate(self.ui.state.file_queue):
            data.append([num+1, "YES" if file.delete else "no", file.orig_filename, file.sample_count, file.length_ms])

        print(tabulate(data, headers=["#", "Converted", "Original Name", "Sample Count", "Length (ms)"]))
