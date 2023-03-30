from enum import Enum


class StateType(Enum):
    QUIT = -1
    INITIAL = 0
    MAIN_MENU = 1
    CHOOSE_ACB = 2
    QUEUE_SONG = 3
    WRITE_ACB = 4
    DELETE_FROM_QUEUE = 5
