import logging
import sys

from audio import preprocessor
from tui.handlers.write_acb import WriteAcb
from tui.program import TuiProgram
from tui.state_type import StateType
from tui.ui import UiHandler


def cli_append_song_list(args):
    log = logging.getLogger("cli_append_song_list")
    acb_path = args.acb_path

    # initialize the ui backend
    program = TuiProgram(args.debug is True)
    ui = program.ui
    state = ui.state

    # preprocess the songs
    pp = preprocessor.AudioPreprocessor()

    try:
        with open(args.list_path, 'r') as f:
            for song_path in f:
                song_path = song_path.strip()
                if not song_path:
                    continue
                log.info(f"Preprocessing song {song_path}")
                song = pp.autoprocess(song_path)
                state.file_queue.append(song)
    except FileNotFoundError:
        sys.exit(f"Couldn't find list file at '{args.list_path}'!")

    ui.set_state(StateType.WRITE_ACB)
    write_acb: WriteAcb = ui.get_handler()
    state.awb_path = args.awb_dir
    state.acb_path = acb_path
    log.info("Opening and parsing ACB and AWB files")
    write_acb.open()

    target_name = write_acb.get_awb_name_from_input(args.awb, print_messages=args.debug is True)
    if target_name is None:
        sys.exit(f"Couldn't find an AWB with a name or index of '{args.awb}'!")

    log.info("Writing injected ACB and AWB")
    results = write_acb.write(target_name)
    for song, cue_name in results.items():
        log.info(f"* {cue_name}: {song}")

    # cleanup
    ui.set_state(StateType.QUIT)
    ui.get_handler().handle(state)

    pass


def cli_append_song(args):
    log = logging.getLogger("cli_append_song")
    acb_path = args.acb_path

    # initialize the ui backend
    program = TuiProgram(args.debug is True)
    ui = program.ui
    state = ui.state

    # preprocess the song
    log.info("Preprocessing song")
    pp = preprocessor.AudioPreprocessor()
    song = pp.autoprocess(args.song_path)
    state.file_queue.append(song)

    ui.set_state(StateType.WRITE_ACB)
    write_acb: WriteAcb = ui.get_handler()
    state.awb_path = args.awb_dir
    state.acb_path = acb_path
    log.info("Opening and parsing ACB and AWB files")
    write_acb.open()

    target_name = write_acb.get_awb_name_from_input(args.awb, print_messages=args.debug is True)
    if target_name is None:
        sys.exit(f"Couldn't find an AWB with a name or index of '{args.awb}'!")

    log.info("Writing injected ACB and AWB")
    results = write_acb.write(target_name)
    for song, cue_name in results.items():
        log.info(f"* {cue_name}: {song}")

    # cleanup
    ui.set_state(StateType.QUIT)
    ui.get_handler().handle(state)

    pass
