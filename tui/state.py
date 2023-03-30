from typing import List

from atom_types.runtime.acb import Acb
from audio.preprocess_result import PreprocessResult
from audio.preprocessor import AudioPreprocessor
from tui.state_type import StateType


class State:
    current: StateType = StateType.INITIAL
    file_queue: List[PreprocessResult] = []

    awb_path: str = None
    acb_path: str = None
    acb_in: Acb = None

    audio_preprocessor: AudioPreprocessor
