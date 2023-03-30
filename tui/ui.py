import logging
from typing import List, Tuple, Type

from tui.state import State
from tui.state_type import StateType


class UiHandler:
    def __init__(self, ui, logger_name: str = 'tui'):
        self.ui = ui
        self.log = logging.getLogger(logger_name)

    def handle(self, state: State):
        raise NotImplementedError()


class Ui:
    state: State = State()
    funcs: dict[StateType, UiHandler] = {}

    def __init__(self, handlers: dict[StateType, Type]):
        self.log = logging.getLogger("tui")
        for state_type in handlers:
            self.funcs[state_type] = handlers[state_type](self)

    def get_handler(self):
        return self.funcs[self.state.current]

    def run(self):
        while self.state.current != StateType.QUIT:
            if self.state.current in self.funcs:
                self.funcs[self.state.current].handle(self.state)
                print()  # new line
            else:
                self.log.error(f"Encountered unknown state '{self.state.current}', exiting.")
                self.set_state(StateType.QUIT)

        if StateType.QUIT in self.funcs:
            # we have a quit handler for cleanup
            self.funcs[StateType.QUIT].handle(self.state)

    def prompt_yes_no(self, prompt: str = "y/n? "):
        while True:
            response = input(prompt).strip().lower()
            match response:
                case "y":
                    return True
                case "n":
                    return False
                case _:
                    print("Invalid choice.")

    def set_state(self, new_state: StateType):
        self.state.current = new_state
