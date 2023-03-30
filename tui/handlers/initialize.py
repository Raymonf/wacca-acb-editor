from audio.error import MissingDependencyError
from audio.preprocessor import AudioPreprocessor
from tui.state import State
from tui.state_type import StateType
from tui.ui import Ui, UiHandler


class Initialize(UiHandler):
    def __init__(self, ui: Ui):
        super().__init__(ui, "initialize")

    def handle(self, state: State):
        self.log.debug("Initialize")
        try:
            state.audio_preprocessor = AudioPreprocessor()
            self.ui.set_state(StateType.MAIN_MENU)
        except MissingDependencyError as e:
            print("Missing dependencies were detected during initialization. "
                  "Please review the following error message(s):")
            print(e)
            self.ui.set_state(StateType.QUIT)
