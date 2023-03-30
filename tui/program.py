import logging

from tui.handlers.choose_acb import ChooseAcb
from tui.handlers.delete_from_queue import DeleteFromQueue
from tui.handlers.initialize import Initialize
from tui.handlers.main_menu import MainMenu
from tui.handlers.queue_song import QueueSong
from tui.handlers.quit import QuitHandler
from tui.handlers.write_acb import WriteAcb
from tui.state_type import StateType
from tui.ui import Ui

HANDLERS = {
    StateType.INITIAL: Initialize,
    StateType.MAIN_MENU: MainMenu,
    StateType.CHOOSE_ACB: ChooseAcb,
    StateType.QUEUE_SONG: QueueSong,
    StateType.WRITE_ACB: WriteAcb,
    StateType.DELETE_FROM_QUEUE: DeleteFromQueue,
    StateType.QUIT: QuitHandler
}


class TuiProgram:
    def __init__(self, is_debug: bool = False):
        logging.basicConfig(level=logging.DEBUG if is_debug else logging.INFO)
        self.ui = Ui(HANDLERS)

    def run(self):
        self.ui.run()
