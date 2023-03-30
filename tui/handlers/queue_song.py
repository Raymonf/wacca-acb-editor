import os

from tui.state import State
from tui.state_type import StateType
from tui.ui import Ui, UiHandler


class QueueSong(UiHandler):
    def __init__(self, ui: Ui):
        super().__init__(ui, "queue_song")

    def handle(self, state: State):
        print("Enter '\\q' (without single-quotes) to cancel this operation.")
        path = input("Enter the path to an audio file: ").strip()
        if path.lower() == '\\q':
            return self.ui.set_state(StateType.MAIN_MENU)

        if not os.path.exists(path):
            print(f"The file '{path}' does not exist!")
            return

        try:
            result = state.audio_preprocessor.autoprocess(path)
            state.file_queue.append(result)
            print("Added song.")
            return self.ui.set_state(StateType.MAIN_MENU)
        except Exception as e:
            self.log.error("Could not process this file.", e)

