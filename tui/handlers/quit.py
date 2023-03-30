import os
from logging import Logger

from audio.preprocess_result import PreprocessResult
from tui.state import State
from tui.ui import Ui, UiHandler


def cleanup_queue(log: Logger, state: State):
    queue = state.file_queue
    while queue:
        file = queue.pop()
        cleanup_one(log, file)


def cleanup_one(log: Logger, file: PreprocessResult):
    if file.delete and os.path.exists(file.path):
        try:
            log.debug(f"Unlinking '{file.path}'")
            os.unlink(file.path)
        except OSError as e:
            log.warning(f"Could not delete {file.path} because '{e}'", e)


class QuitHandler(UiHandler):
    def __init__(self, ui: Ui):
        super().__init__(ui, "quitter")

    def handle(self, state: State):
        # Clean up temporary files

        self.log.debug(f"Quitter reached: removing temporary files marked for deletion")
        cleanup_queue(self.log, state)
