import os
import pathlib

from atom_types.runtime.acb import Acb
from tui.state import State
from tui.state_type import StateType
from tui.ui import Ui, UiHandler


class ChooseAcb(UiHandler):
    def __init__(self, ui: Ui):
        super().__init__(ui, "choose_acb")

    def handle(self, state: State):
        self.log.debug("Choose ACB")

        if self.ui.state.acb_path is not None:
            print(f"There is already an ACB file loaded: {self.ui.state.acb_path}")
            if not self.ui.prompt_yes_no("Do you want to replace the selected file (y/n)? "):
                print("Cancelling operation.")
                return self.ui.set_state(StateType.MAIN_MENU)

        # TODO: open file picker if possible

        path = input("Enter the path to an ACB file: ")
        if not os.path.exists(path):
            print(f"The file '{path}' does not exist!")
            return

        # TODO: manual awb location?
        self.set_acb(path, str(pathlib.Path(path).parent.absolute()))

        self.ui.set_state(StateType.MAIN_MENU)

    def set_acb(self, acb_path: str, awb_dir: str):
        # TODO: clean up old state if needed
        self.ui.state.awb_path = os.path.abspath(awb_dir)
        self.ui.state.acb_path = os.path.abspath(acb_path)
        self.ui.state.acb_in = None  # we'll load it later
