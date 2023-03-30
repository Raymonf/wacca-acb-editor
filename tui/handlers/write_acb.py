from tabulate import tabulate

from atom_types.runtime.acb import Acb
from atom_types.runtime.table.stream_awb import StreamAwbTable
from tui.handlers.quit import cleanup_queue
from tui.state import State
from tui.state_type import StateType
from tui.ui import Ui, UiHandler


def print_awb_list(stream_awbs: StreamAwbTable):
    data = []
    for awb, index in stream_awbs.awbListIndexByName.items():
        data.append([index, awb])
    print(tabulate(data, headers=["Index", "AWB Name"]))


class WriteAcb(UiHandler):
    def __init__(self, ui: Ui):
        super().__init__(ui, "write_acb")

    def handle(self, state: State):
        self.log.debug("WIP: write ACB")

        if len(self.ui.state.file_queue) < 1:
            print("No songs have been queued in the file queue.")
            return self.ui.set_state(StateType.MAIN_MENU)

        if self.ui.state.acb_path is None:
            print("No ACB file has been selected.")
            return self.ui.set_state(StateType.MAIN_MENU)

        if not self.ui.prompt_yes_no(f"Confirm write to '{state.acb_path}' (y/n)? "):
            return self.ui.set_state(StateType.MAIN_MENU)

        if self.ui.state.acb_in is None:
            self.open()

        acb = self.ui.state.acb_in
        stream_awbs = acb.tables.streamAwbs

        print("Valid streaming AWBs:")
        print_awb_list(stream_awbs)

        valid_name = False
        target_name = None
        while not valid_name:
            awb_name = input("Enter target streaming AWB filename or index: ").strip()
            if awb_name.lower() == '\\q':
                return self.ui.set_state(StateType.MAIN_MENU)
            result = self.get_awb_name_from_input(awb_name)
            if result is not None:
                target_name = result
                valid_name = True

        results = self.write(target_name)

        self.log.info("Appended cue names:")
        for song, cue_name in results.items():
            self.log.info(f"* {cue_name}: {song}")

        if self.ui.prompt_yes_no(f"Clean up file queue (y/n)? "):
            cleanup_queue(self.log, state)

        self.ui.set_state(StateType.MAIN_MENU)

    def get_awb_name_from_input(self, awb_name: str, print_messages: bool = True) -> str | None:
        stream_awbs = self.ui.state.acb_in.tables.streamAwbs

        # check if index
        if awb_name.isdigit():
            index = int(awb_name)
            if 0 <= index < len(stream_awbs.awbList):
                target_name = stream_awbs.awbList[index].name
                self.log.debug(f"Got index {index} and found item '{target_name}' in AWB list.")
                return target_name
            if print_messages:
                print(f"Could not find a streaming AWB file with the index {index}.")
            return None

        # check if name
        lowercase_names = list(k.lower() for k in stream_awbs.awbListIndexByName)
        try:
            index = lowercase_names.index(awb_name.lower())
            target_name = stream_awbs.awbList[index].name
            self.log.debug(f"Found item '{target_name}' (index {index}) in AWB list")
            return target_name
        except ValueError:
            if print_messages:
                print(f"Could not find a streaming AWB file named '{awb_name}'.")
        return None

    def open(self):
        if self.ui.state.acb_in is not None:
            raise FileExistsError("ACB is already loaded")
        self.log.debug(f"Opening ACB file '{self.ui.state.acb_path}'")
        self.ui.state.acb_in = Acb.parse_stream(self.ui.state.awb_path, open(self.ui.state.acb_path, "rb"))

    def next_cue_name(self):
        def gen_name(i: int):
            return f"{prefix}_{str(i).zfill(3)}"

        # TODO: configurable prefix
        prefix = "MER_BGM_S04"

        acb = self.ui.state.acb_in
        current_names = set(x['CueName'].value for x in acb.tables.cueNames.utf.rows)
        index = 0
        while gen_name(index) in current_names:
            index += 1
        return gen_name(index)

    def write(self, target_awb_name: str, output_acb_name: str = "MER_BGM.acb.injected") -> dict[str, str]:
        """Does the write.

        :param: target_awb_name: EXACT AWB name"""
        appended_files = {}

        acb = self.ui.state.acb_in
        stream_awbs = acb.tables.streamAwbs

        # get the index out of the name map
        index = stream_awbs.awbListIndexByName[target_awb_name]
        acb.tables.streamAwbs.mark_awb_for_rehash(index)

        # append all the songs to the awb
        awb_info = stream_awbs.awbList[index]
        for song in self.ui.state.file_queue:
            self.log.debug(f"Appending '{song.path}' to {target_awb_name}")
            file_id = awb_info.awb.appendFile(open(song.path, "rb"))
            song.new_index = file_id
            self.log.debug(f"New ID for '{song.path}' is {file_id}")

        # append all the songs to the acb
        for song in self.ui.state.file_queue:
            cue_name = self.next_cue_name()
            self.log.debug(f"Got cue name '{cue_name}' for file '{song.path}'")
            appended_files[song.orig_filename] = cue_name

            acb.add_song_to_awb(
                cue_name=cue_name,
                awb_id=index,
                awb_file_id=song.new_index,
                num_samples=song.sample_count,
                length_ms=song.length_ms
            )

        # write out new awb
        out_awb_name = f"{target_awb_name}.injected"
        awb_info.awb.build_file(out_awb_name)

        # update streaming AWB headers
        remap = {
            f"{target_awb_name}.awb": out_awb_name # we want to read .injected, not the original
        }
        acb.update_streaming_awb_headers(remap=remap)

        # write out new acb
        with open(output_acb_name, "wb") as out:
            acb.build_stream(out)

        return appended_files
